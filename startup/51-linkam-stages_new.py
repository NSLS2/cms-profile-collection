# EPICS interface developed by Jakub
# Bsui code adopted from BMM/Bruce Ravel and modified by Ruipeng Li
# 2025-08-19: Modified by Siyu Wu

import asyncio
import enum
import pandas as pd
import time
import json
from pathlib import Path
from datetime import datetime
from shutil import copyfile
from ophyd import PositionerBase
from ophyd.status import MoveStatus

class LinkamThermal(Device):
    """
    Device interface and experiment orchestration for the Linkam thermal stage.
    Supports step programming, temperature/rate control, async experiment runs,
    and automated data archiving.
    """

    # Set-and-read signals
    cmd = Cpt(EpicsSignal, "STARTHEAT")
    temperature_setpoint = Cpt(EpicsSignal, "SETPOINT:SET")
    temperature_rate_setpoint = Cpt(EpicsSignal, "RAMPRATE:SET")

    # Read-Only signals
    status_power = Cpt(EpicsSignalRO, "STARTHEAT")
    status_code = Cpt(EpicsSignalRO, "STATUS")
    # status_code = Cpt(EpicsSignal, 'STATUS')
    # done = Cpt(AtSetpoint, parent_attr = 'status_code')
    temperature_current = Cpt(EpicsSignalRO, "TEMP")
    temperature_rate_current = Cpt(EpicsSignalRO, "RAMPRATE")
    power = Cpt(EpicsSignalRO, "POWER")

    # Not commonly used signals
    init = Cpt(EpicsSignal, "INIT")
    model_array = Cpt(EpicsSignal, "MODEL")
    serial_array = Cpt(EpicsSignal, "SERIAL")
    stage_model_array = Cpt(EpicsSignal, "STAGE:MODEL")
    stage_serial_array = Cpt(EpicsSignal, "STAGE:SERIAL")
    firm_ver = Cpt(EpicsSignal, "FIRM:VER")
    hard_ver = Cpt(EpicsSignal, "HARD:VER")
    ctrllr_err = Cpt(EpicsSignal, "CTRLLR:ERR")
    config = Cpt(EpicsSignal, "CONFIG")
    stage_config = Cpt(EpicsSignal, "STAGE:CONFIG")
    disable = Cpt(EpicsSignal, "DISABLE")
    dsc = Cpt(EpicsSignal, "DSC")
    # RR_set = Cpt(EpicsSignal, 'RAMPRATE:SET')
    # RR = Cpt(EpicsSignal, 'RAMPRATE')
    ramptime = Cpt(EpicsSignal, "RAMPTIME")
    # startheat = Cpt(EpicsSignal, 'STARTHEAT')
    holdtime_set = Cpt(EpicsSignal, "HOLDTIME:SET")
    holdtime = Cpt(EpicsSignal, "HOLDTIME")
    lnp_speed = Cpt(EpicsSignal, "LNP_SPEED")
    lnp_mode_set = Cpt(EpicsSignal, "LNP_MODE:SET")
    lnp_speed_set = Cpt(EpicsSignal, "LNP_SPEED:SET")

    # Stage origin position logging functions
    # Add by Siyu Wu 2025-08-19

    # Default (required) step columns and PVs for thermal mode. Units are in the column
    # names, e.g. 'temperature(C)'.
    step_columns = ['stepNo', 'temperature(C)', 'ramp_rate(C/min)', 'duration(s)']
    pv_list = [
        'XF:11BM-ES:{LINKAM}:TEMP',
        'XF:11BM-ES:{LINKAM}:RAMPRATE',
        'XF:11BM-ES:{LINKAM}:SETPOINT',
        'XF:11BM-ES:{LINKAM}:STATUS',
        'XF:11BM-ES:{LINKAM}:POWER'
    ]

    def __init__(self, prefix, name=None, step_columns=None, pv_list=None, **kwargs):
        """
        Initialize LinkamThermal device, step configuration, and position logging.
        """
        super().__init__(prefix, name=name, **kwargs)
        self.folder = Path(bluesky_path('cfg'))
        self.config_file = self.folder / 'linkam_stage_pos.cfg'
        self._csv_path = self.folder / f'{name}_step.csv'
        self.step_columns = step_columns or self.step_columns
        self.pv_list = pv_list or self.pv_list
        self.step_config = pd.DataFrame(columns=self.step_columns)
        self._sync()
        self.positions = self._load_config()
        self.loadOrigin()

    def _sync(self):
        """
        Sync current motor positions to internal state.
        """
        self.xo = smx.position
        self.yo = smy.position

    def _save_config(self):
        """Save current positions to JSON config file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.positions, f, indent=2)

    def _load_config(self):
        """Load positions from JSON config file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def setOrigin(self):
        """Save current origin position (xo, yo) with timestamp to config file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.positions = json.load(f)
        else:
            self.positions = {}

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {'xo': self.xo, 'yo': self.yo, 'timestamp': timestamp}
        self.positions.setdefault(self.name, []).append(entry)
        self._save_config()
        print(f"Saved current position for '{self.name}' at {timestamp}.")

    def loadOrigin(self):
        """Load the last saved origin position (xo, yo) from the config file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.positions = json.load(f)
            entries = self.positions.get(self.name)
            if entries:
                latest = entries[-1]
                self.xo = latest['xo']
                self.yo = latest['yo']
                print(f"Loaded last position for '{self.name}' from {latest.get('timestamp', 'unknown')}")
            else:
                print(f"No saved position found for '{self.name}'.")
        else:
            print(f"No config file found for '{self.name}'.")

    def on(self):
        """Turn the stage heater on."""
        while self.cmd.get() != 1:
            time.sleep(0.2)
            self.cmd.put(1)
        return self.cmd.get()

    def _on(self):
        """
        Internal method to turn the stage on.
        """
        yield from bps.mv(self.cmd, 1)

    def off(self):
        """Turn the stage heater off."""
        while self.cmd.get() != 0:
            time.sleep(0.2)
            self.cmd.put(0)
        return self.cmd.get()

    def _off(self):
        """
        Internal method to turn the stage off.
        """
        yield from bps.mv(self.cmd, 0)

    def setTemperature(self, temperature):
        """
        Sets the temperature setpoint for the stage.
        """
        while self.temperature_setpoint.get() != temperature:
            time.sleep(0.2)
            self.temperature_setpoint.put(temperature)
        return self.temperature_setpoint.get()

    def setTemperatureRate(self, temperature_rate: float) -> float:
        """Set the temperature ramp rate for the stage."""
        while self.temperature_rate_setpoint.get() != temperature_rate:
            time.sleep(0.2)
            self.temperature_rate_setpoint.put(temperature_rate)
        return self.temperature_rate_setpoint.get()

    def temperature(self) -> float:
        """Get the current temperature of the stage."""
        return self.temperature_current.get()

    def temperatureRate(self) -> float:
        """Get the current temperature ramp rate of the stage."""
        return self.temperature_rate_current.get()

    @property
    def serial(self):
        return self.arr2word(self.serial_array.get())

    @property
    def model(self):
        return self.arr2word(self.model_array.get())

    @property
    def stage_model(self):
        return self.arr2word(self.stage_model_array.get())

    @property
    def stage_serial(self):
        return self.arr2word(self.stage_serial_array.get())

    @property
    def firmware_version(self):
        return self.arr2word(self.firm_ver.get())

    @property
    def hardware_version(self):
        return self.arr2word(self.hard_ver.get())

    def status(self):
        """
        Print a summary of the current stage status.
        Shows temperature, setpoint, heater, pump, and error states.
        """
        text = f"\nCurrent temperature = {self.temperature():.1f}, setpoint = {self.temperature_setpoint.get():.1f}\n\n"
        code = int(self.status_code.get())
        text += f"Error        : {'yes' if code & 1 else 'no'}\n"
        text += f"At setpoint  : {'yes' if code & 2 else 'no'}\n"
        text += f"Heater       : {'on' if code & 4 else 'off'}\n"
        text += f"Pump         : {'on' if code & 8 else 'off'}\n"
        text += f"Pump Auto    : {'yes' if code & 16 else 'no'}\n"
        print(text)

    # Linkam Stage Step Configuration Read/Load functions
    # Added by Siyu Wu 2025-08-19

    @property
    def csv_path(self) -> Path:
        """Current step-configuration CSV path."""
        return self._csv_path

    @csv_path.setter
    def csv_path(self, path) -> None:
        path = Path(path)
        if path.suffix != '.csv':
            path = path.with_suffix('.csv')
        if not path.is_absolute():
            try:
                path = Path(RE.md['userpy_alias_directory']) / path
            except KeyError as error:
                raise RuntimeError("RE.md['userpy_alias_directory'] must be set before "
                                   "loading a user Linkam step profile.") from error
        self._csv_path = path

    def load_step_config(self, profile=None) -> pd.DataFrame:
        """
        Load a user step-configuration profile or explicit CSV path.
        Uses self.step_columns for required columns; lines starting with '#' are
        treated as comments and skipped. Missing user profiles are initialized
        from a same-named template in the shared cfg directory. The selected
        path becomes csv_path, so subsequent editing saves to that user file.
        Returns: pandas DataFrame
        """
        if profile is not None:
            self.csv_path = profile
        elif self.csv_path.parent == self.folder:
            self.csv_path = self.csv_path.name

        if not self.csv_path.exists():
            template_path = self.folder / self.csv_path.name
            if not template_path.is_file():
                raise FileNotFoundError(f"No user profile at {self.csv_path} and no shared "
                                        f"template at {template_path}.")
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            copyfile(template_path, self.csv_path)
            print(f"[LINKAM] Created user step profile from {template_path.name}: {self.csv_path}")

        df = pd.read_csv(self.csv_path, comment='#', skipinitialspace=True)
        required_cols = set(self.step_columns)
        if not required_cols.issubset(df.columns):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        self.step_config = df
        path_text = str(self.csv_path)
        print(f"[LINKAM] Loaded {len(df)} step(s) from: "
              f"\033]8;;{self.csv_path.as_uri()}\033\\{path_text}\033]8;;\033\\")
        self.check_step_timing()
        return df

    def check_step_timing(self, start_temperature: float = None, verbosity: int = 1) -> list:
        """
        Warn (does not raise) about any loaded step whose duration(s) is too
        short to complete both the temperature ramp and (for tensile) the
        motor move - run_single_step() runs them concurrently and just stops
        at duration(s) regardless, so a step that's too short gets cut off
        before reaching its target temperature/position.

        Each step's ramp is chained from the previous step's target
        temperature, not assumed to start from room temperature every time -
        for step 0, the stage's current live temperature is used unless
        start_temperature overrides it (the stage may already be hot/cold
        from a previous run).

        Returns the list of stepNo with insufficient duration.
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")

        has_motion = {'position(um)', 'velocity(um/s)'}.issubset(self.step_config.columns)
        prev_temp = start_temperature if start_temperature is not None else self.temperature()

        short_steps = []
        for _, step in self.step_config.iterrows():
            stepNo = int(step['stepNo'])
            target_temp = float(step['temperature(C)'])
            ramp_rate = float(step['ramp_rate(C/min)'])
            duration = float(step['duration(s)'])

            ramp_time = abs(target_temp - prev_temp) / (ramp_rate / 60.0) if ramp_rate else 0.0

            move_time = 0.0
            if has_motion:
                velocity = float(step['velocity(um/s)'])
                move_time = abs(float(step['position(um)'])) / velocity if velocity else 0.0

            # Temperature ramp and motion run concurrently in run_single_step(),
            # so the step needs at least as long as whichever takes longer.
            required = max(ramp_time, move_time)

            if required > duration:
                short_steps.append(stepNo)
                if verbosity >= 1:
                    slow_part = "temperature ramp" if ramp_time >= move_time else "motor move"
                    print(f"[LINKAM] step {stepNo}: needs ~{required:.1f}s ({slow_part}) but "
                          f"duration(s)={duration:.1f}s - will be cut short by ~{required - duration:.1f}s.")
            elif verbosity >= 2:
                print(f"[LINKAM] step {stepNo}: needs ~{required:.1f}s, duration(s)={duration:.1f}s "
                      f"({duration - required:.1f}s margin/hold).")

            prev_temp = target_temp  # next step's ramp starts from here, not room temperature

        return short_steps

    def save_step_config(self) -> None:
        """Save step configuration DataFrame to CSV."""
        self.step_config.to_csv(self.csv_path, index=False)

    def show_step_config(self) -> None:
        """Display the current step configuration."""
        if hasattr(self, 'step_config'):
            print(self.step_config)
        else:
            print("No step configuration loaded.")
    def add_step(self, *args, **kwargs) -> None:
        """
        Add a new step to the step configuration.
        You can use positional arguments (in order of self.step_columns, skipping 'stepNo')
        or keyword arguments (column=value).
        Example:
            add_step(25, 10, 15)  # temperature(C), ramp_rate(C/min), duration(s)
            # for tensile: temperature(C), ramp_rate(C/min), duration(s), position(um), velocity(um/s)
            add_step(25, 10, 15, -1000, 100)
        """
        if not hasattr(self, 'step_config'):
            self.step_config = pd.DataFrame(columns=self.step_columns)
        stepNo = len(self.step_config)
        new_step = {'stepNo': stepNo}
        # Fill from positional args
        cols = [col for col in self.step_columns if col != 'stepNo']
        for i, col in enumerate(cols):
            if i < len(args):
                new_step[col] = args[i]
            else:
                new_step[col] = kwargs.get(col, None)
        self.step_config = pd.concat([self.step_config, pd.DataFrame([new_step])], ignore_index=True)
        self.save_step_config()
        print(f"Added step {stepNo}: " + ", ".join(f"{k}={v}" for k, v in new_step.items() if k != 'stepNo'))

    def set_step(self, stepNo: int, *args, **kwargs) -> None:
        """
        Update a specific step in the step configuration.
        You can use positional arguments (in order of self.step_columns, skipping 'stepNo')
        or keyword arguments (column=value).
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo >= len(self.step_config):
            raise IndexError("Step number out of range.")
        current_data = {'stepNo': stepNo}
        cols = [col for col in self.step_columns if col != 'stepNo']
        for i, col in enumerate(cols):
            if i < len(args):
                current_data[col] = args[i]
            else:
                current_data[col] = kwargs.get(col, self.step_config.loc[stepNo, col])
        self.step_config.loc[stepNo] = current_data
        self.save_step_config()
        print(f"Updated step {stepNo}: " + ", ".join(f"{k}={v}" for k, v in current_data.items() if k != 'stepNo'))

    def delete_step(self, stepNo: int) -> None:
        """
        Delete a specific step from the step configuration.
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo >= len(self.step_config):
            raise IndexError("Step number out of range.")
        self.step_config = self.step_config[self.step_config['stepNo'] != stepNo]
        self.step_config.reset_index(drop=True, inplace=True)
        self.step_config['stepNo'] = range(len(self.step_config))
        self.save_step_config()
        print(f"Deleted step {stepNo}.")

    def insert_step(self, stepNo: int, *args, **kwargs) -> None:
        """
        Insert a new step at a specific position in the step configuration.
        You can use positional arguments (in order of self.step_columns, skipping 'stepNo')
        or keyword arguments (column=value).
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo > len(self.step_config):
            raise IndexError("Step number out of range.")
        new_step = {'stepNo': stepNo}
        cols = [col for col in self.step_columns if col != 'stepNo']
        for i, col in enumerate(cols):
            if i < len(args):
                new_step[col] = args[i]
            else:
                new_step[col] = kwargs.get(col, None)
        upper_half = self.step_config[self.step_config['stepNo'] >= stepNo].copy()
        upper_half['stepNo'] += 1
        self.step_config = pd.concat([
            self.step_config[self.step_config['stepNo'] < stepNo],
            pd.DataFrame([new_step]),
            upper_half
        ], ignore_index=True)
        self.save_step_config()
        print(f"Inserted step at position {stepNo}: " + ", ".join(f"{k}={v}" for k, v in new_step.items() if k != 'stepNo'))
    
    # --- Step Execution ---

    def run_step(self, stepNo: int = 0) -> None:
        """
        Run the thermal stage from a specific step (blocking).
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo >= len(self.step_config):
            raise IndexError("Step number out of range.")
        for i in range(stepNo, len(self.step_config)):
            self.run_single_step(i)
        self.off()

    def run_single_step(self, stepNo: int, stop_evt: threading.Event = None) -> None:
        """
        Run a single step (blocking), responsive to stop_evt.
        Prints step info before running.
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo >= len(self.step_config):
            raise IndexError("Step number out of range.")
        if stop_evt and stop_evt.is_set():
            return
        step = self.step_config.iloc[stepNo]
        print(f"[LINKAM] Running step {stepNo}: Temperature={step['temperature(C)']}C, RampRate={step['ramp_rate(C/min)']}C/min, Duration={step['duration(s)']}s")
        self.on()
        self.setTemperature(step['temperature(C)'])
        self.setTemperatureRate(step['ramp_rate(C/min)'])
        wait_s = float(step.get('duration(s)', 0))
        end = time.monotonic() + wait_s
        while time.monotonic() < end:
            if stop_evt and stop_evt.is_set():
                break
            time.sleep(min(0.1, end - time.monotonic()))

    async def run_single_step_async(self, stepNo: int, stop_event: asyncio.Event = None) -> None:
        """
        Async wrapper for run_single_step that bridges to a threading.Event.
        """
        thread_stop = threading.Event()
        async def _bridge():
            if stop_event is None:
                return
            await stop_event.wait()
            thread_stop.set()
        bridge_task = asyncio.create_task(_bridge())
        try:
            await asyncio.to_thread(self.run_single_step, stepNo, thread_stop)
        finally:
            if not bridge_task.done():
                bridge_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await bridge_task

    async def run_step_async(self, stepNo: int = 0, stop_event: asyncio.Event = None) -> None:
        """
        Run the thermal stage from a specific step asynchronously.
        """
        if stop_event is None:
            stop_event = asyncio.Event()
        try:
            if not hasattr(self, 'step_config'):
                raise ValueError("No step configuration loaded. Use load_step_config first.")
            if stepNo < 0 or stepNo >= len(self.step_config):
                raise IndexError("Step number out of range.")
            for i in range(stepNo, len(self.step_config)):
                if stop_event.is_set():
                    print("[LINKAM] Stop event detected, aborting step run.")
                    break
                await self.run_single_step_async(i, stop_event=stop_event)
        finally:
            self.off()

    async def run_and_archive(self, output_file=None, stepNo=0, verbose=True, stop_event=None):
        """
        Run Linkam steps and archive PVs asynchronously.
        Responds to external asyncio.Event stop signal.

        Parameters:
            output_file (str, optional): Path to save archived data. If None, uses timestamped default.
            stepNo (int, optional): Step number to start from. Defaults to 0.
            verbose (bool, optional): If True, prints progress information.
            stop_event (asyncio.Event, optional): External stop signal. If set, aborts run.

        This method wraps the Linkam step runner in an archiver context, recording all PVs in pv_list
        to output_file while running the steps. If interrupted, turns off the heater and exits cleanly.
        """
        if output_file is None:
            now = datetime.now().strftime("%Y%m%d-%H-%M-%S")
            output_file = self.folder / f'linkam_archiver_record_{now}.csv'
        pv_list = self.pv_list
        if stop_event is None:
            stop_event = asyncio.Event()
        @archived(output_file, pv_list, verbose=verbose)
        async def run_steps_async():
            await self.run_step_async(stepNo, stop_event=stop_event)
        try:
            await run_steps_async()
        except KeyboardInterrupt:
            print("[LINKAM] Interrupted! Turning off heater.")
            stop_event.set()
            self.off()

