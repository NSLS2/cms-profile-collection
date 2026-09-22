#!/usr/bin/python
# -*- coding: utf-8 -*-
# vi: ts=4 sw=4


################################################################################
#  Short-term settings (specific to a particular user/experiment) can
# be placed in this file. You may instead wish to make a copy of this file in
# the user's data directory, and use that as a working copy.
################################################################################


#logbooks_default = ['User Experiments']
#tags_default = ['CFN Soft-Bio']

import pickle
import os
from shutil import copyfile
from pathlib import Path


from ophyd import EpicsSignal
from bluesky.suspenders import SuspendFloor, SuspendCeil

if False:
    ring_current = EpicsSignal('SR:OPS-BI{DCCT:1}I:Real-I')
    sus = SuspendFloor(ring_current, 100, resume_thresh=300, sleep=600)
    RE.install_suspender(sus)

### DEFINE YOUR PARENT DATA FOLDER HERE 

RE.md['experiment_alias_directory'] = 'SWu/3_ZhiweiLi/0_StaticGI'
# RE.md['userpy_alias_directory'] = '/nsls2/auto-storage/cms/shared/config/bluesky/profile_collection/users/2026-3/SWu/2_Sanjeeva/Tensile/'

#Or automatically generate path by:
RE.md["userpy_alias_directory"] = str(
    Path(bluesky_path()).parent / 'users' / RE.md['cycle'] / RE.md['experiment_alias_directory']
)


cms.SAXS.setCalibration([743, 1081], 5.03, [-65, -73])

def saxs_on():
    detselect(pilatus2M)
    WAXS.goto('out') 

def alignmode_on():
    cms.modeAlignment()
    detselect(pilatus2M)
    WAXS.goto('half') 

def waxs_on():
    detselect(pilatus300)
    WAXS.goto('in')

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

class SampleTSAXS(SampleTSAXS_Generic):
    
    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        self.naming_scheme = ['name', 'extra', 'exposure_time']

