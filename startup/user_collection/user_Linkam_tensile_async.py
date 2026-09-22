'''
TODO:

1. Save Linkam parameters into the TILED metadata  
2. Integrate the Linkam tensile stage and create a standard method for modes (step, force, velocity)
   -seperate in different modes. 
   -step mode is done. 

'''

#!/usr/bin/python
# -*- coding: utf-8 -*-
# vi: ts=4 sw=4

################################################################################
#  Short-term settings (specific to a particular user/experiment) can
# be placed in this file. You may instead wish to make a copy of this file in
# the user's data directory, and use that as a working copy.
################################################################################

import asyncio
from datetime import datetime
import pickle
import os
from pathlib import Path
from shutil import copyfile

from ophyd import EpicsSignal
from bluesky.suspenders import SuspendFloor, SuspendCeil

ring_current = EpicsSignal('SR:OPS-BI{DCCT:1}I:Real-I')
if False:
    sus = SuspendFloor(ring_current, 100, resume_thresh=400, sleep=600)
    RE.install_suspender(sus)

# Set experiment directories and calibration

RE.md['experiment_alias_directory'] = 'SWu/2_Sanjeeva/Tensile'
# RE.md['userpy_alias_directory'] = '/nsls2/auto-storage/cms/shared/config/bluesky/profile_collection/users/2026-3/SWu/2_Sanjeeva/Tensile/'

#Or automatically generate path by:
RE.md["userpy_alias_directory"] = str(
    Path(bluesky_path()).parent / 'users' / RE.md['cycle'] / RE.md['experiment_alias_directory']
)

cms.SAXS.setCalibration([751, 1081], 5.03, [-65, -73]) #vacuum

def saxs_on():
    detselect(pilatus2M)
    WAXS.goto('out') 

def waxs_on():
    detselect(pilatus300)
    WAXS.goto('in')
 
#cms.setDirectBeamROI()

### DEFINE YOUR PARENT DATA FOLDER HERE 

if False:
    # The following shortcuts can be used for unit conversions. For instance,
    # for a motor operating in 'mm' units, one could instead do:
    #     sam.xr( 10*um )
    # To move it by 10 micrometers. HOWEVER, one must be careful if using
    # these conversion parameters, since they make implicit assumptions.
    # For instance, they assume linear axes are all using 'mm' units. Conversely,
    # you will not receive an error if you try to use 'um' for a rotation axis!
    m = 1e3
    cm = 10.0
    mm = 1.0
    um = 1e-3
    nm = 1e-6
    
    inch = 25.4
    pixel = 0.172 # Pilatus
    
    deg = 1.0
    rad = np.degrees(1.0)
    mrad = np.degrees(1e-3)
    urad = np.degrees(1e-6)
    
def get_default_stage():
    return stg

class Sample(SampleGISAXS_Generic):
    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']