##################################################################################


    # def set(self, value):
    #     if value == 'Open':
    #         return self.full.set('Open') #& self.soft.set('Open')
    #     elif value == 'Soft':
    #         return self.soft.set('Open') & self.full.set('Close')
    #     elif value == 'Close':
    #         return self.full.set('Close') & self.soft.set('Close')
    #     else:
    #         raise ValueError("value must be in {'Open', 'Close', 'Soft'}")


##################################################################################

# Legacy Fuctions (Not Used)

# def setLinkamOn(self):
#     caput('XF:11BM-ES:{LINKAM}:STARTHEAT', 1)
#     return 1

# def setLinkamOff(self):
#     caput('XF:11BM-ES:{LINKAM}:STARTHEAT', 0)
#     return 0

# def linkamTemperature(self):
#     return caget('XF:11BM-ES:{LINKAM}:TEMP')
# def setLinkamTemperature(self,temperature ):
#     caput('XF:11BM-ES:{LINKAM}:SETPOINT:SET', temperature)
#     return temperature


# def setLinkamRate(self, rate):
#     caput('XF:11BM-ES:{LINKAM}:RAMPRATE:SET', rate)
#     return rate

# def linkamStatus(self):
#     return caget('XF:11BM-ES:{LINKAM}:STATUS')