class Sample(SampleGISAXS_Generic):

    def __init__(self, name, base=None, **md):
       
       super().__init__(name=name, base=base, **md)

       #self.naming_scheme = ['name', 'extra', 'clock', 'temperature', 'th', 'exposure_time']
       #self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']
       #self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']
       #self.naming_scheme = ['name', 'extra', 'y', 'th', 'clock', 'exposure_time']
       self.naming_scheme = ['name', 'extra', 'x', 'th', 'exposure_time']
       #self.naming_scheme = ['name', 'extra', 'clock', 'temperature', 'exposure_time']

       self._axes['y'].origin = 9
       self._axes['th'].origin = 0
       
       self.md['exposure_time'] = 1
       #self.SAXS_time = 10 
       #self.WAXS_time = 10
       self.SAXS_time = 10
       self.WAXS_time = 10
       self.WAXS_time_rock = 3
       
       self.incident_angles_default = [0.12, 0.16, 0.20, 0.24]


       self.x_pos_default = [-1, 0, 1]
       
       self.total_flow = 20
       self.wetflow_default = self.total_flow*np.arange(.1, .51, .1)
       self.wetwait_default = [1200,1200,1200,1200,1200]

       self.reset_clock()

    # def _set_axes_definitions(self):
    #     '''Internal function which defines the axes for this stage. This is kept
    #     as a separate function so that it can be over-ridden easily.'''
    #     super()._set_axes_definitions()
        
    #     self._axes_definitions.append( {'name': 'phi',
    #                         'motor': srot,
    #                         'enabled': True,
    #                         'scaling': +1.0,
    #                         'units': 'deg',
    #                         'hint': None,
    #                         } )
    #     self._axes_definitions.append( {'name': 'trans2',
    #                         'motor': strans2,
    #                         'enabled': True,
    #                         'scaling': +1.0,
    #                         'units': 'deg',
    #                         'hint': None,
    #                         } )
        
    # def _measureTimeSeries(self, exposure_time=None, num_frames=10, wait_time=None, extra=None, measure_type='measureTimeSeries', verbosity=3, **md):
        
    #     self.naming_scheme_hold = self.naming_scheme
    #     self.naming_scheme = ['name', 'extra', 'clock', 'exposure_time']
    #     super().measureTimeSeries(exposure_time=exposure_time, num_frames=num_frames, wait_time=wait_time, extra=extra, measure_type=measure_type, verbosity=verbosity, **md)
    #     self.naming_scheme = self.naming_scheme_hold
    
    def goto(self, label, verbosity=3, **additional):
        super().goto(label, verbosity=verbosity, **additional)
        # You can add customized 'goto' behavior here
        
    # def scan_SAXSdet(self, exposure_time=None) :
    #     SAXS_pos=[-73, 0, 73]
    #     #SAXSx_pos=[-65, 0, 65]
        
    #     RE.md['stitchback'] = True
                
    #     for SAXSx_pos in SAXS_pos:
    #         for SAXSy_pos in SAXS_pos:
    #             mov(SAXSx, SAXSx_pos)
    #             mov(SAXSy, SAXSy_pos)
    #             self.measure(10)

    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam
    def do(self, step=0, align_step=0, **md):
        
        #NOTE: if align_step =8 is not working, try align_step=4
        
        if step<=1:
            saxs_on()
            get_beamline().modeAlignment()
            
        if step<=2:
            self.xo() # goto origin


        if step<=4:
            self.yo()
            self.tho()
        
        if step<=5:
            self.align(step=align_step, reflection_angle=0.15)
            #self.setOrigin(['y','th']) # This is done within align

        #if step<=7:
            #self.xr(0.2)

        if step<=8:
            get_beamline().modeMeasurement()
        
        if step<=10:

            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles
                
            swaxs_on()
            self.measureIncidentAngles(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)

            self.thabs(0.0)
            

    def x_scan(self, samth=0.12, exposure_time=10):

        self.gotoOrigin()
        self.thabs(samth)        
        if self.incident_angles==None:
            incident_angles = self.incident_angles_default
        else:
            incident_angles = self.incident_angles
        # saxs_on()
        self.measureIncidentAngles_Stitch(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)
        for x in np.arange(-1, 1.01, 0.2):
            self.xabs(x)
            self.measure(exposure_time, extra='location1')

        if pilatus2M in cms.detector:
            SAXSy.move(SAXSy.position+5.16)           
        elif pilatus800 in cms.detector:
            WAXSy.move(WAXSy.position+5.16)           

        for x in np.arange(-1, 1.01, 0.2):
            self.xabs(x)
            self.measure(exposure_time, extra='location2')            

        if pilatus2M in cms.detector:
            SAXSy.move(SAXSy.position-5.16)           
        elif pilatus800 in cms.detector:
            WAXSy.move(WAXSy.position-5.16)           

    # DEPRECATED
    # TODO USE what is defined in startup/26-IonChamber.py
    # def IC_int(self):
        
    #     ion_chamber_readout1=caget('XF:11BMB-BI{IM:3}:IC1_MON')
    #     ion_chamber_readout2=caget('XF:11BMB-BI{IM:3}:IC2_MON')
    #     ion_chamber_readout3=caget('XF:11BMB-BI{IM:3}:IC3_MON')
    #     ion_chamber_readout4=caget('XF:11BMB-BI{IM:3}:IC4_MON')
        
    #     ion_chamber_readout=ion_chamber_readout1+ion_chamber_readout2+ion_chamber_readout3+ion_chamber_readout4
        
    #     return ion_chamber_readout>1*5e-08

    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam
    def do_SAXS(self, step=0, align_step=0, **md):
        
        if step<=1:
            saxs_on()
            get_beamline().modeAlignment()
            
        if step<=2:
            self.xo() # goto origin


        if step<=4:
            self.yo()
            self.tho()
        
        if step<=5:
            self.align(step=align_step, reflection_angle=0.12)
            #self.setOrigin(['y','th']) # This is done within align

        #if step<=7:
            #self.xr(0.2)

        if step<=8:
            get_beamline().modeMeasurement()
        
        if step<=10:
            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles
            
            # if 'ME_TCTA&Ir(ppy)3' in self.name:
            #     self.SAXS_time = 60
            # if 'ES' in self.name:
            #     swaxs_on()
            #     self.measureIncidentAngles_Stitch(incident_angles, exposure_time=120, tiling='ygaps', **md)
            # else:
            #     saxs_on()
            #     self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)
            #     # if 'thin' in self.name:
            #     #     self.measureIncidentAngle(0.12, exposure_time=120)
            saxs_on()
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)
             


            #if self.exposure_time_SAXS==None:
                #self.measureIncidentAngles(incident_angles, exposure_time=self.SAXS_time, tiling=self.tiling, **md)
            #else:
                #self.measureIncidentAngles(incident_angles, exposure_time=self.exposure_time_SAXS, tiling=self.tiling, **md)

            self.thabs(0.0)

    ###############    
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam    
    def do_WAXS_only(self, step=0, align_step=0, **md):
        if step<5:
            self.xo()
            self.yo()
            self.tho()
            get_beamline().modeMeasurement()        
        if step<=10:
            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles
                
            waxs_on()
            #for detector in get_beamline().detector:
                #detector.setExposureTime(self.MAXS_time)
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.WAXS_time, tiling='ygaps', **md)
            #self.xabs(0.5)
            #self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.WAXS_time, tiling='ygaps', **md)
            

    ###############
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam 
    def do_SAXS_measure(self, step=0, align_step=0, **md):
        if step<5:
            self.xo()
            self.yo()
            self.tho()
            get_beamline().modeMeasurement()        
        if step<=10:
            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles
                
            saxs_on()
            #for detector in get_beamline().detector:
                #detector.setExposureTime(self.MAXS_time)
            #self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps',**md)
            self.thabs(0.0)            
 
    ##### For checking one sample
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam 
    def do_WAXS(self, step=0, align_step=0, reflection_angle=0.12,   **md):
    
        if step<=1:
            saxs_on()
            get_beamline().modeAlignment()
            
        if step<=2:
            self.xo() # goto origin


        if step<=4:
            self.yo()
            self.tho()
        
        if step<=5:
            self.align(step=align_step, reflection_angle=reflection_angle )
            #self.setOrigin(['y','th']) # This is done within align

        #if step<=7:
            #self.xr(0.2)

        if step<=8:
            get_beamline().modeMeasurement()
        
        if step<=10:
            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles


            if self.measure_setting['exposure_time']==None:
                exposure_time = self.WAXS_time
            else:
                exposure_time = self.measure_setting['exposure_time']
                
            waxs_on()
            #for detector in get_beamline().detector:
                #detector.setExposureTime(self.MAXS_time)
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)
            
            self.thabs(0.0)

    ##### For checking one sample
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam 
    def do_WAXS_align(self, step=0, align_step=0, reflection_angle=0.12,   **md):
    
        if step<=1:
            saxs_on()
            get_beamline().modeAlignment()
            
        if step<=2:
            self.xo() # goto origin


        if step<=4:
            self.yo()
            self.tho()
        
        if step<=5:
            self.align(step=align_step, reflection_angle=reflection_angle )
            #self.setOrigin(['y','th']) # This is done within align

        #if step<=7:
            #self.xr(0.2)

        #if step<=8:
            #get_beamline().modeMeasurement()
    
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam 
    def do_WAXS_measure(self, step=0, **md):

        if step<=1:
            self.gotoOrigin()

        if step<=10:
            if self.incident_angles==None:
                incident_angles = self.incident_angles_default
            else:
                incident_angles = self.incident_angles

            incident_angle_large = [angle for angle in incident_angles if angle>5]

            if self.measure_setting['exposure_time']==None:
                exposure_time = self.WAXS_time
            else:
                exposure_time = self.measure_setting['exposure_time']
            
            get_beamline().modeMeasurement()            
            waxs_on()
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)


            #for detector in get_beamline().detector:
                #detector.setExposureTime(self.MAXS_time)
            
            # for xpos in np.arange(-5, 5.1, .5):
            #     self.xabs(xpos)
            #     self.measureIncidentAngles_Stitch(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)

            #rock
            # if 1: #'PBTTT' in self.name:
            #     rock_angle = 1.16
            #     rock_motor_limits = 0.46
            # elif 'PCD' in self.name:
            #     rock_angle = 0.98
            #     rock_motor_limits = 0.68
            # self.measureRock(rock_angle, exposure_time=self.WAXS_time_rock, rock_motor=sth, rock_motor_limits=rock_motor_limits, extra='rock', **md)


            # self.xabs(1)
            # self.measureIncidentAngles_Stitch(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)

                
            self.thabs(0.0)        