class Sample(SampleTSAXS_Generic):

    def __init__(self, name, base=None, **md):
       
        super().__init__(name=name, base=base, **md)

        self.naming_scheme = ['name', 'extra', 'id', 'clock', 'x', 'LTensile_temperature', 'LTensile_position', 'LTensile_force', 'exposure_time'] #, 'exposure_time']

        self.stage = LTensile.stage
        self._stage = LTensile

        self._axes['x'].origin = self._stage.xo
        self._axes['y'].origin = self._stage.yo
        self._axes['th'].origin = 0
       
        self.exposure_time = 10
        self.SAXS_time = 10
        self.WAXS_time = 10

        self.md['exposure_time'] = self.exposure_time

        self.x_pos_default = [-1, 0, 1]
       
    def get_attribute(self, attribute):
        if attribute=='LTensile_temperature':
            return LTensile.temperature()
        if attribute=='LTensile_position':
            return LTensile.POS.get()
        if attribute=='LTensile_force':
            return LTensile.FORCE.get()
        if attribute=='LTensile_strain':
            return LTensile.STRAIN.get()
        if attribute=='LTensile_stress':
            return LTensile.STRESS.get()

        return super().get_attribute(attribute)

    def get_naming_string(self, attribute):

        # Handle special cases of formatting the text
        super().get_naming_string(attribute)

        if attribute=='LTensile_temperature':
            return '{:.1f}C'.format(self.get_attribute(attribute))
        if attribute=='LTensile_position':
            return '{:.1f}um'.format(self.get_attribute(attribute))
        if attribute=='LTensile_force':
            return '{:.1f}N'.format(self.get_attribute(attribute))
        if attribute=='LTensile_strain':
            return 'Strain{:.1f}'.format(self.get_attribute(attribute))
        if attribute=='LTensile_stress':
            return 'Stress{:.1f}'.format(self.get_attribute(attribute))

        return super().get_naming_string(attribute)


    def get_naming_attribute(self, attribute):
        super().get_naming_string(attribute)
        # if attribute=='temperature_Linkam':
        #     return LThermal.temperature()

    ### Async Linkam Control
    ### Add by Siyu Wu 2025/08/21

    def measure_tensile(self, 
                        exposure_time = None,
                        interval = None, 
                        reset_clock = True,
                        stepNo = 0, 
                        output_file = None, 
                        *args, **kwargs):
        """
        Entry point for user: runs Linkam and archiver async, then triggers Bluesky
        """

        self.naming_scheme = ['name', 'extra', 'id', 'x', 'clock', 'LTensile_temperature', 'LTensile_position', 'LTensile_force', 'exposure_time'] #, 'exposure_time']

        if exposure_time is None:
            exposure_time = self.exposure_time

        if interval is None:
            interval = np.max(self.exposure_time, exposure_time) +10

        async_run(self._measure_tensile_archiver, 
                  exposure_time = exposure_time,
                  interval = interval,
                  reset_clock = reset_clock,
                  stepNo=stepNo,
                  output_file=output_file, 
                  *args, **kwargs)

    async def _measure_tensile_archiver(self, 
                                        exposure_time=None,
                                        interval=None,
                                        reset_clock=True,
                                        stepNo=0, 
                                        output_file=None, 
                                        *args, **kwargs):
        """
        Orchestrate Linkam control/archiver and Bluesky measurement as async tasks.
        Both tasks share an asyncio.Event for robust stopping.

        If either the Linkam archiver or Bluesky measurement task fails or raises an exception,
        the exception is caught, the Linkam heater is turned off, the Linkam stage is stopped, the stop event is sent
        and any remaining tasks are awaited with exceptions suppressed.

        Parameters
        ----------
        stepNo : int, optional
            The step number for the Linkam archiver process (default: 0).
        output_file : str or None, optional
            Path to the output CSV file for archiver data. If None, a default filename is generated.
        *args
            Additional positional arguments passed to the Bluesky measurement function.
        **kwargs
            Additional keyword arguments passed to the Bluesky measurement function.
        """

        if output_file is None:
            now = datetime.now().strftime("%Y%m%d-%H-%M-%S")
            output_file = RE.md["userpy_alias_directory"] + '/'+ self.name + '_linkam_archiver_' + now + '.csv'

        stop_evt = asyncio.Event()

        async def linkam_archiver_task():
            await LTensile.run_and_archive(output_file=output_file, stepNo=stepNo, verbose=True, stop_event=stop_evt)
            stop_evt.set()  # Signal to stop Bluesky when Linkam/archiver is done   

        # Start Linkam/archiver and Bluesky measurement as async tasks
        linkam_task = asyncio.create_task(linkam_archiver_task())
        bluesky_task = asyncio.create_task(self.measureTimeSeries_async(
            exposure_time=exposure_time,
            interval=interval,
            reset_clock=reset_clock,
            stop_event=stop_evt,
            linkam_task=linkam_task,
            *args, **kwargs
        ))

        try:
            await asyncio.gather(linkam_task, bluesky_task)
        except KeyboardInterrupt:
            print("\n[LINKAM] Interrupted by user! Turning off heater and saving archiver data...")
            LTensile.off()
            LTensile.stop()
            stop_evt.set()
            await asyncio.gather(linkam_task, bluesky_task, return_exceptions=True)

    async def measureTimeSeries_async(self, 
                                      maxTime=60*60*24, 
                                      exposure_time=None, 
                                      interval=None, 
                                      reset_clock=True, 
                                      stop_event=None, 
                                      linkam_task=None, 
                                      *args, **kwargs):
        """
        Asynchronously performs a time series measurement using a detector, with periodic intervals and optional external stop conditions.

        Parameters
        ----------
        maxTime : float, optional
            Maximum duration of the measurement in seconds (default: 6 hours).
        exposure_time : float, optional
            Exposure time for each measurement in seconds (default: 0.02).
        interval : float, optional
            Time interval between consecutive measurements in seconds (default: 10).
        reset_clock : bool, optional
            If True, resets the internal clock before starting the measurement (default: True).
        stop_event : threading.Event or asyncio.Event, optional
            External event to signal stopping the measurement early.
        linkam_task : asyncio.Task, optional
            Async task representing Linkam/archiver process; measurement stops when this task is done.
        *args, **kwargs
            Additional arguments passed to the `measure` method.

        Notes
        -----
        - The method triggers the detector at regular intervals using the specified exposure time.
        - Periodically checks for external stop requests and completion of the Linkam/archiver task.
        - Uses asynchronous sleep to maintain compatibility with async event loops.
        - Prints status messages at each measurement and when stopping conditions are met.
        """
        if reset_clock:
            self.reset_clock()
            t0 = time.time()
            t1 = t0

        now = time.time() - t0
        while now < maxTime:
            # Check for external stop
            if stop_event and stop_event.is_set():
                print("[Bluesky] External stop requested.")
                break
            # Check if Linkam/archiver are done
            if linkam_task is not None and linkam_task.done():
                print("[Bluesky] Linkam/archiver finished, stopping measurement.")
                break

            # Trigger detector using Bluesky (blocking)
            print(f"\n[Bluesky] Start measurement at t = {now:.1f}s, T = {LTensile.temperature():.1f}C")
            print(f'\n[Bluesky] Current Position: {LTensile.POS.get():.1f}um, Current Force: {LTensile.FORCE.get():.1f}N')
            
            # TODO make it into a decorator
            # Replace custom measurement plan here


            self.measure(exposure_time, *args, **kwargs)

            # dynamic plan for scan x axis
            # x pos change as a function of tensile stage streth length.
            # L0 = 2.975 # The initial tensile stage pos reading, unit in mm
            # dL = LTensile.POS.get()/1000 - L0 # the change of the tensile stage length, unit in mm
            # sam_length = 5.99 # the length of the sample, unit in mm
            # sam_ROI_0 = 0.15 # the initial region of interest on the sample, unit in mm
            # sam_ROI = sam_ROI_0 * (1 + dL / L0) # the change of the region of interest on the sample, unit in mm

            # for xpos in np.arange(-sam_ROI, sam_ROI+0.01, sam_ROI):
            #     self.xabs(xpos)
                # self.measure(exposure_time, *args, **kwargs)

            # Custom plan for scan y axis
            # for ypos in [-0.3, 0, 0.3]:
            #     self.naming_scheme = ['name', 'extra', 'id', 'clock', 'y', 'LTensile_position', 'LTensile_force', 'exposure_time']
            #     self.yabs(ypos)
            #     time.sleep(1)
            #     self.measure(exposure_time, *args, **kwargs)

            # # Custom plan for burst mode,
            # # it calculates the number of frames needed for a burst 
            # #     based on the velocity and step length, 
            # #     then triggers a series measurement.
            # num_frames = (step_length_um / velocity + 10) / exposure_time  # Number of frames per burst
            # numframes = int(np.ceil(num_frames))
            # self.series_measure(num_frames=numframes,
            #                         exposure_time=exposure_time - 0.005,
            #                         exposure_period=exposure_time,)


            print(f"\n[Bluesky] exposed for {exposure_time:.2f}s, next in {interval}s")

            t1 += interval
            sleep_time = t1 - time.time()
            # Use asyncio.sleep for async compatibility
            while sleep_time > 0:
                # Check every 0.2s for stop or Linkam/archiver completion
                check_time = min(0.2, sleep_time)
                await asyncio.sleep(check_time)
                sleep_time -= check_time
                if stop_event and stop_event.is_set():
                    print("[Bluesky] External stop requested during sleep.")
                    break
                if linkam_task is not None and linkam_task.done():
                    print("[Bluesky] Linkam/archiver finished during sleep, stopping measurement.")
                    break
            now = time.time() - t0

    ########################################################
    # Legacy codes that not been used or are deprecated

    def measureTimeSeries_custom(self, maxTime=60*60*6, exposure_time=10,interval=20, reset_clock=True):
        if reset_clock==True:
            self.reset_clock()
        
        start_time = np.ceil(self.clock()/interval)*interval
        trigger_time = np.arange(start_time, maxTime, interval)

        # while self.clock()<maxTime:
        for trigger in trigger_time:
            while self.clock()<trigger:
                time.sleep(.2)
            self.measure(exposure_time)

    def measure_gridscan(self, exposure_time=10):
        self.naming_scheme = ['name', 'extra', 'x', 'y', 'exposure_time']
        self.gotoOrigin()
        for xpos in [-0.2, 0, 0.2]:
            self.xabs(xpos)
            for ypos in [-0.2, 0, 0.2]:
                self.yabs(ypos)

                time.sleep(2)
                self.measure(exposure_time,extra='gridscan')

        self.gotoOrigin()

if True:
    
    cali = CapillaryHolder(base=stg)

    cali.addSampleSlot( Sample_Calibration('Lab6_cali_5m'), 2.0 )
    cali.addSampleSlot( Sample_Calibration('FL_screen'), 5.0 )
    cali.addSampleSlot( Sample_Calibration('AgBH_cali_5m'), 7.0 )
    cali.addSampleSlot( Sample_Calibration('AgBHCeO2_cali_5m'), 8.0 )
    cali.addSampleSlot( Sample_Calibration('Empty'), 11.0 )


'''
TODO:
### Standard Operation Procedure (SOP) ###


'''

