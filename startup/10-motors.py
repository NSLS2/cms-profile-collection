print(f'Loading {__file__}')

from ophyd import EpicsMotor, EpicsSignal, Device, Component as Cpt
import json
from pathlib import Path
from datetime import datetime

# slity = EpicsMotor('XF:11BMA-OP{Slt:0-Ax:T}Mtr', name='slity')


# class Slits(Device):
#    top = Cpt(EpicsMotor, '-Ax:T}Mtr')
#    bottom = Cpt(EpicsMotor, '-Ax:B}Mtr')
beamline_stage = "default"  #for AB, please also change Smpl2-Y from 3... to -5 
# beamline_stage = 'open_MAXS'
# beamline_stage = 'BigHuber'

print('Beamline_stage = {}'.format(beamline_stage))

# slits = Slits('XF:11BMA-OP{Slt:0', name='slits')

###################################################################################
# above as found on 19 Oct 2016, then commented out
# below added by MF in Oct 2016
###################################################################################


########## Universal Configuration Management for Multi-Motor Devices ##########

class Configurable:
    """Mixin for multi-motor devices: save/load named positions and move motors.

    Features:
    - `get(name)` loads a saved position (no motion).
    - `goto(name)` loads and moves all tracked motors to the saved values.
    - `save_position(name)` stores the current motor positions under `name`.
    - `mov(motor, value)` and `movr(motor, delta)` are short aliases for
      absolute and relative motor movement.

    Example:
        # The s4 config contains: 'trans_inair', 'GI_inair', 'trans_vacuum',
        # and 'GI_vacuum'. 
        # Example usage for s4 (a MotorCenterAndGap instance):

        s4.show_position()                   # print current positions
        s4.goto('trans_inair')               # move s4 to the 'trans_inair' set
        s4.save_position('test')             # save current position as 'test'
        s4.mov('xc', -1.48)                  # absolute move for a single axis
        s4.movr('yg', 0.05)                  # relative move for a single axis

    """
    
    _config_motors = []  # Override in device to specify which motors to track
    _config_file = None  # Override to specify config file path
    
    def get(self, name):
        """
        Load a saved position configuration without moving motors.
        
        Args:
            name: Position name to load
            
        Returns:
            Dict with position data
        """
        return self.load_position(name)
    
    def goto(self, name):
        """
        Load a saved position and move all motors there.
        
        Args:
            name: Position name to load and move to
            
        Usage:
            s4.goto('open')  # Load and move s4 to 'open' position
        """
        positions_dict = self._load_config()
        entries = positions_dict.get(name)
        if entries and isinstance(entries, list):
            target_positions = entries[-1]  # Get latest entry
            print(f"Moving '{self.name}' to position '{name}'...")
            for motor_name in self._config_motors:
                if (hasattr(self, motor_name) and 
                    motor_name in target_positions):
                    motor = getattr(self, motor_name)
                    target_value = target_positions[motor_name]
                    motor.move(target_value)
            self.show_position()
        else:
            print(f"No saved position found for '{name}'.")
    
    def _load_config(self):
        """Load configuration from JSON file."""
        if self._config_file is None:
            self._config_file = Path(f'{self.name}_config.cfg')
        
        config_file = Path(self._config_file) if not isinstance(self._config_file, Path) else self._config_file
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_config(self):
        """Save configuration to JSON file."""
        if self._config_file is None:
            self._config_file = Path(f'{self.name}_config.cfg')
        
        config_file = Path(self._config_file) if not isinstance(self._config_file, Path) else self._config_file
        with open(config_file, 'w') as f:
            json.dump(self._positions, f, indent=2)
    
    def _sync(self):
        """Synchronize internal position cache with actual motor positions."""
        for motor_name in self._config_motors:
            if hasattr(self, motor_name):
                motor = getattr(self, motor_name)
                setattr(self, f'_{motor_name}', motor.position)
    
    def _get_positions_dict(self):
        """Get current positions as a dictionary."""
        positions = {}
        for motor_name in self._config_motors:
            if hasattr(self, motor_name):
                motor = getattr(self, motor_name)
                positions[motor_name] = motor.position
        return positions
    
    def load_position(self, name):
        """Load a saved position configuration by name."""
        positions = self._load_config()
        entries = positions.get(name)
        if entries:
            latest = entries[-1]
            print(f"Loaded position '{name}' from {latest.get('timestamp', 'unknown')}")
            for motor_name in self._config_motors:
                if motor_name in latest and hasattr(self, motor_name):
                    motor = getattr(self, motor_name)
                    setattr(self, f'_{motor_name}', latest[motor_name])
            return latest
        else:
            print(f"No saved position found for '{name}'.")
            return None
    
    def save_position(self, name):
        """Save current position with a given name."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = self._get_positions_dict()
        entry['timestamp'] = timestamp
        
        positions = self._load_config()
        positions.setdefault(name, []).append(entry)
        self._positions = positions
        self._save_config()
        print(f"Saved position '{name}' at {timestamp}.")
    
    def show_position(self):
        """Display current motor positions."""
        self._sync()
        print(f"Device '{self.name}' positions:")
        for motor_name in self._config_motors:
            if hasattr(self, motor_name):
                motor = getattr(self, motor_name)
                print(f"  {motor_name} = {motor.position}")
    
    def relative_move(self, motor_name, delta):
        """Move a motor relative to current position."""
        if motor_name not in self._config_motors or not hasattr(self, motor_name):
            print(f"Invalid motor name: {motor_name}")
            return
        
        motor = getattr(self, motor_name)
        new_pos = motor.position + delta
        motor.move(new_pos)
        print(f"{motor_name} moved relatively by {delta} -> {new_pos}")
    
    def movr(self, motor_name, delta):
        """Move a motor relative to current position (short alias)."""
        return self.relative_move(motor_name, delta)
    
    def absolute_move(self, motor_name, value):
        """Move a motor to an absolute position."""
        if motor_name not in self._config_motors or not hasattr(self, motor_name):
            print(f"Invalid motor name: {motor_name}")
            return
        
        motor = getattr(self, motor_name)
        motor.move(value)
        print(f"{motor_name} moved to {value}")
    
    def mov(self, motor_name, value):
        """Move a motor to an absolute position (short alias)."""
        return self.absolute_move(motor_name, value)
    
    @staticmethod
    def clear_config(config_file):
        """Clear configuration, keeping only the latest entry for each position name."""
        path = Path(config_file)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
            for key in data:
                if isinstance(data[key], list) and len(data[key]) > 0:
                    data[key] = [data[key][-1]]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Configuration file '{config_file}' cleaned: only latest entries retained.")
        else:
            print(f"Config file '{config_file}' does not exist.")


########## motor classes ##########
class MotorCenterAndGap(Device, Configurable):
    "Center and gap using Epics Motor records"
    xc = Cpt(EpicsMotor, "-Ax:XC}Mtr")
    yc = Cpt(EpicsMotor, "-Ax:YC}Mtr")
    xg = Cpt(EpicsMotor, "-Ax:XG}Mtr")
    yg = Cpt(EpicsMotor, "-Ax:YG}Mtr")
    
    _config_motors = ['xc', 'yc', 'xg', 'yg']
    
    def __init__(self, *args, config_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        if config_file is not None:
            self._config_file = Path(config_file)
        self._positions = self._load_config()


class Blades(Device):
    "Actual T/B/O/I and virtual center/gap using Epics Motor records"
    tp = Cpt(EpicsMotor, "-Ax:T}Mtr")
    bt = Cpt(EpicsMotor, "-Ax:B}Mtr")
    ob = Cpt(EpicsMotor, "-Ax:O}Mtr")
    ib = Cpt(EpicsMotor, "-Ax:I}Mtr")
    xc = Cpt(EpicsMotor, "-Ax:XCtr}Mtr")
    yc = Cpt(EpicsMotor, "-Ax:YCtr}Mtr")
    xg = Cpt(EpicsMotor, "-Ax:XGap}Mtr")
    yg = Cpt(EpicsMotor, "-Ax:YGap}Mtr")


class Filter(Device):
    "Attenuator filters"
    sts = Cpt(EpicsSignal, "Pos-Sts")
    in_cmd = Cpt(EpicsSignal, "In-Cmd")
    out_cmd = Cpt(EpicsSignal, "Out-Cmd")


class EllipMirDevice(Device):
    "New 1D focusing elliptical mirror stages on MDrive controller."
    pitch = Cpt(EpicsMotor, ":1}Mtr")
    z = Cpt(EpicsMotor, ":2}Mtr")
    x = Cpt(EpicsMotor, ":3}Mtr")
    y = Cpt(EpicsMotor, "XF:11BMB-ES{Chm:Smpl3-Ax:Y}Mtr", add_prefix=())


# class MotorSlits(Blades, MotorCenterAndGap):
#    "combine t b i o and xc yc xg yg"
#    pass

# class VirtualMotorSlits(Blades, VirtualMotorCenterAndGap):
#    "combine t b i o and xc yc xg yg"
#    pass


########## FOE motors ##########
## stages for Front End (FE) slits (divergence) (FOE)
# FE_x = EpicsMotor('FE:C11B-OP{Slt:12-Ax:X}t2.C', name='FE_x')
# FE_y = EpicsMotor('FE:C11B-OP{Slt:12-Ax:Y}t2.C', name='FE_y')


## stages for monochromator (FOE)
mono_bragg = EpicsMotor("XF:11BMA-OP{Mono:DMM-Ax:Bragg}Mtr", name="mono_bragg")
mono_pitch2 = EpicsMotor("XF:11BMA-OP{Mono:DMM-Ax:P2}Mtr", name="mono_pitch2")
mono_roll2 = EpicsMotor("XF:11BMA-OP{Mono:DMM-Ax:R2}Mtr", name="mono_roll2")
mono_perp2 = EpicsMotor("XF:11BMA-OP{Mono:DMM-Ax:Y2}Mtr", name="mono_perp2")


## stages for toroidal mirror (FOE)
mir_usx = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:XU}Mtr", name="mir_usx")
mir_dsx = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:XD}Mtr", name="mir_dsx")
mir_usy = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:YU}Mtr", name="mir_usy")
mir_dsyi = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:YDI}Mtr", name="mir_dsyi")
mir_dsyo = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:YDO}Mtr", name="mir_dsyo")
mir_bend = EpicsMotor("XF:11BMA-OP{Mir:Tor-Ax:UB}Mtr", name="mir_bend")


########## FOE slits ##########
## FMB Oxford slits -- usage: s0.tp, s0.bt, s0.ob, s0.ib, s0.xc, s0.xg, s0.yc, s0.yg
s0 = Blades("XF:11BMA-OP{Slt:0", name="s0")


########## Endstation slits #########
## jj slits -- usage: s*.xc, s*.xg, s*.yc, s*.yg

# Option 1: Default behavior (config file = {device_name}_config.cfg in current directory)
# s1 = MotorCenterAndGap("XF:11BMB-OP{Slt:1", name="s1")

# Option 2: Custom config file for each slit (recommended for separate tracking)
s1 = MotorCenterAndGap("XF:11BMB-OP{Slt:1", name="s1", config_file='cfg/s1_config.cfg')
s2 = MotorCenterAndGap("XF:11BMB-OP{Slt:2", name="s2", config_file='cfg/s2_config.cfg')
s3 = MotorCenterAndGap("XF:11BMB-OP{Slt:3", name="s3", config_file='cfg/s3_config.cfg')
s4 = MotorCenterAndGap("XF:11BMB-OP{Slt:4", name="s4", config_file='cfg/s4_config.cfg')
s5 = MotorCenterAndGap("XF:11BMB-OP{Slt:5", name="s5", config_file='cfg/s5_config.cfg')

# Practical s4 examples (useful copy-paste snippets):
# The file cfg/s4_config.cfg contains named sets: 'trans_inair', 'GI_inair',
# 'trans_vacuum', and 'GI_vacuum'. Use these names with get/goto.
# Show current positions:
#     s4.show_position()
# Load saved values without moving:
#     data = s4.get('trans_inair')
#     print('trans_inair:', data)
# Move to a saved configuration (performs motion):
#     s4.goto('trans_inair')
# Move to the latest GI vacuum config (there are multiple saved entries):
#     s4.goto('GI_vacuum')
# Single-axis moves (no RE required):
#     s4.mov('xc', -1.48)    # absolute
#     s4.movr('yg', 0.05)    # relative

# Option 3: Share one config file for all slits (if you prefer centralized tracking)
# slits_config_file = 'cfg/slits_config.cfg'
# s1 = MotorCenterAndGap("XF:11BMB-OP{Slt:1", name="s1", config_file=slits_config_file)
# s2 = MotorCenterAndGap("XF:11BMB-OP{Slt:2", name="s2", config_file=slits_config_file)
# s3 = MotorCenterAndGap("XF:11BMB-OP{Slt:3", name="s3", config_file=slits_config_file)
# s4 = MotorCenterAndGap("XF:11BMB-OP{Slt:4", name="s4", config_file=slits_config_file)
# s5 = MotorCenterAndGap("XF:11BMB-OP{Slt:5", name="s5", config_file=slits_config_file)

# attenuators
filters = {
    f"filter{ifoil}": Filter(f"XF:11BMB-OP{{Fltr:{ifoil}}}", name=f"filter{ifoil}") for ifoil in range(1, 8 + 1)
}
# filters_sts = [fil.sts.get() for fil in filters.values()]
# filters_cmd = [fil.cmd.get() for fil in filters.values()]
# locals().update(filters)

########## Endstation motors ##########
## stages for Endstation diagnostics
bim3y = EpicsMotor("XF:11BMB-BI{IM:3-Ax:Y}Mtr", name="bim3y")
fs3y = EpicsMotor("XF:11BMB-BI{FS:3-Ax:Y}Mtr", name="fs3y")
bim4y = EpicsMotor("XF:11BMB-BI{IM:4-Ax:Y}Mtr", name="bim4y")
bim5y = EpicsMotor("XF:11BMB-BI{IM:5-Ax:Y}Mtr", name="bim5y")

## stages for sample positioning
# beamline_stage is defined by the current sample stage. 'default' is the regular vacuum chamber
#'open_WAXS' is the alternative stage position with Pilatus300k as the WAXS detector.
if beamline_stage == "default":
    smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:X}Mtr", name="smx")

    # smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:X}Mtr", name="smx") # change to ESP302 and hardware IOC2, by RL at 20260313
     
    smy = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:Y}Mtr", name="smy")
    # 2023-Sep-12, change sth and schi back to original setting
    sth = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:theta}Mtr", name="sth")
    schi = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:chi}Mtr", name="schi")
    # 2023-Jul-29 theta not stable, switch to chi for incident angle
    # sth = EpicsMotor('XF:11BMB-ES{Chm:Smpl-Ax:chi}Mtr', name='sth')
    # schi = EpicsMotor('XF:11BMB-ES{Chm:Smpl-Ax:theta}Mtr', name='schi')

elif beamline_stage == "open_MAXS":
    smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:X}Mtr", name="smx")
    #changed by RL at 20260312 to change to a temporary stage (borrowed from IXS) for open area. 

    # smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl3-Ax:X}Mtr", name="smx") 
    smy = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:Y}Mtr", name="smy")

    #for test
    # smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl3-Ax:X}Mtr", name="smx") 
    # smy = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:Y}Mtr", name="smy")
    ##

    # smz = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:Z}Mtr", name="smz")
    # sth = EpicsMotor('XF:11BMB-ES{SM:2-Ax:theta}Mtr', name='sth')
    # schi = EpicsMotor('XF:11BMB-ES{SM:2-Ax:chi}Mtr', name='schi')
    # swap sth and schi at 082219 by RL
    sth = EpicsMotor("XF:11BMB-ES{SM:2-Ax:theta}Mtr", name="sth")
    schi = EpicsMotor("XF:11BMB-ES{SM:2-Ax:chi}Mtr", name="schi")

elif beamline_stage == "BigHuber":
    # Huber
    smy = EpicsMotor("XF:11BMB-ES{Chm:Smpl3-Ax:Y}Mtr", name="smy")
    sth = EpicsMotor("XF:11BMB-ES{Chm:Smpl3-Ax:theta}Mtr", name="sth")
    schi = EpicsMotor("XF:11BMB-ES{Chm:Smpl3-Ax:chi}Mtr", name="schi")

    # # Newports for PTA
    # smx = EpicsMotor('XF:11BMB-ES{PTA:Sample-Ax:X}Mtr', name='smx')
    # laserx = EpicsMotor('XF:11BMB-ES{PTA:Laser-Ax:X}Mtr', name='laserx')
    # lasery = EpicsMotor('XF:11BMB-ES{PTA:Laser-Ax:Y}Mtr', name='lasery')

    # # # GDoerk's spray coater
    smx = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:Y}Mtr", name="smx")
    # # smx = EpicsMotor('XF:11BMB-ES{ESP:3-Ax:C1}Mtr', name='smx')
    sprayy = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:X}Mtr", name="sprayy")

#added in 10-27-2025 for telescoping flight path
fpn = EpicsMotor("XF:11BM-ES{Mdrive-Ax:1}Mtr", name="fpn")
fpr = EpicsMotor("XF:11BM-ES{Mdrive-Ax:2}Mtr", name="fpr")

 

# goniometer
smy2 = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:Y2}Mtr", name="smy2")
sphi = EpicsMotor("XF:11BMB-ES{Chm:Smpl-Ax:phi}Mtr", name="sphi")


srot = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Srot}Mtr", name="srot")
strans = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Strans}Mtr", name="strans")
strans2 = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Strans2}Mtr", name="strans2")
stilt = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Stilt}Mtr", name="stilt")
stilt2 = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Stilt2}Mtr", name="stilt2")

# the srot is fixed after repair but two module controllers are broken,
# strans, strans2, stilt, stilt2 and strot are moved to backup controllers
# changed by RL 20220727
# strans =  EpicsMotor('XF:11BMB-ES{Spare:L-Ax:M}Mtr', name='strans')
# strans2 = EpicsMotor('XF:11BMB-ES{Spare:L-Ax:2}Mtr', name='strans2')
# stilt = EpicsMotor('XF:11BMB-ES{Spare:L-Ax:0}Mtr', name='stilt')
# stilt2 = EpicsMotor('XF:11BMB-ES{Spare:L-Ax:1}Mtr', name='stilt2')
# srot = EpicsMotor('XF:11BMB-ES{Spare:L-Ax:L}Mtr', name='srot')

# srot = None
# strans = None
# strans2 = None
# stilt = None
# stilt2 = None

## stages for on-axis sample camera mirror/lens
camx = EpicsMotor("XF:11BMB-ES{Cam:OnAxis-Ax:X1}Mtr", name="camx")
camy = EpicsMotor("XF:11BMB-ES{Cam:OnAxis-Ax:Y1}Mtr", name="camy")

## stages for off-axis sample camera
cam2x = EpicsMotor("XF:11BMB-ES{Cam:OnAxis-Ax:X2}Mtr", name="cam2x")
cam2z = EpicsMotor("XF:11BMB-ES{Cam:OnAxis-Ax:Y2}Mtr", name="cam2z")

## stages for sample exchanger
armz = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Z}Mtr", name="armz")
armx = EpicsMotor("XF:11BMB-ES{SM:1-Ax:X}Mtr", name="armx")
armphi = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Yaw}Mtr", name="armphi")
army = EpicsMotor("XF:11BMB-ES{SM:1-Ax:Y}Mtr", name="army")
# armr = EpicsMotor('XF:11BMB-ES{SM:1-Ax:ArmR}Mtr', name='armr')

# The SmarAct module is broken. Need to change to a SPARE_S for armr
# changed from spareM to spareS by RL at 2021/07/23
# armr = EpicsMotor("XF:11BMB-ES{Spare:L-Ax:S}Mtr", name="armr")
# changed to camy2 as armr was not integrated into MCS2 at 2025/04/02
# armr = EpicsMotor("XF:11BMB-ES{Cam:OnAxis-Ax:Y2}Mtr", name="armr")
armr = EpicsMotor("XF:11BMB-ES{ATT:1-Ax:X}Mtr", name="armr")


## stages for detectors
## currently not working. The new pilatus800k is sitting on a stage with manual movement
# DETx = EpicsMotor('XF:11BMB-ES{Det:Stg-Ax:X}Mtr', name='DETx')
# DETy =  EpicsMotor('XF:11BMB-ES{Det:Stg-Ax:Y}Mtr', name='DETy')
# WAXSx = EpicsMotor('XF:11BMB-ES{Det:WAXS-Ax:X}Mtr', name='WAXSx')
WAXSx = EpicsMotor("XF:11BMB-ES{Det:WAXS-Ax:X}Mtr", name="WAXSx")
WAXSy = EpicsMotor("XF:11BMB-ES{Det:WAXS-Ax:Y}Mtr", name="WAXSy")
WAXSz = EpicsMotor("XF:11BMB-ES{Det:WAXS-Ax:Z}Mtr", name="WAXSz")

SAXSx = EpicsMotor("XF:11BMB-ES{Det:SAXS-Ax:X}Mtr", name="SAXSx")
SAXSy = EpicsMotor("XF:11BMB-ES{Det:SAXS-Ax:Y}Mtr", name="SAXSy")

MAXSx = EpicsMotor("XF:11BMB-ES{Det:MAXS-Ax:X}Mtr", name="MAXSx")
MAXSy = EpicsMotor("XF:11BMB-ES{Det:MAXS-Ax:Y}Mtr", name="MAXSy")

## stages for beamstops
# bsx = EpicsMotor('XF:11BMB-ES{BS:SAXS-Ax:X}Mtr', name='bsx')
# bsy = EpicsMotor('XF:11BMB-ES{BS:SAXS-Ax:Y}Mtr', name='bsy')
# bsphi = EpicsMotor('XF:11BMB-ES{BS:SAXS-Ax:phi}Mtr', name='bsphi')

# beamstop in SmarAct MCS2 controller --- MCS11 --01/18/24
bsx = EpicsMotor("XF:11BMB-ES{BS-Ax:X}Mtr", name="bsx")
bsy = EpicsMotor("XF:11BMB-ES{BS-Ax:Y}Mtr", name="bsy")
bsphi = EpicsMotor("XF:11BMB-ES{BS-Ax:Phi}Mtr", name="bsphi")

# bsx = EpicsMotor("XF:11BMB-ES{Spare:L-Ax:S}Mtr", name="bsx")
# bsy = EpicsMotor("XF:11BMB-ES{Spare:L-Ax:L}Mtr", name="bsy")
# bsphi = EpicsMotor("XF:11BMB-ES{Spare:L-Ax:M}Mtr", name="bsphi")


# beamstop in SmarAct MCS2 controller --- MCS11 --01/18/24
MAXSbsx = EpicsMotor("XF:11BMB-ES{Spare:1-Ax:7}Mtr", name="MAXSbsx")
MAXSbsy = EpicsMotor("XF:11BMB-ES{Spare:1-Ax:8}Mtr", name="MAXSbsy")


def wMAXSbs():
    print(f"MAXSbsx = {MAXSbsx.position:.2f} mm")
    print(f"MAXSbsy = {MAXSbsy.position:.2f} mm")


##stage for vacuum gate
gatex = EpicsMotor("XF:11BMB-ES{Chm:Gate-Ax:X}Mtr", name="gatex")


# Modular Table --- MC07 --10/01/24

TABLEr = EpicsMotor("XF:11BMB-ES{Tbl:Rear-Ax:Z}Mtr", name="TABLEr")
TABLEn = EpicsMotor("XF:11BMB-ES{Tbl:Near-Ax:Z}Mtr", name="TABLEn")
TABLEd = EpicsMotor("XF:11BMB-ES{Tbl:End-Ax:Z}Mtr", name="TABLEd")


# Stages for 1D Focusing Mirror --- Mdrive-01 -- 04/06/2026
EllipMir = EllipMirDevice("XF:11BM1-OP{MDrive", name="EllipMir")

# Backward-compatible aliases.
EllipMir_pitch = EllipMir.pitch
EllipMir_z = EllipMir.z
EllipMir_x = EllipMir.x
EllipMir_y = EllipMir.y

# Add a helper function to print the current positions of the elliptical mirror motors.
def wEllipMir():
    '''
    Print the current positions of the elliptical mirror motors in a readable format.
     - Pitch in degrees with 4 decimal places
     - X, Y, Z in millimeters with 2 decimal places     
    '''
    print('====================================')
    print(f"EllipMir_pitch = {EllipMir_pitch.position:.4f} deg")
    print(f"EllipMir_x = {EllipMir_x.position:.2f} mm")
    print(f"EllipMir_y = {EllipMir_y.position:.2f} mm")
    print(f"EllipMir_z = {EllipMir_z.position:.2f} mm")

# For MDrive (X, Y, edited by YZ, 20230920)
#mdx = EpicsMotor("XF:11BM-ES{Mdrive-Ax:X}Mtr", name="mdx")
#mdy = EpicsMotor("XF:11BM-ES{Mdrive-Ax:Y}Mtr", name="mdy")

# mdx = EpicsMotor("XF:11BM-ES{Mdrive-Ax:6}Mtr", name="mdx")
# mdy = EpicsMotor("XF:11BM-ES{Mdrive-Ax:1}Mtr", name="mdy")


## easy access for stages
def wbs():
    print("bsx = {}".format(bsx.position))
    print("bsy = {}".format(bsy.position))
    print("bsphi = {}".format(bsphi.position))


def wsam():
    print("smx = {}".format(smx.position))
    print("smy = {}".format(smy.position))
    print("sth = {}".format(sth.position))


def wWAXS():
    print("WAXSx = {}".format(WAXSx.position))
    print("WAXSy = {}".format(WAXSy.position))
    print("WAXSz = {}".format(WAXSz.position))


def wSAXS():
    print("SAXSx = {}".format(SAXSx.position))
    print("SAXSy = {}".format(SAXSy.position))


def wMAXS():
    print("MAXSx = {}".format(MAXSx.position))
    print("MAXSy = {}".format(MAXSy.position))


def wGONIO():
    print("sort = {}".format(srot.position))
    print("strans = {}".format(strans.position))
    print("strans2 = {}".format(strans2.position))
    print("stilt = {}".format(stilt.position))
    print("stilt2 = {}".format(stilt2.position))

#Add by RL 2026/03/28
def s5in():
    camy_position = camy.position
    if abs(camy.position-75) < 5:
        print('camy is moving back to beam position.')
        camy.mov(camy_position - 75)
    else:
        print('ERROR: camy is too low/high.')

def s5out():
    camy_position = camy.position
    if abs(camy.position) < 5:
        print('camy is in beam position. Moving out now.')
        camy.mov(camy_position + 75)
    else:
        print('ERROR: camy is too low/high.')

#Add by Siyu 2025/04/14

import time

class Beamstop:
    def __init__(self, name, config_file='beamstop_config.cfg'):
        self.name = name
        self.config_file = Path(config_file)
        self.bsx = bsx.position
        self.bsy = bsy.position
        self.bsphi = bsphi.position
        self.positions = self._load_config()
        self.load()

    @classmethod
    def get(cls, name, config_file='beamstop_config.cfg'):
        print(f"Set current beamstop to '{name}' without moving.")
        return cls(name, config_file=config_file)

    @classmethod
    def goto(cls, name, config_file='beamstop_config.cfg'):
        bs = cls(name, config_file=config_file)
        # bs._move()
        RE(bs._move())
        return bs

    def _load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.positions, f, indent=2)

    def _simulate_move(self):
        print(f"[OFFLINE] Moving motors to {self.name} position:")
        print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}, bsphi -> {self.bsphi}")

    # def _move(self):
    #     print(f"Moving motors to {self.name} position:")
    #     bsx.move(0)
    #     bsy.move(0)
    #     print(f"  bsx -> {0}, bsy -> {0}")
    #     time.sleep(2)
    #     bsphi.move(self.bsphi)
    #     print(f"  bsphi -> {self.bsphi}")
    #     time.sleep(5)
    #     bsx.move(self.bsx)
    #     bsy.move(self.bsy)
    #     print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}")
    #     time.sleep(2)
    #     self.show()
    #     config_update()
    #     config_load()


    def _move(self):
        print(f"Moving motors to {self.name} position:")
        yield from bps.mv(bsx, 0, bsy, 0)
        print(f"  bsx -> {0}, bsy -> {0}")
        yield from bps.mv(bsphi, self.bsphi)
        print(f"  bsphi -> {self.bsphi}")
        yield from bps.mv(bsx, self.bsx, bsy, self.bsy)
        print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}")
        self.show()
        config_update()
        config_load()

    # def move(self):
    #     RE(self._move())

    def x(self):
        print(f"bsx = {self.bsx}")

    def y(self):
        print(f"bsy = {self.bsy}")

    def phi(self):
        print(f"bsphi = {self.bsphi}")

    def xr(self, delta):
        self.bsx += delta
        bsx.move(self.bsx)
        print(f"bsx moved relatively by {delta} mm -> {self.bsx}")

    def yr(self, delta):
        self.bsy += delta
        bsy.move(self.bsy)
        print(f"bsy moved relatively by {delta} mm -> {self.bsy}")

    def phir(self, delta):
        self.bsphi += delta
        bsphi.move(self.bsphi)
        print(f"bsphi moved relatively by {delta} deg -> {self.bsphi}")

    def xabs(self, value):
        self.bsx = value
        bsx.move(self.bsx)
        print(f"bsx moved to {value} mm")

    def yabs(self, value):
        self.bsy = value
        bsy.move(self.bsy)
        print(f"bsy moved to {value} mm")

    def phiabs(self, value):
        self.bsphi = value
        bsphi.move(self.bsphi)
        print(f"bsphi moved to {value} deg")

    def save(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            'bsx': self.bsx,
            'bsy': self.bsy,
            'bsphi': self.bsphi,
            'timestamp': timestamp
        }
        self.positions.setdefault(self.name, []).append(entry)
        self._save_config()
        print(f"Saved current position for '{self.name}' at {timestamp}.")

    def load(self):
        entries = self.positions.get(self.name)
        if entries:
            latest = entries[-1]
            self.bsx = latest['bsx']
            self.bsy = latest['bsy']
            self.bsphi = latest['bsphi']
            print(f"Loaded last position for '{self.name}' from {latest.get('timestamp', 'unknown')}")
        else:
            print(f"No saved position found for '{self.name}'.")

    def show(self):
        print(f"Beamstop '{self.name}':")
        print(f"  bsx = {self.bsx}")
        print(f"  bsy = {self.bsy}")
        print(f"  bsphi = {self.bsphi}")

    @staticmethod
    def clear_cfg(config_file='beamstop_config.cfg'):
        path = Path(config_file)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
            for key in data:
                if isinstance(data[key], list) and len(data[key]) > 0:
                    data[key] = [data[key][-1]]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print("Configuration file cleaned: only latest entries retained.")
        else:
            print("Config file does not exist.")