class GIBar_Custom(GIBar):
    def __init__(self, name='GIBarCustom', base=None, **kwargs):
        super().__init__(name=name, base=base, **kwargs)
       
        #self._axes['x'].origin = -59.3
        ##position for calibration 
        self._axes['x'].origin = -71.35
        self._axes['y'].origin = 7
        self._axes['th'].origin = 0.1
        self.setPosition()
        
        # CREATE DIRECTORIES TO SAVE DATA
        #holder_data_folder = os.path.join(parent_data_folder, self.name)
        #os.makedirs(holder_data_folder, exist_ok=True)
        #os.makedirs(os.path.join(holder_data_folder, 'waxs'), exist_ok=True)
        #os.makedirs(os.path.join(holder_data_folder, 'saxs'), exist_ok=True)
        #os.makedirs(os.path.join(holder_data_folder, 'waxs/raw'), exist_ok=True)
        #os.makedirs(os.path.join(holder_data_folder, 'saxs/raw'), exist_ok=True)
        #RE.md['experiment_alias_directory'] = holder_data_folder
        
        #### COPY CURRENT STATE OF user.py TO SAMPLE DIRECTORY
        #copyfile(os.path.join(parent_data_folder, 'user.py'), os.path.join(holder_data_folder,'user.py'))
                    
    # TODO
    # Refracture it so it does not live in Sample Class
    # Make it into a standalone function that accepts hol/sam 
    def doSamples(self, verbosity=3):

        #maxs_on()
        for sample in self.getSamples():
            if verbosity>=3:
                print('Doing sample {}...'.format(sample.name))
            if sample.detector=='SAXS' or sample.detector=='BOTH':
                sample.do_SAXS()

        for sample in self.getSamples():
            if verbosity>=3:
                print('Doing sample {}...'.format(sample.name))
            if sample.detector=='WAXS':
                sample.do_WAXS_align()

        for sample in self.getSamples():
            if verbosity>=3:
                print('Doing sample {}...'.format(sample.name))
            if sample.detector=='BOTH' or  sample.detector=='WAXS':
                sample.do_WAXS_measure()

                
    ###############The new alignement procedure.                   
    #def doSamples(self, step=0, verbosity=3):

        #if step<10:
            #self.alignSamples_Custom(step=step)
        
        #if step<15:
            #for sample in self.getSamples():
                #if verbosity>=3:
                    #print('Doing sample {}...'.format(sample.name))
                #if sample.detector=='SAXS' or sample.detector=='SAXS':
                    #sample.do_SAXS_only()

            #for sample in self.getSamples():
                #if verbosity>=3:
                    #print('Doing sample {}...'.format(sample.name))
                #if sample.detector=='WAXS' or sample.detector=='SAXS':
                    #sample.do_WAXS_only()

    def doTemperatures(self, step=0, reset_clock=True, temperature_heat_list=[100], temperature_cool_list=[100, 45],temperature_list=None, tiling=None, output_file='Transmission_output', int_measure=False, wait_time=600, temperature_probe='A', output_channel='1', temperature_tolerance=1,  temp_tolerance=1, poling_period=2.0, verbosity=3,**md):

        #cms.modeMeasurement()
        if temperature_list==None:
            temperature_list = self.temperature_list

        if reset_clock==True:
            for sample in self.getSamples():
                sample.reset_clock()
        #RT
        if step < 1:

            self.doSamples()            

        #heating
        if step < 5:
            for index, temperature in enumerate(temperature_heat_list):
                # Set new temperature
                self.setTemperature(temperature, output_channel=output_channel, verbosity=verbosity)
                
                # Wait until we reach the temperature
                start_time = time.time()
                while abs(self.temperature(temperature_probe=temperature_probe, verbosity=0) - temperature)>temperature_tolerance and time.time()-start_time<1000:
                    if verbosity>=3:
                        print('  setpoint = {:.3f}°C, Temperature = {:.3f}°C          \r'.format(self.temperature_setpoint()-273.15, self.temperature(temperature_probe=temperature_probe, verbosity=0)), end='')
                    time.sleep(poling_period)
                    
                # Allow for additional equilibration at this temperature
                sam=self.gotoSample(1)
                sam.xr(0.2)
                sam.setOrigin['x']
                sam.do_SAXS()
                sam.do_WAXS_measure()

        #max T=150
        if step < 10:
            temperature=150
            self.setTemperature(temperature, output_channel=output_channel, verbosity=verbosity)
            
            # Wait until we reach the temperature
            start_time = time.time()
            while abs(self.temperature(temperature_probe=temperature_probe, verbosity=0) - temperature)>temperature_tolerance and time.time()-start_time<1000:
                if verbosity>=3:
                    print('  setpoint = {:.3f}°C, Temperature = {:.3f}°C          \r'.format(self.temperature_setpoint()-273.15, self.temperature(temperature_probe=temperature_probe, verbosity=0)), end='')
                time.sleep(poling_period)

            start_time_150 = time.time()    
            self.doSamples()         

            while time.time() - start_time_150< 3600*3:
                sam=self.gotoSample(1)
                sam.xr(0.2)
                sam.setOrigin['x']
                sam.do_SAXS()
                sam.do_WAXS_measure()
                time.sleep(60*15)

        #cooling
        if step < 15:
            for index, temperature in enumerate(temperature_cool_list):
                # Set new temperature
                self.setTemperature(temperature, output_channel=output_channel, verbosity=verbosity)
                
                # Wait until we reach the temperature
                start_time = time.time()
                while abs(self.temperature(temperature_probe=temperature_probe, verbosity=0) - temperature)>temperature_tolerance and time.time()-start_time<1000:
                    if verbosity>=3:
                        print('  setpoint = {:.3f}°C, Temperature = {:.3f}°C          \r'.format(self.temperature_setpoint()-273.15, self.temperature(temperature_probe=temperature_probe, verbosity=0)), end='')
                    time.sleep(poling_period)
                    
                # Allow for additional equilibration at this temperature
                sam=self.gotoSample(1)
                sam.xr(0.2)
                sam.setOrigin['x']
                sam.do_SAXS()
                sam.do_WAXS_measure()                


        if step < 20:
            temperature=45
            self.setTemperature(temperature, output_channel=output_channel, verbosity=verbosity)
            
            # Wait until we reach the temperature
            start_time = time.time()
            while abs(self.temperature(temperature_probe=temperature_probe, verbosity=0) - temperature)>temperature_tolerance and time.time()-start_time<1000:
                if verbosity>=3:
                    print('  setpoint = {:.3f}°C, Temperature = {:.3f}°C          \r'.format(self.temperature_setpoint()-273.15, self.temperature(temperature_probe=temperature_probe, verbosity=0)), end='')
                time.sleep(poling_period)

            self.doSamples()      

        if step < 25:
            self.setTemperature(25)
    
    # DESPRECATED FEATURE
    def alignSamples_Custom(self, step=0, align_step=0, verbosity=3, **md):
    
        cali_sample=None

        #search the middle sample for a full alignment
        if step < 10:
            #cali_sample = self.getSample(1) 
            sample_pos_list = []
            for sample in self.getSamples():
                sample_pos_list.append(sample.position)
                cali_sample = sample
            hol_xcenter = min(sample_pos_list)/2+max(sample_pos_list)/2
            
            print(sample_pos_list)
            
            #locate the sample for alignning the holder
            for sample in self.getSamples():
                if abs(sample.position-hol_xcenter) < abs(cali_sample.position-hol_xcenter):
                    cali_sample = sample
                print('The current calibraion sample is {}'.format(cali_sample.name))

            print('The calibraion sample is {}'.format(cali_sample.name))
                
        if step < 15:
            #full alignment on cali_sample
            #cali_sample.align()
            saxs_on()
            get_beamline().modeAlignment()
            cali_sample.gotoOrigin()
            cali_sample.align(step=0)           
            cali_sample.gotoOrigin()
            #cali_sample.yo()
            #cali_sample.tho()

        #set the th and y of other samples
        if step < 20:
            for sample in self.getSamples():
                sample.setOrigin(['th', 'y'])
            
        #quickly align other samples
        if step < 30:
            cms.modeAlignment()
            for sample in self.getSamples():
                if sample != cali_sample:
                    
                    print('Aligning sample {}...'.format(sample.name))
                    sample.gotoOrigin()
                    sample.align_custom(step=align_step)   
                    sample.gotoOrigin()
                    #wsam()

