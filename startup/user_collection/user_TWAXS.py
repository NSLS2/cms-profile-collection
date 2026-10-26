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

ring_current = EpicsSignal('SR:OPS-BI{DCCT:1}I:Real-I')
sus = SuspendFloor(ring_current, 100, resume_thresh=300, sleep=600)
RE.install_suspender(sus)

### DEFINE YOUR PARENT DATA FOLDER HERE 

RE.md['experiment_alias_directory'] = 'Test/0_Static'
# RE.md['userpy_alias_directory'] = '/nsls2/auto-storage/cms/shared/config/bluesky/profile_collection/users/2026-3/SWu/2_Sanjeeva/Tensile/'

#Or automatically generate path by:
# RE.md["userpy_alias_directory"] = str(
#     Path(bluesky_path()).parent / 'users' / RE.md['cycle'] / RE.md['experiment_alias_directory'] ) 
RE.md["userpy_alias_directory"] = str(
    Path('/nsls2/data/cms/shared/config/bluesky/profile_collection/users') / RE.md['cycle'] / RE.md['experiment_alias_directory']
)

cms.SAXS.setCalibration([744, 1081], 5.03, [-65, -73]) #vacuum

def saxs_on():
    detselect([pilatus2M,pilatus300])
    WAXS.goto('out')

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


class SampleGISAXS(SampleGISAXS_Generic):
    
    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']
        self.naming_scheme = ['name', 'extra', 'clock', 'temperature', 'exposure_time']


class Sample(SampleTSAXS):
# class Sample(SampleGISAXS):

    def __init__(self, name, base=None, **md):
       
       super().__init__(name=name, base=base, **md)

       self.naming_scheme = ['name', 'extra', 'x', 'y', 'exposure_time']
       #self.naming_scheme = ['name', 'extra', 'clock', 'temperature', 'exposure_time']

       self._axes['x'].origin = -18.2
       self._axes['y'].origin = 7.4         

       self.md['exposure_time'] = 1
       self.SAXS_time = 10
       self.WAXS_time = 10
       self.WAXS_time_rock = 3
       
       #self.incident_angles_default = [0.08, 0.10, 0.12, 0.15, 0.20]

       self.x_pos_default = [-1, 0, 1]
       
       self.total_flow = 20
       self.wetflow_default = self.total_flow*np.arange(.1, .51, .1)
       self.wetwait_default = [1200,1200,1200,1200,1200]
        
    def _measureTimeSeries(self, exposure_time=None, num_frames=10, wait_time=None, extra=None, measure_type='measureTimeSeries', verbosity=3, **md):
        
        self.naming_scheme_hold = self.naming_scheme
        self.naming_scheme = ['name', 'extra', 'clock', 'exposure_time']
        super().measureTimeSeries(exposure_time=exposure_time, num_frames=num_frames, wait_time=wait_time, extra=extra, measure_type=measure_type, verbosity=verbosity, **md)
        self.naming_scheme = self.naming_scheme_hold
    
    def goto(self, label, verbosity=3, **additional):
        super().goto(label, verbosity=verbosity, **additional)
        # You can add customized 'goto' behavior here
        
    def scan_SAXSdet(self, exposure_time=None) :
        SAXS_pos=[-73, 0, 73]
        #SAXSx_pos=[-65, 0, 65]
        
        RE.md['stitchback'] = True
                
        for SAXSx_pos in SAXS_pos:
            for SAXSy_pos in SAXS_pos:
                mov(SAXSx, SAXSx_pos)
                mov(SAXSy, SAXSy_pos)
                self.measure(10)
                
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
            self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)
            #waxs_on()
            #self._test2_measureIncidentAngles(self.incident_angles_default, exposure_time=self.WAXS_time, tiling='ygaps', **md)

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

        
    def IC_int(self):
        
        ion_chamber_readout1=caget('XF:11BMB-BI{IM:3}:IC1_MON')
        ion_chamber_readout2=caget('XF:11BMB-BI{IM:3}:IC2_MON')
        ion_chamber_readout3=caget('XF:11BMB-BI{IM:3}:IC3_MON')
        ion_chamber_readout4=caget('XF:11BMB-BI{IM:3}:IC4_MON')
        
        ion_chamber_readout=ion_chamber_readout1+ion_chamber_readout2+ion_chamber_readout3+ion_chamber_readout4
        
        return ion_chamber_readout>1*5e-08


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

            if 'RL_XY_SL' in self.name:
                swaxs_on()
                for xpos in np.arange(-2, 2.1, 0.5):
                    self.xabs(xpos)
                    self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)
            else:
                saxs_on()
                self.measureIncidentAngles_Stitch(incident_angles, exposure_time=self.SAXS_time, tiling='ygaps', **md)


            #if self.exposure_time_SAXS==None:
                #self.measureIncidentAngles(incident_angles, exposure_time=self.SAXS_time, tiling=self.tiling, **md)
            #else:
                #self.measureIncidentAngles(incident_angles, exposure_time=self.exposure_time_SAXS, tiling=self.tiling, **md)

            self.thabs(0.0)

    ###############        
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

            #for detector in get_beamline().detector:
                #detector.setExposureTime(self.MAXS_time)
            
            # for xpos in np.arange(-5, 5.1, .5):
            #     self.xabs(xpos)
            self.measureIncidentAngles(incident_angles, exposure_time=exposure_time, tiling='ygaps', **md)

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