# def linkamTensilePos(self):
#     return caget('XF:11BM-ES:{LINKAM}:TST_MOTOR_POS')


class TensileStatus(enum.IntFlag):
    """
    Decoded bits of TST_STATUS (LinkamTensile.status_code_Tensile). This is
    the single translation layer for that raw int - everything else (status
    text, home(), etc.) should read these flags instead of re-deriving
    `code & <bit>` from scratch.
    """
    ZERO_LIMIT = 1
    REF_LIMIT = 2
    MOVE_DONE = 4
    DIRECTION = 8
    FORCE = 16
    CYCLE_MODE = 32
    CYCLE_DIR_OPEN = 64


class LinkamTensile(LinkamThermal, PositionerBase):
    """
    Device interface and experiment orchestration for the Linkam tensile stage.

    Supports step programming with temperature, ramp rate, wait time, position, velocity,
    and automated data archiving of all relevant PVs (temperature, force, position, velocity, etc).

    Also a PositionerBase, so bps.mv(LTensile, target)/LTensile.set(target) work
    natively (with bluesky's standard timeout/pause/progress-bar support). mov()/
    movr() are the blocking, progress-bar-showing user entrypoints built on that;
    _mov()/_movr() are the lower-level, no-wait/no-progress-bar building blocks
    used internally (e.g. by run_single_step()'s async step runner).
    """

    egu = 'um'  # required by PositionerBase; used in progress bar / status displays
    precision = 3  # decimal digits for position display (progress bar, repr, etc.)

    # cmd = Cpt(EpicsSignal, 'STARTHEAT')
    # temperature_setpoint = Cpt(EpicsSignal, 'SETPOINT:SET')
    # temperature_rate_setpoint = Cpt(EpicsSignal, 'RAMPRATE:SET')

    # status = Cpt(EpicsSignalRO, 'STATUS')
    # temperature = Cpt(EpicsSignalRO, 'TEMP')
    # rampRate = Cpt(EpicsSignalRO, 'RAMPRATE')

    # Read-Only signals for the states of the stage
    status_code_Tensile = Cpt(EpicsSignalRO, "TST_STATUS")
    POS = Cpt(EpicsSignalRO, "TST_MOTOR_POS")
    POS_RAW = Cpt(EpicsSignalRO, "TST_RAW_MOTOR_POS")

    FORCE = Cpt(EpicsSignalRO, "TST_FORCE")
    STRAIN = Cpt(EpicsSignalRO, "TST_STRAIN")
    STRESS = Cpt(EpicsSignalRO, "TST_STRESS")

    tensile_maxs_force = Cpt(EpicsSignalRO, "TST_MAX_FORCE")
    tensile_remain_cycles = Cpt(EpicsSignalRO, "TST_CYCLES_REMAINING")

    # Read-Only signals of the set points
    direction = Cpt(EpicsSignalRO, "TST_TABLE_DIR")
    force = Cpt(EpicsSignal, "TST_FORCE_SETPOINT")
    distance = Cpt(EpicsSignal, "TST_MTR_DIST_SP")  # relative distance
    mode = Cpt(EpicsSignalRO, "TST_TABLE_MODE")
    velocity = Cpt(EpicsSignal, "TST_MTR_VEL")

    # Set-and-read signals
    run_cmd = Cpt(EpicsSignal, "TST_START_MOTOR")  # start/stop the motor

    direction_setpoint = Cpt(EpicsSignal, "TST_TABLE_DIR:SET")
    force_setpoint = Cpt(EpicsSignal, "TST_FORCE_SETPOINT:SET")
    distance_setpoint = Cpt(EpicsSignal, "TST_MTR_DIST_SP:SET")  # relative distance
    mode_setpoint = Cpt(EpicsSignal, "TST_TABLE_MODE:SET")
    velocity_setpoint = Cpt(EpicsSignal, "TST_MTR_VEL:SET")

    # not commonly used ones
    J2J_distance = Cpt(EpicsSignal, "TST_JAW_TO_JAW_SIZE")
    J2J_distance_setpoint = Cpt(EpicsSignal, "TST_JAW_TO_JAW_SIZE:SET")

    # PVs to archive for tensile experiments. Units are in the column names:
    # temperature(C), ramp_rate(C/min) [temperature ramp, not stretch speed], duration(s)
    # [step time budget], position(um) [relative move via movr()],
    # velocity(um/s) [stretch/motor speed, not temperature ramp].
    step_columns = ['stepNo', 'temperature(C)', 'ramp_rate(C/min)', 'duration(s)', 'position(um)', 'velocity(um/s)']
    pv_list = [
        'XF:11BM-ES:{LINKAM}:TEMP',          # Temperature
        'XF:11BM-ES:{LINKAM}:RAMPRATE',      # Ramp rate
        'XF:11BM-ES:{LINKAM}:TST_FORCE',     # Force
        'XF:11BM-ES:{LINKAM}:TST_RAW_MOTOR_POS', # Position
        # 'XF:11BM-ES:{LINKAM}:TST_MTR_VEL',   # Velocity
        # 'XF:11BM-ES:{LINKAM}:SETPOINT',      # Setpoint
        # 'XF:11BM-ES:{LINKAM}:TST_STATUS',        # Status
        'XF:11BM-ES:{LINKAM}:POWER'          # Power
    ]

    def __init__(self, prefix, name=None, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.step_setters = {
            'temperature(C)': self.setTemperature,
            'ramp_rate(C/min)': self.setTemperatureRate,
            'position(um)': self.setPosition,
            'velocity(um/s)': self.setVelocity,
        }
        # Feed POS updates into PositionerBase's readback subscription, which
        # MoveStatus subscribes to (event_type=SUB_READBACK) to drive progress
        # bars. Without this, MoveStatus's watchers never get real data.
        self.POS.subscribe(self._position_changed)

    def _position_changed(self, value=None, **kwargs):
        """Forward POS updates to PositionerBase - feeds MoveStatus/progress bars."""
        if value is not None:
            self._set_position(value)

    def trace_tensile_status(self):
        """Print raw and decoded tensile-status updates; return its subscription token."""
        def _trace(value=None, old_value=None, timestamp=None, **kwargs):
            bits = TensileStatus(int(value))
            print(f"[LINKAM-TENSILE] TST_STATUS {old_value!r} -> {int(bits)} "
                  f"(zero={bool(bits & TensileStatus.ZERO_LIMIT)}, "
                  f"ref={bool(bits & TensileStatus.REF_LIMIT)}, "
                  f"done={bool(bits & TensileStatus.MOVE_DONE)}, "
                  f"position={self.POS.get():.3f}um)")

        return self.status_code_Tensile.subscribe(_trace, run=True)

    def stop_tracing_tensile_status(self, token):
        """Stop a status trace started by trace_tensile_status()."""
        self.status_code_Tensile.unsubscribe(token)

    def statusTensile(self, verbosity=3):
        text = f"\nCurrent temperature = {self.temperature():.1f}, setpoint = {self.temperature_setpoint.get():.1f}\n\n"

        # mode_value = self.
        text += f"\nCurrent mode = {self.getMode(verbosity=5):}\n\n"
        bits = self.status_bits

        text += f"Zero Limit        : {'yes' if bits & TensileStatus.ZERO_LIMIT else 'no'}\n"
        text += f"ref Limit         : {'yes' if bits & TensileStatus.REF_LIMIT else 'no'}\n"
        text += f"Move Done         : {'on' if bits & TensileStatus.MOVE_DONE else 'off'}\n"
        text += f"Direction         : {'on' if bits & TensileStatus.DIRECTION else 'off'}\n"
        text += f"Force             : {'yes' if bits & TensileStatus.FORCE else 'no'}\n"
        text += f"Cycle mode        : {'yes' if bits & TensileStatus.CYCLE_MODE else 'no'}\n"
        text += f"Cycle dir open    : {'yes' if bits & TensileStatus.CYCLE_DIR_OPEN else 'no'}\n"

        if verbosity >= 3:
            print(text)
        return int(bits)

    @property
    def status_bits(self) -> TensileStatus:
        """Decoded TST_STATUS bits - see TensileStatus for what each bit means."""
        return TensileStatus(int(self.status_code_Tensile.get()))

    @property
    def zero_limit(self) -> bool:
        """True if the hardware zero (low) limit switch is tripped."""
        return bool(self.status_bits & TensileStatus.ZERO_LIMIT)

    @property
    def ref_limit(self) -> bool:
        """True if the hardware reference (high) limit switch is tripped."""
        return bool(self.status_bits & TensileStatus.REF_LIMIT)

    @property
    def move_done(self) -> bool:
        """True if the motor reports move-complete."""
        return bool(self.status_bits & TensileStatus.MOVE_DONE)

    @property
    def position(self) -> float:
        """Current position (um) - required by PositionerBase (used by bps.mv()/progress bars)."""
        return self.POS.get()

    def _require_velocity(self, velocity: float = None) -> None:
        """
        Raise ValueError if no velocity is configured (the move would silently
        never start), or if a negative velocity was given. velocity is a speed
        magnitude - direction is set separately from the move distance's sign
        (see setDirection()) - and Linkam does not accept a negative velocity.
        """
        if velocity is not None and velocity < 0:
            raise ValueError(f"[LINKAM-TENSILE] velocity must be > 0 (got {velocity}); "
                              "direction is set automatically from the move distance's sign.")
        if velocity is None and self.velocity.get() == 0:
            raise ValueError("[LINKAM-TENSILE] velocity is 0 and no velocity was given; "
                              "the stage would never move.")

    def move(self, position: float, wait: bool = True, timeout: float = None,
             velocity: float = None, settle_time: float = 0.3, **kwargs) -> MoveStatus:
        """
        Move to an absolute position (um). Returns a MoveStatus - ophyd's
        standard positioner status, with its own timeout and .watch() support
        for progress bars. This is what bps.mv(LTensile, target)/set() use;
        mov()/movr() are blocking, progress-bar-showing wrappers around this.
        """
        target = float(position)
        relative_pos = target - self.POS.get()
        status = MoveStatus(self, target, timeout=timeout, settle_time=settle_time)

        if relative_pos == 0:
            status.set_finished()
            return status

        self._require_velocity(velocity)
        command_time = time.monotonic()
        self._movr(relative_pos, velocity=velocity, verbosity=0)

        # TST_STATUS lags the real motor state by ~1s (observed on hardware),
        # so a "done" reading right after commanding the move is not yet
        # trustworthy - it may just be the leftover pre-move value. Only
        # accept it once we've actually seen the busy state this move caused,
        # or once that lag has elapsed (a move too fast for the status word
        # to ever report busy).
        STATUS_LAG = 1.5  # seconds; margin over the observed ~1s IOC status delay

        def _poll_done():
            seen_busy = False
            while not status.done:
                if not self.move_done:
                    seen_busy = True
                elif seen_busy or (time.monotonic() - command_time) > STATUS_LAG:
                    status.set_finished()
                    return
                time.sleep(0.05)

        threading.Thread(target=_poll_done, daemon=True).start()

        if wait:
            status.wait()
        return status

    def set(self, position: float, *, timeout: float = None, moved_cb=None, wait: bool = False, **kwargs) -> MoveStatus:
        """PositionerBase's required set() - delegates to move()."""
        return self.move(position, wait=wait, timeout=timeout, **kwargs)

    def start(self):
        return self.run_cmd.put(1)

    def _start(self):
        yield from bps.mv(self.run_cmd, 1)

    def stop(self, *, success: bool = False):
        return self.run_cmd.put(0)

    def _stop(self):
        yield from bps.mv(self.run_cmd, 0)

    def setMode(self, mode):
        """
        mode = 0 : 'velocity'
        mode = 1 : 'step'
        mode = 2 : 'cycle'
        mode = 3 : 'force'
        mode = 4 : 'relax'
        mode = 5 : 'stop'
        """

        if type(mode) == str:
            if mode == "velocity":
                mode = 0
            elif mode == "step":
                mode = 1
            elif mode == "cycle":
                mode = 2
            elif mode == "force":
                mode = 3
            elif mode == "relax":
                mode = 4
            elif mode == "stop":
                mode = 5
            else:
                return print("Wrong mode.")

        if mode == 0:
            print("Mode:      velocity.")
            print("Constant velocity is expected.")
            print("Inputs are limited to velocity and distance.")

        elif mode == 1:
            print("Mode:      step.")
            print("Distance is expected.")
            print("Inputs are limited to velocity and distance.")

        elif mode == 2:
            print("Mode:      cycle.")
            print("SWITCH TO setp MODE!")
            # print('Inputs are limited to velocity and distance.')

        elif mode == 3:
            print("Mode:      force.")
            print("Constant force is expected.")
            print("Inputs are limited to force and distance.")

        elif mode == 4:
            print("Mode:      relax.")
            print("Nothing is expected except time.")

        elif mode == 5:
            print("Mode:      stop.")

        else:
            return print("[LINKAM-TENSILE] Wrong mode. Please choose from 0-velocity, 1-step, 3-force, 4-relax and 5-stop")

        return self.mode_setpoint.put(mode)

    def getMode(self, verbosity=0):
        value = self.mode_setpoint.get()
        if value == 0:
            mode_value = "velocity"
        elif value == 1:
            mode_value = "step"
        elif value == 2:
            mode_value = "cycle"
        elif value == 3:
            mode_value = "force"
        elif value == 4:
            mode_value = "relax"
        elif value == 5:
            mode_value = "stop"

        if verbosity >= 3:
            return mode_value

        return value

    def _mov(self, position, velocity=None, verbosity=3):
        # move to the absolute position - internal, no wait-for-done/no progress bar.
        # Fire-and-forget: used by move() and by other features (e.g. the async
        # step runner in run_single_step()) that manage their own timing.
        if position < 0:
            return "[LINKAM-TENSILE] Error: position < 0. "

        # set distance
        relative_pos = position - self.POS.get()
        if verbosity >= 3:
            print("[LINKAM-TENSILE] The motor will move {:1f} mm.".format(relative_pos))

        if relative_pos > 0:
            self.setDirection(0)
        elif relative_pos < 0:
            self.setDirection(1)
        else:
            return self.POS.get()

        self._require_velocity(velocity)
        self.distance_setpoint.put(abs(relative_pos))

        # set velocity
        if velocity == None and self.velocity.get() == 0:
            return print("[LINKAM-TENSILE] The velocity is 0. No movement.")
            # self.velocity_setpoint.put(self.velocity.get())
        elif velocity == None and self.velocity.get() != 0:
            pass
        else:
            self.velocity_setpoint.put(velocity)

        self.run_cmd.put(1)
        if verbosity >= 1:
            while int(LTensile.status_code_Tensile.get()) & 4:
                return self.POS.get()

        if verbosity >= 3:
            print(self.POS.get())
        return self.POS.get()

    def _movr(self, distance, velocity=None, verbosity=3):
        # move to the relative position - internal, no wait-for-done/no progress bar.
        # Fire-and-forget: used by move() and by other features (e.g. the async
        # step runner in run_single_step()) that manage their own timing.
        relative_pos = distance
        if relative_pos > 0:  # open
            self.setDirection(0)
        elif relative_pos < 0:  # close
            self.setDirection(1)
        else:
            return self.POS.get()

        self._require_velocity(velocity)
        self.distance_setpoint.put(abs(relative_pos))

        if velocity == None and self.velocity.get() == 0:
            return print("[LINKAM-TENSILE] The velocity is 0. No movement.")
            # self.velocity_setpoint.put(self.velocity.get())
        elif velocity == None and self.velocity.get() != 0:
            pass
        else:
            self.velocity_setpoint.put(velocity)

        self.run_cmd.put(1)
        if verbosity >= 1:
            while int(LTensile.status_code_Tensile.get()) & 4:
                return self.POS.get()

        if verbosity >= 3:
            print(self.POS.get())
        return self.POS.get()

    def mov(self, position: float, velocity: float = None, timeout: float = None,
            settle_time: float = 0.3) -> float:
        """
        User entrypoint: move to an absolute position (um) via the RunEngine
        (RE(bps.mv(self, position))) - the native bluesky mechanism, so this
        gets RE.waiting_hook's progress bar plus pause/resume/interrupt
        support, same as moving a normal EpicsMotor. No need to type RE(...)
        yourself. For the fire-and-forget building block with no wait/progress
        bar (e.g. used by the async step runner), see _mov().
        """
        RE(bps.mv(self, position, velocity=velocity, timeout=timeout, settle_time=settle_time))
        return self.POS.get()

    def movr(self, distance: float, velocity: float = None, timeout: float = None,
             settle_time: float = 0.3) -> float:
        """User entrypoint: relative move (um) via the RunEngine - see mov().
        For the fire-and-forget building block with no wait/progress bar, see _movr()."""
        return self.mov(self.POS.get() + distance, velocity=velocity,
                         timeout=timeout, settle_time=settle_time)

    def home_blocking(self, step_size: float = -200, velocity: float = None,
                      max_steps: int = 500, move_timeout: float = 30.0,
                      verbosity: int = 3) -> float:
        """
        Home the tensile stage (plain blocking call, bypasses the RunEngine).

        Procedure: move to absolute position 0, then repeatedly step by
        step_size (um) until the hardware zero limit switch trips
        (zero_limit; see statusTensile()). The position readback is only
        accurate to ~um and is not used to decide "at zero" - only the zero
        limit switch is authoritative. Each step is driven by move(), which
        handles the wait/timeout itself (see move()).

        Kept alongside home_plan()/home() for quick manual testing outside a
        plan; RE has no visibility into this call (no pause/resume/interrupt).

        Raises ValueError if no velocity is configured (the move would
        silently never start), and RuntimeError if a step doesn't finish
        within move_timeout, or its own RuntimeError if max_steps is
        exhausted first.
        """
        self._require_velocity(velocity)

        if verbosity >= 1:
            print("[LINKAM-TENSILE] Homing: moving to position 0.")
        self.move(0, velocity=velocity, timeout=move_timeout)  # move(), not mov(): no per-step progress bar

        for i in range(max_steps):
            # 1. Already home? Only the zero limit switch is authoritative.
            if self.zero_limit:
                if verbosity >= 1:
                    print(f"[LINKAM-TENSILE] Homing complete after {i} step(s): zero limit reached "
                          f"(position={self.POS.get():.3f}um).")
                return self.POS.get()

            # 2. Not home yet: take one more step (move() waits for it to finish).
            if verbosity >= 3:
                print(f"[LINKAM-TENSILE] Homing step {i}: position={self.POS.get():.3f}um, "
                      f"moving {step_size}um")
            self.move(self.POS.get() + step_size, velocity=velocity, timeout=move_timeout)

        # 3. Ran out of steps without ever satisfying the stopping condition.
        raise RuntimeError(f"[LINKAM-TENSILE] Homing aborted: zero limit not reached after "
                            f"{max_steps} steps (position={self.POS.get():.3f}um).")

    def home_plan(self, step_size: float = -200, velocity: float = None,
                  max_steps: int = 500, move_timeout: float = 30.0,
                  verbosity: int = 3):
        """
        Bluesky plan version of home_blocking(): same procedure and stopping
        condition (only the zero_limit switch, not the position readback -
        see home_blocking()), but drives the moves via bps.abs_set(self, ...)
        - since LinkamTensile is a PositionerBase, this gives the RunEngine
        native pause/resume/interrupt/progress-bar support, no custom
        wait-for-move plan stub needed. Run via RE(LTensile.home_plan()), or
        just call LTensile.home().
        """
        self._require_velocity(velocity)

        if verbosity >= 1:
            print("[LINKAM-TENSILE] Homing: moving to position 0.")
        yield from bps.abs_set(self, 0, wait=True, timeout=move_timeout, velocity=velocity)

        for i in range(max_steps):
            # 1. Already home? Only the zero limit switch is authoritative.
            if self.zero_limit:
                if verbosity >= 1:
                    print(f"[LINKAM-TENSILE] Homing complete after {i} step(s): zero limit reached "
                          f"(position={self.POS.get():.3f}um).")
                return self.POS.get()

            # 2. Not home yet: take one more step (abs_set(wait=True) waits for it to finish).
            if verbosity >= 3:
                print(f"[LINKAM-TENSILE] Homing step {i}: position={self.POS.get():.3f}um, "
                      f"moving {step_size}um")
            yield from bps.abs_set(self, self.POS.get() + step_size, wait=True,
                                    timeout=move_timeout, velocity=velocity)

        # 3. Ran out of steps without ever satisfying the stopping condition.
        raise RuntimeError(f"[LINKAM-TENSILE] Homing aborted: zero limit not reached after "
                            f"{max_steps} steps (position={self.POS.get():.3f}um).")

    def home(self, step_size: float = -2000, velocity: float = 2000,
             max_steps: int = 50, move_timeout: float = 30.0,
             verbosity: int = 3):
        """
        User entrypoint: runs home_plan() through the RunEngine (RE) for you,
        e.g. just call LTensile.home() - no need to type RE(...) yourself.
        For a version that bypasses the RunEngine entirely, see home_blocking().
        """
        return RE(self.home_plan(step_size=step_size, velocity=velocity,
                                  max_steps=max_steps,
                                  move_timeout=move_timeout, verbosity=verbosity))

    def setDirection(self, direction, wait_time=0.1, verbosity=3):
        # 0 = Open, 1 = close
        if direction == 0 or direction == "open":
            self.direction_setpoint.put(0)
            # print("test0")

        elif direction == 1 or direction == "close":
            # print("test1")
            self.direction_setpoint.put(1)
        else:
            print("[LINKAM-TENSILE] Wrong input.")

        time.sleep(wait_time)
        if verbosity >= 3:
            if self.direction.get() == 0:
                text_direction = "open"
            else:
                text_direction = "close"
            print("[LINKAM-TENSILE] Current direction : {}".format(text_direction))

        return self.direction.get()

    def _setDirection(self, direction, verbosity=3):
        # 0 = Open, 1 = close
        if direction == 0 or direction == "open":
            yield from bps.mv(self.direction_setpoint, 0)
        elif direction == 1 or direction == "close":
            yield from bps.mv(self.direction_setpoint, 1)
        else:
            print("[LINKAM-TENSILE] Wrong input.")

        if verbosity >= 3:
            if self.direction.get() == 0:
                text_direction = "open"
            else:
                text_direction = "close"
            print("[LINKAM-TENSILE] Current direction : {}".format(text_direction))

        return self.direction.get()

    def states(self):
        # show the current states of the tensile stage, including
        # T, motor position and direction, force, velocity and mode

        # from Temperature sensor, independent from the tensile
        text = f"\nCurrent temperature = {self.temperature():.1f}, setpoint = {self.temperature_setpoint.get():.1f}\n\n"

        # stage states, RO
        text += f"\nSTAGE POSITION = {self.POS.get():1f}\n\n"
        text += f"\nSTAGE FORCE  = {self.FORCE.get():1f}\n\n"
        text += f"\nSTAGE STRAIN = {self.STRAIN.get():1f}\n\n"
        text += f"\nSTAGE STRESS = {self.STRESS.get():1f}\n\n"

        # setting for the tensile part
        text += f"\nCurrent mode = {self.getMode(verbosity=5)}\n\n"
        text += f"\nCurrent distance = {self.distance.get():1f}, setpoint={self.distance_setposition.get():1f}\n\n"
        text += f"\nCurrent velocity = {self.velocity.get():1f}, setpoint={self.velocity_setposition.get():1f}\n\n"
        text += f"\nCurrent force = {self.force.get():1f}, setpoint={self.force_setposition.get():1f}\n\n"

    # force = Cpt(EpicsSignal, 'TST_FORCE_SETPOINT')
    # distance = Cpt(EpicsSignal, 'TST_MTR_DIST_SP') #relative distance
    # mode = Cpt(EpicsSignalRO, 'TST_TABLE_MODE')
    # velocity = Cpt(EpicsSignal, 'TST_MTR_VEL')

    # Linkam Stage Tensile Step Configuration Read/Load functions
    # Added by Siyu Wu 2025-09-01

    def setPosition(self, position: float) -> float:
        """Set the tensile stage position."""
        while self.POS.get() != position:
            time.sleep(0.2)
            self.distance_setpoint.put(position)
        return self.POS.get()

    def setVelocity(self, velocity: float) -> float:
        """Set the tensile stage velocity."""
        while self.velocity_current.get() != velocity:
            time.sleep(0.2)
            self.velocity_setpoint.put(velocity)
        return self.velocity_current.get()

    def force(self) -> float:
        """Get the current tensile stage force."""
        return self.FORCE.get()

    def run_single_step(self, stepNo: int, stop_evt: threading.Event = None) -> None:
        """
        Run a single tensile step (blocking), responsive to stop_evt.
        Sets all step PVs, triggers motor start, waits, and stops motor if interrupted.
        """
        if not hasattr(self, 'step_config'):
            raise ValueError("No step configuration loaded. Use load_step_config first.")
        if stepNo < 0 or stepNo >= len(self.step_config):
            raise IndexError("Step number out of range.")
        step = self.step_config.iloc[stepNo]
        print(f"[LINKAM-TENSILE] Running step {stepNo}: " +
            ", ".join(f"{col}={step[col]}" for col in self.step_columns if col != 'stepNo'))

        # Set all relevant PVs
        self.setTemperature(step['temperature(C)'])
        self.setTemperatureRate(step['ramp_rate(C/min)'])

        self.on()

        # Use _movr to trigger tensile movement without waiting for it to finish
        # (position(um) is a relative move, velocity(um/s) is speed) - this step's
        # duration(s) budget covers the move, see the CSV header comments.
        self._movr(step['position(um)'], step['velocity(um/s)'])

        try:
            wait_s = float(step.get('duration(s)', 0))
            end = time.monotonic() + wait_s
            while time.monotonic() < end:
                if stop_evt and stop_evt.is_set():
                    print("[LINKAM-TENSILE] Stop event detected, stopping motor.")
                    break
                time.sleep(min(0.1, end - time.monotonic()))
        finally:
            self.stop()

    async def run_single_step_async(self, stepNo: int, stop_event: asyncio.Event = None) -> None:
        """
        Async wrapper for run_single_step that bridges to a threading.Event.
        """
        thread_stop = threading.Event()
        async def _bridge():
            if stop_event is None:
                return
            await stop_event.wait()
            thread_stop.set()
        bridge_task = asyncio.create_task(_bridge())
        try:
            await asyncio.to_thread(self.run_single_step, stepNo, thread_stop)
        finally:
            if not bridge_task.done():
                bridge_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await bridge_task

    async def run_step_async(self, stepNo: int = 0, stop_event: asyncio.Event = None) -> None:
        """
        Run the tensile stage from a specific step asynchronously.
        """
        if stop_event is None:
            stop_event = asyncio.Event()
        try:
            if not hasattr(self, 'step_config'):
                raise ValueError("No step configuration loaded. Use load_step_config first.")
            if stepNo < 0 or stepNo >= len(self.step_config):
                raise IndexError("Step number out of range.")
            for i in range(stepNo, len(self.step_config)):
                if stop_event.is_set():
                    print("[LINKAM-TENSILE] Stop event detected, aborting step run.")
                    break
                await self.run_single_step_async(i, stop_event=stop_event)
        finally:
            self.off()
            self.stop()

try:
    LThermal = LinkamThermal("XF:11BM-ES:{LINKAM}:", name="LinkamTrans")
    # LThermal = LinkamThermal("XF:11BM-ES:{LINKAM}:", name="LinkamGI")
    LTensile = LinkamTensile("XF:11BM-ES:{LINKAM}:", name="LinkamTensile")
except:
    pass