# def do(sample, step=0, align_step=0, **md):
    
#     #WIP: A unverrified draft for sample alignment procedure
    
#     if step<=1:
#         saxs_on()
#         get_beamline().modeAlignment()
        
#     if step<=2:
#         self.xo() # goto origin

#     if step<=4:
#         self.yo()
#         self.tho()
    
#     if step<=5:
#         self.align(step=align_step, reflection_angle=0.15)
#         #self.setOrigin(['y','th']) # This is done within align

#     #if step<=7:
#         #self.xr(0.2)

#     if step<=8:
#         get_beamline().modeMeasurement()
    
#     if step<=10:

#         if self.incident_angles==None:
#             incident_angles = self.incident_angles_default
#         else:
#             incident_angles = self.incident_angles
            
#         swaxs_on()
#         self.measureIncidentAngles(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)

#         self.thabs(0.0)


if True:
    
    cali = CapillaryHolder(base=stg)

    cali.addSampleSlot( Sample_Calibration('Lab6_cali_5m'), 2.0 )
    cali.addSampleSlot( Sample_Calibration('FL_screen'), 5.0 )
    cali.addSampleSlot( Sample_Calibration('AgBH_cali_5m'), 7.0 )
    cali.addSampleSlot( Sample_Calibration('AgBHCeO2_cali_5m'), 8.0 )
    cali.addSampleSlot( Sample_Calibration('Empty'), 11.0 )