@with_tiling()
def do_holder(holder, exposure_time=10, extra=None, **md):
    for sample in holder.getSamples():
        sample.gotoOrigin()
        time.sleep(1)
        sample.measureSpots(num_spots=4, axis='x',exposure_time=exposure_time, extra=extra, **md)
        sample.measureSpots(num_spots=4, axis='y',exposure_time=exposure_time, extra=extra, **md)
        # sample.measure(exposure_time=exposure_time, **md)

if True:
    
    cali = CapillaryHolder(base=stg)
    #hol = CapillaryHolderCustom(base=stg)

    cali.addSampleSlot( Sample_Calibration('Lab6_cali_5m'), 2.0 )
    cali.addSampleSlot( Sample_Calibration('FL_screen'), 5.0 )
    cali.addSampleSlot( Sample_Calibration('AgBH_cali_5m'), 7.0 )
    cali.addSampleSlot( Sample_Calibration('AgBHCeO2_cali_5m'), 8.0 )
    cali.addSampleSlot( Sample_Calibration('Empty'), 11.0 )

if True:
    
    # Example of a multi-sample holder
    
    md = {
        'owner' : 'user' ,
        'series' : 'various' ,
        }

    hol1 = CapillaryHolder(base=stg)
    hol1.addGaragePosition(1,1)
    hol1.name = 'hol1'
    hol1.addSampleSlot( Sample('EC-PC-Na-1-dis-slow'), 1.0 )

    # que = Queue(base=stg)

    # que.addHolderIntoQueue(hol1, [1, 1], 1)   
    # que.addHolderIntoQueue(hol2, [1, 2], 2)   
    # # que.addHolderIntoQueue(hol3, [1, 3], 3) 
    # # # que.addHolderIntoQueue(hol4, [1, 2], 4)
    # # que.addHolderIntoQueue(hol1, [2, 1], 5)   
    # # que.addHolderIntoQueue(hol8, [2, 3], 6)   
    # # que.addHolderIntoQueue(hol9, [3, 1], 7)   
    # # que.addHolderIntoQueue(hol10, [3, 2], 8)   
    # # que.addHolderIntoQueue(hol11, [3, 3], 9)  
    # # que.addHolderIntoQueue(hol12, [4, 1], 10)  
    # # que.addHolderIntoQueue(hol13, [4, 2], 11)  
    # # que.addHolderIntoQueue(hol12, [4, 3], 12)  

    # que.setSequence()  
    # que.checkStatus(verbosity=5) 


# sam=Sample('test')
# detselect([fs4])
# sam.measure(1)

'''
2025_1

rod
In [132]: wbs()
bsx = -11.000014
bsy = 17.0005
bsphi = -181.50260699999998






#new beamstop setup at 2023C2

rod bs

In [69]: wbs()
bsx = -13.10041
bsy = 14.500015
bsphi = -178.00030500000003

round bs 

In [90]: wbs()
bsx = -16.700347
bsy = -0.1998869999999997
bsphi = -19.999025000000003


que.runHolders()


#cali.origin
In [89]: wsam()
smx = -16.2
smy = -2.0
sth = 0.0


In [425]: hol6.saveSampleStates()
Out[425]: 
{1: {'origin': {'x': 7.0, 'y': 0.04625000000000057, 'th': -0.137109375}},
 2: {'origin': {'x': 23.0, 'y': 0.050050000000000594, 'th': -0.148515625}},
 3: {'origin': {'x': 40.0, 'y': 0.08125000000000071, 'th': 0.080390625}},
 4: {'origin': {'x': 55.0, 'y': 0.0, 'th': 0.0}},
 5: {'origin': {'x': 72.0, 'y': 0.0, 'th': 0.0}},
 6: {'origin': {'x': 88.0, 'y': 0.0, 'th': 0.0}}}


 


cms.ventSample()
cms.pumpSample()

#Click the tiny green button once, then in the "800k" tab, click  ctrl+X twice to restart the WAXS detector

an alternative solution is : startWAXS()

ctrl+S to save the scripts first, then
"%run -i ..."  to reload the scripts
%
y
n
hol1
y


hol1.listSamples()   #check sample name has been updated
hol1.gotoOrigin()    #goto hol1 origin
hol1.yr(-4)          #lower the bar
hol1.setOrigin('y')  #reset the origin
hol2.setOrigin('y')
..

que.runHolders()


history




'''


'''
#change sample
#put tensile onto sample stage, push it down to the end and close chamber
cms.pumpChamber() # pump chamber
startWAXS() #start WAXS detector
sam=Sample('test')
#define the tensile protocol
sam.series_measure(num_frames=110, exposure_time=9.99, exposure_period=10)
cms.ventChamber()


#sample position for last sample on hol1
pass-320406 [534]: wsam()
smx = 23.150000000000002
smy = 7.1002
sth = 0.615390625


pass-320406 [54]: %wa fpr, fpn
/home/xf11bm/.cache/rattler/cache/envs/cms-profile-collection-15379365194774168494/envs/terminal/lib/python3.12/site-packages/bluesky/magics.py:38: UserWarning: BlueskyMagics.positioners is deprecated. Please use the newer labels feature.
  warnings.warn(
Positioner                     Value       Low Limit   High Limit  Offset     
fpn                            130.99998   0.0         140.0       32.3       
fpr                            120.00003   0.0         128.0       245.0      



pass-320406 [102]: wsam()
smx = -36.85
smy = 7.368650000000001
sth = 0.601328125

'''