if True:
    
    # Example of a multi-sample holder
    # Copy-paste the autogenerated script from google spreedsheet here
    
    md = {
        'owner' : 'UserName' ,
        'series' : 'various' ,
        }
    
    hol1 = GIBar_Custom(base=stg)
    hol1.addGaragePosition(1,1)
    hol1.name = 'hol1'
    hol1.addSampleSlotPosition( Sample('ZWLi_1_CNCl_1', **md),1, 5,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_2_CNCl_2', **md),2, 13,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_3_CNCl_3', **md),3, 21,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_4_CNCl_4', **md),4, 30,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_5_CNCl_5', **md),5, 37.5,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_6_MPB_1', **md),6, 51,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_7_MPB_2', **md),7, 59,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_8_MPB_3', **md),8, 67,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_9_MPB_4', **md),9, 75,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])
    hol1.addSampleSlotPosition( Sample('ZWLi_10_MPB_5', **md),10, 83,'BOTH', incident_angles=[0.08,0.10,0.12,0.14,0.16])

    # Comment out the queue section if not using robot sample changer
    
    # que = Queue(base=stg)

    # que.addHolderIntoQueue(hol1, [1, 1], 1)   
    # que.addHolderIntoQueue(hol2, [1, 2], 2)   
    # que.addHolderIntoQueue(hol3, [1, 3], 3) 
    # que.addHolderIntoQueue(hol4, [2, 1],4)
    # que.addHolderIntoQueue(hol5, [2, 2], 5)   
    # que.addHolderIntoQueue(hol6, [2, 3], 6)   
    # que.addHolderIntoQueue(hol7, [3, 1], 7)   
    # que.addHolderIntoQueue(hol8, [3, 2], 8)   
    # que.addHolderIntoQueue(hol9, [3, 3], 9)  
    # que.addHolderIntoQueue(hol10, [4, 1], 10)  
    # que.addHolderIntoQueue(hol11, [4, 2], 11)  
    # que.addHolderIntoQueue(hol12, [4, 3], 12)  

    # que.setSequence()  
    # que.checkStatus(verbosity=5) 


# sam=Sample('test')
# detselect([fs4])
# sam.measure(1)

'''
TODO:
### Standard Operation Procedure (SOP) ###

cms.ventSample()
cms.pumpSample()

startWAXS()

ctrl+S to save the scripts first, then
"%run -i ..."  to reload the scripts

hol1.listSamples()   #check sample name has been updated
hol1.gotoOrigin()    #goto hol1 origin
hol1.yr(-4)          #lower the bar
hol1.setOrigin('y')  #reset the origin
hol2.setOrigin('y')
..

que.runHolders()


history




'''