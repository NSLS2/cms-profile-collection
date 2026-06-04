#!/usr/bin/python
# -*- coding: utf-8 -*-
# vi: ts=4 sw=4

#######
#v3 -->  v4:  coord based on KY_coord_form.py

# applied on sample : 16(7th) , 7(8th), 6(9th), 11(10th), 12(11th), 1(12th, LonC), 5(13th), 3(14th, LonC)

#######




################################################################################
#  Short-term settings (specific to a particular user/experiment) can
# be placed in this file. You may instead wish to make a copy of this file in
# the user's data directory, and use that as a working copy.
################################################################################



from ophyd import EpicsSignal
from bluesky.suspenders import SuspendFloor, SuspendCeil
from bluesky.preprocessors import stage_decorator
from epics import caput, caget


if True:
    # Define suspenders to hold data collection if x-ray
    # beam is not available.
    
    ring_current = EpicsSignal('SR:OPS-BI{DCCT:1}I:Real-I')
    sus = SuspendFloor(ring_current, 100, resume_thresh=400, sleep=600)
    RE.install_suspender(sus)

#    absorber_pos = EpicsSignal( 'XF:11BMB-ES{SM:1-Ax:ArmR}Mtr.RBV')
#    sus_abs_low = SuspendFloor(absorber_pos, -56, resume_thresh=-55)
#    sus_abs_hi = SuspendCeil(absorber_pos, -54, resume_thresh=-55)
#    RE.install_suspender(sus_abs_low)
#    RE.install_suspender(sus_abs_hi)

    #RE.clear_suspenders()

##2026Jan
# smx = EpicsMotor("XF:11BM-ES{DDSM100-Ax:X1}Mtr", name="smx")



# sprayy = EpicsMotor("XF:11BMB-ES{Chm:Smpl2-Ax:Y}Mtr", name="sprayy")


#cms.SAXS.setCalibration([758, 1079], 5.83, [-65, -73])  #20201021, 13.5 keV 1680 - 573
# cms.SAXS.setCalibration([754, 1082], 5.83, [-65, -73])

RE.md['experiment_alias_directory'] = 'robot_0'
RE.md["userpy_alias_directory"] = '/nsls2/data/cms/shared/config/bluesky/profile_collection/users/2026-2/beamline/Robot'
# cms.SAXS.setCalibration([742, 1081], 5.83, [-65, -73])  #2024 June 5m
cms.SAXS.setCalibration([742, 1081], 5.03, [-65, -73]) 


def smaxs_on():
    detselect([pilatus2M, pilatus8002])
    MAXSx.move(-60)    
    MAXSy.move(-135)   

def maxs_on():
    detselect([pilatus2M, pilatus8002])
    MAXSx.move(-60)    
    MAXSy.move(-135)   

def saxs_on():
    detselect([pilatus2M, pilatus8002])
    MAXSx.move(-60)    
    MAXSy.move(-105)   
  

def vacOn():
    pdu[6].on()

def vacOff():
    pdu[6].off()


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
    

INTENSITY_EXPECTED_050 = 18800.0
INTENSITY_EXPECTED_025 = INTENSITY_EXPECTED_050*0.5


def get_default_stage():
    return stg



class SampleTSAXS(SampleTSAXS_Generic):
    
    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        self.naming_scheme = ['name', 'extra', 'temperature', 'exposure_time']
        
        self.md['exposure_time'] = 30.0


class SampleGISAXS(SampleGISAXS_Generic):
    
    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']

 
# class Sample(SampleTSAXS):
class Sample(SampleGISAXS):

    def __init__(self, name, base=None, **md):
        super().__init__(name=name, base=base, **md)
        
        #self.naming_scheme = ['name', 'extra', 'clock', 'temperature', 'th', 'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'temperature', 'th', 'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'th', 'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'y', 'th', 'clock', 'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'opos', 'lpos', 'x', 'th',  'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'clock', 'localT', 'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'x', 'yy',  'exposure_time']
        #self.naming_scheme = ['name', 'extra', 'SamX', 'SamY',  'exposure_time']
        # self.naming_scheme = ['name', 'extra', 'x', 'yy', 'SamX', 'SamY', 'exposure_time']
        # self.naming_scheme = ['name', 'extra', 'x', 'yy', 'h1', 'h2', 'exposure_time']
        # self.naming_scheme = ['name', 'extra', 'Tc', 'clock', 'x', 'th', 'exposure_time']
        # self.naming_scheme = ['name', 'extra', 'id',  'clock', 'temperature', 'x', 'th', 'exposure_time']
        self.naming_scheme = ['name', 'extra', 'id',  'clock', 'temperature', 'x', 'th', 'exposure_time']
        self.name_o = self.name
        self.md['exposure_time'] = 5.0
        # self.incident_angles_default = [0.08, 0.10, 0.12, 0.15, 0.20]

    #       self.anneal_time = int(self.name.split('_')[-2].split('anneal')[-1])
        # self.anneal_time = int(self.name.split('anneal')[-1].split('_')[0])
        # self.preanneal_time = int(self.name.split('pre')[-1].split('_')[0])
            
        # self._positional_axis = ['x','y']

        self.smxPos = [121.5, 142.5, 162.5]

        #RT
        self._axes['x'].origin = 40.5
        self._axes['y'].origin = 15.21  #smy stage should be set with the limit [-5.5, -5]
        self._axes['th'].origin = 0.301

        #@150C
        # self._axes['x'].origin = 40.5
        self._axes['y'].origin = 15.61  #smy stage should be set with the limit [-5.5, -5]
        self._axes['th'].origin = 0.39-0.12


        # self._axes['x'].origin = 2000 #0.5 #2.4
        # self._axes['y'].origin = 20.2  #smy stage should be set with the limit [-5.5, -5]
        # self._axes['th'].origin = 0

   
    def _set_axes_definitions(self):
        '''Internal function which defines the axes for this stage. This is kept
        as a separate function so that it can be over-ridden easily.'''
        
        # The _axes_definitions array holds a list of dicts, each defining an axis
        super()._set_axes_definitions()

        self._axes_definitions.append ( #{'name': 'y',
                            # 'motor': smy2,
                            # 'enabled': True,
                            # 'scaling': +1.0,
                            # 'units': 'mm',
                            # 'hint': 'positive moves stage up',
                            # }, 
                            {'name': 'x',
                            'motor': smx,
                            'enabled': True,
                            'scaling': +1.0,
                            'units': 'mm',
                            'hint': 'positive moves stage up',
                            } )        

    def get_attribute(self, attribute):
        '''Return the value of the requested md.'''
        if attribute == 'Tc':  
            #return 'SamX{:.2f}'.format(-1*self.yypos(verbosity=0))     # Nov 2020
            return 'Tc{:.2f}'.format(pta.getTemperature(verbosity=0))      # Feb 2021
        else:
            return super().get_attribute(attribute)



    def get_md(self, prefix='sample_', include_marks=True, **md):
        '''Returns a dictionary of the current metadata.
        The 'prefix' argument is prepended to all the md keys, which allows the
        metadata to be grouped with other metadata in a clear way. (Especially,
        to make it explicit that this metadata came from the sample.)'''
        
        # Update internal md
        #self.md['key'] = value

        
        md_return = self.md.copy()
        md_return['name'] = self.name
    
    
        if include_marks:
            for label, positions in self._marks.items():
                md_return['mark_'+label] = positions
    
    
        # Add md that varies over time
        md_return['clock'] = self.clock()
    
        for axis_name, axis in self._axes.items():
            md_return[axis_name] = axis.get_position(verbosity=0)
            md_return['motor_'+axis_name] = axis.get_motor_position(verbosity=0)
        
        md_return['savename'] = self.get_savename() # This should be over-ridden by 'measure'

        # Include the user-specified metadata
        md_return.update(md)
    
        # Add an optional prefix
        if prefix is not None:
            md_return = { '{:s}{:s}'.format(prefix, key) : value for key, value in md_return.items() }
    
        return md_return

    def align(self, step=0, reflection_angle=0.12, verbosity=3):
        '''Align the sample with respect to the beam. GISAXS alignment involves
        vertical translation to the beam center, and rocking theta to get the
        sample plane parralel to the beam. Finally, the angle is re-optimized
        in reflection mode.
        
        The 'step' argument can optionally be given to jump to a particular
        step in the sequence.'''
        
        cms.modeAlignment()

        start_time = time.time()
        alignment = 'Success'
        initial_y = smy.position
        initial_th = sth.position
        
        if step<=1:
            align_crazy = self.swing(reflection_angle=reflection_angle)
            crazy_y = smy.position
            crazy_th = sth.position
        else:
            align_crazy = False, 0        
        
        if  align_crazy[0] == False:
            alignment = 'Failed'
            if step<=4:
                if verbosity>=4:
                    print('    align: fitting')
                
                fit_scan(smy, 1.0, 21, fit='HMi')
                ##time.sleep(2)
                fit_scan(sth, 1.5, 21, fit='max')
                    #time.sleep(2)            
                    
            if step<=8:
                #fit_scan(smy, 0.3, 21, fit='sigmoid_r')
                
                fit_edge(smy, 0.6, 21)
                #time.sleep(2)
                #fit_edge(smy, 0.4, 21)
                fit_scan(sth, 0.8, 21, fit='COM')
                #time.sleep(2)            
                self.setOrigin(['y', 'th'])
        
        
            if step<=9 and reflection_angle is not None:
                self.thabs(0)
                fit_edge(smy, 0.3, 13)
                self.setOrigin(['y'])      

                # Final alignment using reflected beam
                if verbosity>=4:
                    print('    align: reflected beam')
                get_beamline().setReflectedBeamROI(total_angle=reflection_angle*2.0)
                #get_beamline().setReflectedBeamROI(total_angle=reflection_angle*2.0, size=[12,2])
                
                self.thabs(reflection_angle)
                
                result = fit_scan(sth, 0.3, 41, fit='max') 
                #result = fit_scan(sth, 0.2, 81, fit='max') #it's useful for alignment of SmarAct stage
                sth_target = result.values['x_max']-reflection_angle
                
                if result.values['y_max']>5:
                    th_target = self._axes['th'].motor_to_cur(sth_target)
                    self.thsetOrigin(th_target)

                fit_scan(smy, 0.15, 11, fit='max')
                self.setOrigin(['y'])            

            if step<=10:
                self.thabs(0.0)
                beam.off()

        ### save the alignment information
        align_time = time.time() - start_time


        cms.modeMeasurement()
        self.name = 'test'
        self.thabs(0.1)
        self.measure(1)

    def swing(self, step=0, reflection_angle=0.12, ROI_size=[10, 180], th_range=0.3, int_threshold=10, verbosity=3):

        #setting parameters
        rel_th = 1
        ct = 0
        cycle = 0
        intenisty_threshold = 10

        #re-assure the 3 ROI positon
        get_beamline().setDirectBeamROI()
        get_beamline().setReflectedBeamROI(total_angle=reflection_angle*2)

        #set ROI2 as a fixed area
        get_beamline().setROI2ReflectBeamROI(total_angle=reflection_angle*2, size=ROI_size)
        pilatus2M.roi2.size.y.set(190)
        pilatus2M.roi2.min_xyz.min_y.set(852)


        #def ROI3 in 160pixels with the center located at reflection beam
        # get_beamline().setReflectedBeamROI(total_angle = reflection_angle*2, size=ROI_size) #set ROI3

        # self.thabs(reflection_angle)
        if verbosity>=4:
            print('  Aligning {}'.format(self.name))
        
        # if step<=0:
        #     # Prepare for alignment
            
        #     if RE.state!='idle':
        #         RE.abort()
                
        #     if get_beamline().current_mode!='alignment':
        #         #if verbosity>=2:
        #             #print("WARNING: Beamline is not in alignment mode (mode is '{}')".format(get_beamline().current_mode))
        #         print("Switching to alignment mode (current mode is '{}')".format(get_beamline().current_mode))
        #         get_beamline().modeAlignment()
                
                
            get_beamline().setDirectBeamROI()
            
            beam.on()

        
        if step<=2:
            # if verbosity>=4:
            #     print('    align: searching')
                
            # Estimate full-beam intensity
            value = None
            if True:
                # You can eliminate this, in which case RE.md['beam_intensity_expected'] is used by default
                self.yr(-.5)
                #detector = gs.DETS[0]
                detector = get_beamline().detector[0]
                # value_name = get_beamline().TABLE_COLS[0]
                beam.on()
                RE(count([detector]))
                value = detector.read()['pilatus2m-1_stats4_total']['value']
                self.yr(.5)
            
            # if 'beam_intensity_expected' in RE.md:
            #     if value<RE.md['beam_intensity_expected']*0.75:
            #         print('WARNING: Direct beam intensity ({}) lower than it should be ({})'.format(value, RE.md['beam_intensity_expected']))
                
            #check the last value:
            # value=20000
            ii = 0
            while abs(pilatus2M.stats4.total.get() - value)/value < 0.1 and ii < 3: 
                ii += 1
                # Find the step-edge
                RE(self.search_plan(motor=smy, step_size=.1, min_step=0.01, target=0.5, intensity=value, polarity=-1,detector_suffix='_stats4_total'))                
                # Find the peak
                # self.thsearch(step_size=0.2, min_step=0.01, target='max', verbosity=verbosity)
                RE(self.search_plan(motor=sth, step_size=.2, min_step=0.01, target='max',detector_suffix='_stats4_total'))
            #last check for height
            # self.ysearch(step_size=0.05, min_step=0.005, intensity=value, target=0.5, verbosity=verbosity, polarity=-1)
            RE(self.search_plan(motor=smy, step_size=0.05, min_step=0.005, target=0.5, intensity=value, polarity=-1,detector_suffix='_stats4_total'))
                   
        #check reflection beam
        self.thr(reflection_angle)
        RE(count([detector]))
        
        if abs(detector.stats2.max_xy.get().y - detector.stats2.centroid.get().y) < 20 and detector.stats2.max_value.get() > intenisty_threshold:

            #continue the fast alignment 
            print('The reflective beam is found! Continue the fast alignment')
            
            while abs(rel_th) > 0.005 and ct < 5:
            # while detector.roi3.max_value.get() > 50 and ct < 5:
                
                #absolute beam position 
                refl_beam = detector.roi2.min_xyz.min_y.get() + detector.stats2.max_xy.y.get()

                #roi3 position
                roi3_beam = detector.roi3.min_xyz.min_y.get() + detector.roi3.size.y.get()/2

                #distance from current postion to the center of roi2 (the disired rel beam position)
                # rel_ypos = detector.stats2.max_xy.get().y - detector.stats2.size.get().y
                rel_ypos = refl_beam - roi3_beam

                rel_th = rel_ypos/get_beamline().SAXS.distance/1000*0.172/np.pi*180/2
                
                print('The th offset is {}'.format(rel_th))
                self.thr(rel_th)
                
                ct += 1
                RE(count([detector]))

            if detector.stats3.total.get()>50:

                print('The fast alignment works!')
                self.thr(-reflection_angle)

    
                self.setOrigin(['y', 'th'])

                beam.off()

                return True, ii

            else:
                print('Alignment Error: Cannot Locate the reflection beam')
                self.thr(-reflection_angle)
                beam.off()

                return False, ii


        elif abs(detector.stats2.max_xy.get().y - detector.stats2.centroid.get().y) > 5:
            print('Max and Centroid dont Match!')

            #perform the full alignment
            print('Alignment Error: No reflection beam is found!')
            self.thr(-reflection_angle)
            beam.off()
            return False, ii

        else:
            print('Intensiy < threshold!')

            #perform the full alignment
            print('Alignment Error: No reflection beam is found!')
            self.thr(-reflection_angle)
            beam.off()
            return False, ii


    def swing_short(self, step=0, reflection_angle=0.12, ROI_size=[10, 180], th_range=0.3, int_threshold=10, verbosity=3):

        #setting parameters
        rel_th = 1
        ct = 0
        cycle = 0
        intenisty_threshold = 10

        #re-assure the 3 ROI positon
        get_beamline().setDirectBeamROI()
        get_beamline().setReflectedBeamROI(total_angle=reflection_angle*2)

        #set ROI2 as a fixed area
        get_beamline().setROI2ReflectBeamROI(total_angle=reflection_angle*2, size=ROI_size)
        pilatus2M.roi2.size.y.set(190)
        pilatus2M.roi2.min_xyz.min_y.set(852)

        self.tho()
        cms.modeAlignment()
        #def ROI3 in 160pixels with the center located at reflection beam
        # get_beamline().setReflectedBeamROI(total_angle = reflection_angle*2, size=ROI_size) #set ROI3

        # self.thabs(reflection_angle)
        if verbosity>=4:
            print('  Aligning {}'.format(self.name))
        
        # if step<=0:
        #     # Prepare for alignment
            
        #     if RE.state!='idle':
        #         RE.abort()
                
        #     if get_beamline().current_mode!='alignment':
        #         #if verbosity>=2:
        #             #print("WARNING: Beamline is not in alignment mode (mode is '{}')".format(get_beamline().current_mode))
        #         print("Switching to alignment mode (current mode is '{}')".format(get_beamline().current_mode))
        #         get_beamline().modeAlignment()
                
            
        get_beamline().setDirectBeamROI()
        
        beam.on()

        
        # if step<=2:
        #     # if verbosity>=4:
        #     #     print('    align: searching')
                
        #     # Estimate full-beam intensity
        #     value = None
        #     if True:
        #         # You can eliminate this, in which case RE.md['beam_intensity_expected'] is used by default
        #         self.yr(-.5)
        #         #detector = gs.DETS[0]
        #         detector = get_beamline().detector[0]
        #         # value_name = get_beamline().TABLE_COLS[0]
        #         beam.on()
        #         RE(count([detector]))
        #         value = detector.read()['pilatus2M_stats4_total']['value']
        #         self.yr(.5)
            
        #     # if 'beam_intensity_expected' in RE.md:
        #     #     if value<RE.md['beam_intensity_expected']*0.75:
        #     #         print('WARNING: Direct beam intensity ({}) lower than it should be ({})'.format(value, RE.md['beam_intensity_expected']))
                
        #     #check the last value:
        #     # value=20000
        #     ii = 0
        #     while abs(pilatus2M.stats4.total.get() - value)/value < 0.1 and ii < 3: 
        #         ii += 1
        #         # Find the step-edge
        #         RE(self.search_plan(motor=smy, step_size=.1, min_step=0.01, target=0.5, intensity=20000, polarity=-1,detector_suffix='_stats4_total'))                
        #         # Find the peak
        #         # self.thsearch(step_size=0.2, min_step=0.01, target='max', verbosity=verbosity)
        #         RE(self.search_plan(motor=sth, step_size=.2, min_step=0.01, target='max',detector_suffix='_stats4_total'))
        #     #last check for height
        #     # self.ysearch(step_size=0.05, min_step=0.005, intensity=value, target=0.5, verbosity=verbosity, polarity=-1)
        #     RE(self.search_plan(motor=smy, step_size=0.05, min_step=0.005, target=0.5, intensity=20000, polarity=-1,detector_suffix='_stats4_total'))
                   
        #check reflection beam
        detector= pilatus2M
        self.thr(reflection_angle)
        RE(count([pilatus2M]))
        
        if abs(detector.stats2.max_xy.get().y - detector.stats2.centroid.get().y) < 20 and detector.stats2.max_value.get() > intenisty_threshold:

            #continue the fast alignment 
            print('The reflective beam is found! Continue the fast alignment')
            
            while abs(rel_th) > 0.005 and ct < 5:
            # while detector.roi3.max_value.get() > 50 and ct < 5:
                
                #absolute beam position 
                refl_beam = detector.roi2.min_xyz.min_y.get() + detector.stats2.max_xy.y.get()

                #roi3 position
                roi3_beam = detector.roi3.min_xyz.min_y.get() + detector.roi3.size.y.get()/2

                #distance from current postion to the center of roi2 (the disired rel beam position)
                # rel_ypos = detector.stats2.max_xy.get().y - detector.stats2.size.get().y
                rel_ypos = refl_beam - roi3_beam

                rel_th = rel_ypos/get_beamline().SAXS.distance/1000*0.172/np.pi*180/2
                
                print('The th offset is {}'.format(rel_th))
                self.thr(rel_th)
                
                ct += 1
                RE(count([detector]))

            if detector.stats3.total.get()>50:

                print('The fast alignment works!')
                self.thr(-reflection_angle)

    
                self.setOrigin(['y', 'th'])

                beam.off()

                return True, ii

            else:
                print('Alignment Error: Cannot Locate the reflection beam')
                self.thr(-reflection_angle)
                beam.off()

                return False, ii


        elif abs(detector.stats2.max_xy.get().y - detector.stats2.centroid.get().y) > 5:
            print('Max and Centroid dont Match!')

            #perform the full alignment
            print('Alignment Error: No reflection beam is found!')
            self.thr(-reflection_angle)
            beam.off()
            return False, ii

        else:
            print('Intensiy < threshold!')

            #perform the full alignment
            print('Alignment Error: No reflection beam is found!')
            self.thr(-reflection_angle)
            beam.off()
            return False, ii

    def search_plan(self, motor=smy, step_size=1.0, min_step=0.05, intensity=None, target=0.5, detector=None, detector_suffix=None, polarity=+1, verbosity=3):
        '''Moves this axis, searching for a target value.
        
        Parameters
        ----------
        step_size : float
            The initial step size when moving the axis
        min_step : float
            The final (minimum) step size to try
        intensity : float
            The expected full-beam intensity readout
        target : 0.0 to 1.0
            The target ratio of full-beam intensity; 0.5 searches for half-max.
            The target can also be 'max' to find a local maximum.
        detector, detector_suffix
            The beamline detector (and suffix, such as '_stats4_total') to trigger to measure intensity
        polarity : +1 or -1
            Positive motion assumes, e.g. a step-height 'up' (as the axis goes more positive)
        '''
        print("HERE!!")
        
        if detector is None:
            #detector = gs.DETS[0]
            detector = get_beamline().detector[0]
        if detector_suffix is None:
            #value_name = gs.TABLE_COLS[0]
            value_name = get_beamline().TABLE_COLS[0]
        else:
            value_name = detector.name + detector_suffix

        print(f"detector={detector}")

        @bpp.stage_decorator([detector])
        @bpp.run_decorator(md={})
        def inner_search():
            nonlocal intensity, target, step_size

            if not get_beamline().beam.is_on():
                print('WARNING: Experimental shutter is not open.')
            
            
            if intensity is None:
                intensity = RE.md['beam_intensity_expected']

            # bec.disable_table()
            
            
            # Check current value
            vv = yield from bps.trigger_and_read([detector, motor])
            value = vv[value_name]['value']
            # RE(count([detector]))
            # value = detector.read()[value_name]['value']


            if target == 'max':
                
                if verbosity>=5:
                    print("Performing search on axis '{}' target is 'max'".format(self.name))
                
                max_value = value
                # max_position = self.get_position(verbosity=0)
                
                
                direction = +1*polarity
                
                while step_size>=min_step:
                    if verbosity>=4:
                        print("        move {} by {} × {}".format(self.name, direction, step_size))

                    #  pos = yield from bps.rd(motor)
                    yield from bps.mvr(motor, direction*step_size)
                    # self.move_relative(move_amount=direction*step_size, verbosity=verbosity-2)

                    prev_value = value
                    yield from bps.trigger_and_read([detector, motor])
                    # RE(count([detector]))
                    
                    value = detector.read()[value_name]['value']
                    # if verbosity>=3:
                    #     print("      {} = {:.3f} {}; value : {}".format(self.name, self.get_position(verbosity=0), self.units, value))
                        
                    if value>max_value:
                        max_value = value
                        # max_position = self.get_position(verbosity=0)
                        
                    if value>prev_value:
                        # Keep going in this direction...
                        pass
                    else:
                        # Switch directions!
                        direction *= -1
                        step_size *= 0.5
                    
                    
            elif target == 'min':
                
                if verbosity>=5:
                    print("Performing search on axis '{}' target is 'min'".format(self.name))
                
                direction = +1*polarity
                
                while step_size>=min_step:
                    if verbosity>=4:
                        print("        move {} by {} × {}".format(self.name, direction, step_size))

                    # pos = yield from bps.rd(motor)
                    yield from bps.mvr(motor, direction*step_size)
                    # self.move_relative(move_amount=direction*step_size, verbosity=verbosity-2)

                    prev_value = value
                    yield from bps.trigger_and_read([detector, motor])
                    # RE(count([detector]))
                    value = detector.read()[value_name]['value']
                    if verbosity>=3:
                        print("      {} = {:.3f} {}; value : {}".format(self.name, self.get_position(verbosity=0), self.units, value))
                        
                    if value<prev_value:
                        # Keep going in this direction...
                        pass
                    else:
                        # Switch directions!
                        direction *= -1
                        step_size *= 0.5
                                    
            else:

                target_rel = target
                target = target_rel*intensity

                if verbosity>=5:
                    print("Performing search on axis '{}' target {} × {} = {}".format(self.name, target_rel, intensity, target))
                if verbosity>=4:
                    print("      value : {} ({:.1f}%)".format(value, 100.0*value/intensity))
                
                
                # Determine initial motion direction
                if value>target:
                    direction = -1*polarity
                else:
                    direction = +1*polarity
                    
                while step_size>=min_step:
                    
                    if verbosity>=4:
                        print("        move {} by {} × {}".format(self.name, direction, step_size))
                    
                    # pos = yield from bps.rd(motor)
                    yield from bps.mvr(motor, direction*step_size)
                    # self.move_relative(move_amount=direction*step_size, verbosity=verbosity-2)
                    
                    yield from bps.trigger_and_read([detector, motor])
                    # RE(count([detector]))
                    value = detector.read()[value_name]['value']
                    #if verbosity>=3:
                    #    print("      {} = {:.3f} {}; value : {} ({:.1f}%)".format(self.name, self.get_position(verbosity=0), self.units, value, 100.0*value/intensity))
                        
                    # Determine direction
                    if value>target:
                        new_direction = -1.0*polarity
                    else:
                        new_direction = +1.0*polarity
                        
                    if abs(direction-new_direction)<1e-4:
                        # Same direction as we've been going...
                        # ...keep moving this way
                        pass
                    else:
                        # Switch directions!
                        direction *= -1
                        step_size *= 0.5
        
            # bec.enable_table()

        yield from inner_search()

    def runSpray(self, num_frames, exposure_time=None, exposure_period=None, detectors=None, extra=None, wait_time=None, verbosity=3, **md):
        """
        Continueous shots with internal trigger of detectors .
        
        Parameters
        ----------
        speeds: list
            The list of spinner speeds in multiple steps.
            speeds = [500, 2000, 500]
        periods: list
            The lasting time for corresponding spinner speed. 
            periods = [5, 60, 20]
        num_frames : int
            The number of data points. 
        exposure_time: float
            The exposure time for single point
        exposure_period: float
            The exposure period for single point. should be at least 0.05s longer than exposure_time
        md : dict, optional
            metadata        
        """

        # print(speeds)

        # speeds = tuple(speeds)
        # times = tuple(times)
        # print(type(speeds))
        if exposure_period < exposure_time+0.005:
            return print('Error: exposure period should be at least 0.005s more than exposure time.')

        if detectors==None:
            detectors = cms.detector

        if exposure_time is not None:
            self.set_attribute('exposure_time', exposure_time)
            
        # Set exposure time
        for detector in get_beamline().detector:
            yield from detector.setExposureTime(exposure_time)
            yield from detector.setExposurePeriod(exposure_period)
            yield from detector.setExposureNumber(num_frames)
                
        #bec.disable_plots()
        #bec.disable_table()
        
        savename = self.get_savename(savename_extra=extra)
        
        #caput('XF:11BMB-ES{Det:SAXS}:cam1:FileName', savename)
        
        if verbosity>=2 and (get_beamline().current_mode != 'measurement'):
            print("WARNING: Beamline is not in measurement mode (mode is '{}')".format(get_beamline().current_mode))

        if verbosity>=1 and len(cms.detector)<1:
            print("ERROR: No detectors defined in cms.detector")
            return
        
        md_current = self.get_md()
        md_current['sample_savename'] = savename
        md_current['series'] = 'series_measure'
        md_current.update(self.get_measurement_md())
        #md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, md_current['detector_sequence_ID'])
        md_current['measure_series_num_frames'] = num_frames
        md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current['exposure_time'] = exposure_time
        #md_current['measure_series_motor'] = motor.name
        #md_current['measure_series_positions'] = [start, stop]

        #md_current['fileno'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current.update(md)
        
        # turn on shutter
        yield from shutter_on()

        # Perform the scan
        @bpp.stage_decorator(detectors)

        def inner(**md):

            for detector in detectors:
                status = yield from bps.trigger(detector, group='det')

            # status = yield from bps.trigger(pilatus2M, group='det')

            # for index, period in enumerate(periods):

                # print('Step {} : speed = {}V for {}seconds'.format(index, speeds[index], period))
            print('Trigger ON')
            if wait_time != None:
                yield from bps.sleep(wait_time)
            yield from bps.mv(TTL2, 1) #TLL on

            yield from bps.wait(group='det')
            yield from bps.create(name="primary")
            for detector in detectors:
                yield from bps.read(detector)
            yield from bps.save()

            #total_time = num_frames*exposure_period
            #moving_interval = 1
            # for index in range(int(total_time/moving_interval)):
                # yield from bps.mov(smx, smx.position+0.1*index)
                # yeild from sleep(1)


        yield from bpp.run_wrapper(
            inner(md={'spray': 'TTL2'}
            ))

        #get_beamline().beam._test_off(wait_time=0.1)
        yield from bps.mv(TTL2, 0) #TLL off
        yield from shutter_off()

        self.md['measurement_ID'] += 1
   
        #data collected, link uid to file name
        for detector in cms.detector:
            self.handle_fileseries(detector, num_frames=num_frames, extra=extra, verbosity=verbosity, **md)

        #reset the num_frame back to 1
        for detector in get_beamline().detector:
            yield from detector.setExposureNumber(1)

    def runSpray_Ext(self, num_frames, exposure_time=None, exposure_period=None, detectors=None, trigger_mode='ExtTrigger', extra=None, wait_time=None, verbosity=3, **md):
        """
        Continueous shots with internal trigger of detectors .
        
        Parameters
        ----------
        speeds: list
            The list of spinner speeds in multiple steps.
            speeds = [500, 2000, 500]
        periods: list
            The lasting time for corresponding spinner speed. 
            periods = [5, 60, 20]
        num_frames : int
            The number of data points. 
        exposure_time: float
            The exposure time for single point
        exposure_period: float
            The exposure period for single point. should be at least 0.05s longer than exposure_time
        md : dict, optional
            metadata        
        """

        # print(speeds)

        # speeds = tuple(speeds)
        # times = tuple(times)
        # print(type(speeds))
        if exposure_period < exposure_time+0.005:
            return print('Error: exposure period should be at least 0.005s more than exposure time.')

        if detectors==None:
            detectors = cms.detector

        if exposure_time is not None:
            self.set_attribute('exposure_time', exposure_time)
            
        # Set exposure time
        for detector in get_beamline().detector:
            yield from detector.setExposureTime(exposure_time)
            yield from detector.setExposurePeriod(exposure_period)
            yield from detector.setExposureNumber(num_frames)
                
        #bec.disable_plots()
        #bec.disable_table()
        if trigger_mode=='ExtTrigger':
            detector.cam.trigger_mode.put(2)
        if trigger_mode=='ExtMultiple':
            detector.cam.trigger_mode.put(3)
        if trigger_mode=='Internal':
            detector.cam.trigger_mode.put(0)

        yield from bps.sleep(2)        

        savename = self.get_savename(savename_extra=extra)
        
        #caput('XF:11BMB-ES{Det:SAXS}:cam1:FileName', savename)
        
        if verbosity>=2 and (get_beamline().current_mode != 'measurement'):
            print("WARNING: Beamline is not in measurement mode (mode is '{}')".format(get_beamline().current_mode))

        if verbosity>=1 and len(cms.detector)<1:
            print("ERROR: No detectors defined in cms.detector")
            return
        
        md_current = self.get_md()
        md_current['sample_savename'] = savename
        md_current['series'] = 'series_measure'
        md_current.update(self.get_measurement_md())
        #md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, md_current['detector_sequence_ID'])
        md_current['measure_series_num_frames'] = num_frames
        md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current['exposure_time'] = exposure_time
        #md_current['measure_series_motor'] = motor.name
        #md_current['measure_series_positions'] = [start, stop]

        #md_current['fileno'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current.update(md)
        
        # turn on shutter
        yield from shutter_on()

        # Perform the scan
        @bpp.stage_decorator(detectors)

        def inner(**md):

            for detector in detectors:
                status = yield from bps.trigger(detector, group='det')

            # status = yield from bps.trigger(pilatus2M, group='det')

            # for index, period in enumerate(periods):

                # print('Step {} : speed = {}V for {}seconds'.format(index, speeds[index], period))
            print('Trigger ON')
            if wait_time != None:
                yield from bps.sleep(wait_time)
                
            yield from bps.mv(TTL2, 1) #TLL on

            yield from bps.wait(group='det')
            yield from bps.create(name="primary")
            for detector in detectors:
                yield from bps.read(detector)
            yield from bps.save()

            #total_time = num_frames*exposure_period
            #moving_interval = 1
            # for index in range(int(total_time/moving_interval)):
            #     yield from bps.mov(smx, smx.position+0.1*index)
            #     yield from sleep(1)


        yield from bpp.run_wrapper(
            inner(md={'spray': 'TTL2'}
            ))

        #get_beamline().beam._test_off(wait_time=0.1)
        yield from bps.mv(TTL2, 0) #TLL off
        yield from shutter_off()

        self.md['measurement_ID'] += 1

        detector.cam.trigger_mode.put(0)   
        #data collected, link uid to file name
        for detector in cms.detector:
            self.handle_fileseries(detector, num_frames=num_frames, extra=extra, verbosity=verbosity, **md)

        #reset the num_frame back to 1
        for detector in get_beamline().detector:
            yield from detector.setExposureNumber(1)


    def measure_exttrigger(self, num_frames, exposure_time=None, exposure_period=None, detectors=None, extra=None, per_step=None, wait_time=None, measure_type='Series_measure', verbosity=3, trigger_mode='ExtTrigger', **md):
    # def series_measure(self, num_frames, exposure_time=None, exposure_period=None, detectors=None, extra=None, per_step=None, wait_time=None, measure_type='Series_measure', verbosity=3, fill_gaps=False, **md):
        
        """
        Continueous shots with internal trigger of detectors. (burst mode)
        
        Parameters
        ----------
        num_frames : int
            The number of data points. 
        exposure_time: float
            The exposure time for single point
        exposure_period: float
            The exposure period for single point. should be at least 0.05s longer than exposure_time
        md : dict, optional
            metadata        
        """

        if detectors is None:
            detectors = cms.detector
   
        if exposure_time is not None:
            self.set_attribute('exposure_time', exposure_time)
            
        # Set exposure time
        for detector in get_beamline().detector:
            if exposure_time != detector.cam.acquire_time.get():
                RE(detector.setExposureTime(exposure_time))
                # detector.cam.acquire_time.put(exposure_time)
            # detector.cam.acquire_period.put(exposure_period)
            # detector.cam.num_images.put(num_frames)
            RE(detector.setExposurePeriod(exposure_period))
            RE(detector.setExposureNumber(num_frames))
            if trigger_mode=='ExtTrigger':
                detector.cam.trigger_mode.put(2)
            if trigger_mode=='ExtMultiple':
                detector.cam.trigger_mode.put(3)
            if trigger_mode=='Internal':
                detector.cam.trigger_mode.put(0)
            time.sleep(2)
        
        savename = self.get_savename(savename_extra=extra)
        if verbosity>=2 and (get_beamline().current_mode != 'measurement'):
            print("WARNING: Beamline is not in measurement mode (mode is '{}')".format(get_beamline().current_mode))

        if verbosity>=1 and len(get_beamline().detector)<1:
            print("ERROR: No detectors defined in cms.detector")
            return
        
        md_current = self.get_md()
        md_current['sample_savename'] = savename
        md_current['measure_type'] = measure_type
        md_current['series'] = 'series_measure'
        md_current.update(self.get_measurement_md())
        #md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, md_current['detector_sequence_ID'])
        md_current['measure_series_num_frames'] = num_frames
        md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current['exposure_time'] = exposure_time
        #md_current['measure_series_motor'] = motor.name
        #md_current['measure_series_positions'] = [start, stop]

        #md_current['fileno'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current.update(md)
        
        print(RE.md['scan_id'])
        # Perform the scan
        #get_beamline().beam._test_on(wait_time=0.1)
        get_beamline().beam.on()

        RE(count(get_beamline().detector, md=md_current))
        get_beamline().beam.off()

        self.md['measurement_ID'] += 1
        #reset the num_frame back to 1
        for detector in get_beamline().detector:
            RE(detector.setExposureNumber(1))
            detector.cam.trigger_mode.put(0)

        #data collected, link uid to file name
        for detector in cms.detector:
            print('handling the file names')
            self.handle_fileseries(detector, num_frames=num_frames, extra=extra, verbosity=verbosity, **md)


    def initialDetector(self):
        for detector in get_beamline().detector:
            yield from detector.setExposureNumber(1)


    def measureSpotsGD(self, exposure_time=5, xstep=-0.1*50, Np=10, Nmax = 1000, incident_angles=[0.1], wait_time=10):
        cms.modeMeasurement()
        smaxs_on()
        for ii in np.arange(0, Nmax):
            print('\n==== Number {} ====\n'.format(ii))
            #self.thabs(incident_angles)
            #self.measure(exposure_time=exposure_time)
            self.measureIncidentAngles(angles=incident_angles, exposure_time=exposure_time)
            if ii > 0 and np.mod(ii, Np)==0:
                self.xr(xstep)
            time.sleep(wait_time)

    def measure_final(self, exposure_time=5, incident_angles=[0.1, 0.15]):
        self.measureIncidentAngles(angles=incident_angles, extra='final', exposure_time=exposure_time)
        self.xr(100)
        self.measureIncidentAngles(angles=incident_angles, extra='final', exposure_time=exposure_time)
        self.xr(-100)
 

    def prepareRobot(self, incident_angle=0.5, ):
        '''A measurement plan for GISAXS measurement with given incident angle.
        
        Parameters
        ----------
        incident_angle : float
            The incident angle in degree.
        '''
        cms.modeMeasurement()
        smaxs_on()
        self.thabs(incident_angle)
        # self.measure(exposure_time=5, extra='GISAXS_{}deg'.format(incident_angle))
        # self.series_measure(num_frames=120, exposure_time=0.99, exposure_period=1.0)


    def measureRobot(self, series_measure=True, reset_clock=True, exposure_time=0.095,exposure_period=0.1,  num_frames=600, maxTime=600, interval=10):
        '''A measurement plan for GISAXS measurement with given incident angle.
        
        Parameters
        ----------
        incident_angle : float
            The incident angle in degree.
        '''
        # cms.modeMeasurement()
        # smaxs_on()
        # self.thabs(incident_angle)
        # self.measure(exposure_time=5, extra='GISAXS_{}deg'.format(incident_angle))
        if reset_clock==True:
            self.reset_clock() 
        if series_measure==True:
            self.series_measure(num_frames=num_frames, exposure_time=exposure_time, exposure_period=exposure_period)

        start_time = self.clock()
        
        for _clock in np.arange(start_time, maxTime, interval):

            if self.clock() > maxTime:
                print(f"Maximum time of {maxTime} seconds exceeded. Stopping measurement.")
                break
            
            while self.clock()<_clock:
                time.sleep(0.2)
            self.measure(exposure_time=1)        

    def startSpin(self, vol=3):
        ioL.set(AO2[1], vol)

    def runSpinner(self, vol=0.75, wait_time=60):
        ioL.set(AO2[1], vol)
        time.sleep(wait_time)
        ioL.set(AO2[1], 0)
        

    def countdown(seconds):
        end = time.time() + seconds

        while True:
            remaining = end - time.time()
            if remaining <= 0:
                print("0")
                break
            print(int(remaining))
            time.sleep(min(1, remaining))


    def setSpeed(self, voltage): 
        '''
            set the spinning speed, defined by voltage

            # voltage(V)  ---   speed(RPM)
            #    2V               5270 
            #    3V               3315 
            #    4V               1520 
            #    1V               7200
            #    0V               9150

            #    2.63V            4000 
            #    3.2V             3000
            #    3.71V            2000
            #    4V               1500
            #    4.25V            1000
            #    >4.5V             700
            #    >5V              stop

            #new circut board
            voltage(V)  ---   speed(RPM)

               0.49V            1000 
               1.01V            2000
               1.51V            3000
               2.01V            4000
               2.52V            5000
               3.02V            6000
               3.53V            7000               
                       
                               
                                               '''
        self.voltage = voltage


    def spincoating(self, speeds, periods): 

        self.setDryFlow(5)
        for speed, period in zip(speeds, periods):
            self.setVoltage(speed)
            time.sleep(period)
        self.setVoltage(0)        
        self.setDryFlow(5)

    def setVoltage(self, voltage):
        ioL.set(AO2[1], voltage)

    def spinOn(self):
        self.setVoltage(self.voltage)

    def spinOff(self):
        self.setVoltage(0)


    # RE(sam.runSpinner_s(speeds=[0.45, 2.38], periods=[10, 110], num_frames=1200, exposure_time=0.095, exposure_period=0.1, extra='spin', injection=True, wait_time=13))  
    # do injection
    def runSpinner_duo(self, speeds=[0.76], periods=[100], num_frames=60, injection=False, 
                       exposure_time=0.495, exposure_period=0.5, detectors=[pilatus8002], extra=None, 
                       speed_signal=AO2[1].signal, wait_time=5,  verbosity=3, **md):
        """

       RE( sam.runSpinner_duo( speeds=[0.49, 2.52 ], periods=[10, 120  ], num_frames=500, injection=True, 
                       exposure_time=.3 - 0.006, exposure_period=.3, detectors=[pilatus8002], extra=None, 
                       speed_signal=AO2[1].signal, wait_time=15  ) )


       RE( sam.runSpinner_duo( speeds=[ 2.52 ], periods=[  120  ], num_frames=800, injection=True, 
                       exposure_time=.15 - 0.005, exposure_period=.15, detectors=[pilatus8002], extra=None, 
                       speed_signal=AO2[1].signal, wait_time=3  ) )




        Continueous shots with internal trigger of detectors .
        
        Parameters
        ----------
        speeds: list
            The list of spinner speeds in multiple steps.
            speeds = [500, 2000, 500]
        periods: list
            The lasting time for corresponding spinner speed. 
            periods = [5, 60, 20]
        num_frames : int
            The number of data points. 
        exposure_time: float
            The exposure time for single point
        exposure_period: float
            The exposure period for single point. should be at least 0.05s longer than exposure_time
        md : dict, optional
            metadata        
        """

        # RE( sam.runSpinner(  speeds=[ 4 ], periods=[ 1 ], num_frames= 100 , exposure_time= .3 - 0.006, exposure_period= .3  ))
        # RE( sam.runSpinner(  speeds=[ 4 ], periods=[ 1 ], injection=True,num_frames= 10 , exposure_time= .3 - 0.006, exposure_period= .3  ))
        

        # print(speeds)

        # speeds = tuple(speeds)
        # times = tuple(times)
        # print(type(speeds))
        print('0--start--')
        #detselect([pilatus2M, pilatus8002])
        #detselect([ pilatus8002 ])
        #maxs_on() # move the maxs detector in the beam
        #print ( '1 finish setup the det ')

        if len(speeds) != len(periods):
            return print('Error: the steps of period needs to match to speeds.')
        if exposure_period < exposure_time+0.005:
            return print('Error: exposure period should be at least 0.005s more than exposure time.')
        # if detectors==None:
        #     detectors = cms.detector

        if exposure_time is not None:
            self.set_attribute('exposure_time', exposure_time)
            
        # Set exposure time
        for detector in detectors: #get_beamline().detector:
            yield from detector.setExposureTime(exposure_time)
            yield from detector.setExposurePeriod(exposure_period)
            yield from detector.setExposureNumber(num_frames)
                
        #bec.disable_plots()
        #bec.disable_table()
        print ( '1 finish setup the det ')
        savename = self.get_savename(savename_extra=extra)

        #turn off the dry flow 

        # yield from bps.mv(AO[1].signal, 0)
        # print ( '2 Turn off the dry flow ')

        #injection:(((((((((((())))))))))))

        
        # yield from bps.time.sleep(wait_time)
        #time.sleep(wait_time)  #comment this out Jan 28, 2023, 


        if verbosity>=2 and (get_beamline().current_mode != 'measurement'):
            print("WARNING: Beamline is not in measurement mode (mode is '{}')".format(get_beamline().current_mode))

        if verbosity>=1 and len(cms.detector)<1:
            print("ERROR: No detectors defined in cms.detector")
            return
        
        md_current = self.get_md()
        md_current['sample_savename'] = savename
        md_current['series'] = 'series_measure'
        md_current.update(self.get_measurement_md())
        #md_current['filename'] = '{:s}_{:04d}.tiff'.format(savename, md_current['detector_sequence_ID'])
        md_current['measure_series_num_frames'] = num_frames
        md_current['speeds'] = speeds
        md_current['periods'] = periods
        md_current['triggerTime'] = wait_time
        md_current['filename'] = '{:s}_{:04d}'.format(savename, RE.md['scan_id'])
        md_current['exposure_time'] = exposure_time
        md_current['measure_type'] = 'measure'
        #md_current['measure_series_motor'] = motor.name
        #md_current['measure_series_positions'] = [start, stop]

        #md_current['fileno'] = '{:s}_{:04d}.tiff'.format(savename, RE.md['scan_id'])
        md_current.update(md)
        md = md_current
        
        print('4- step stage detector')
        print(md_current)
        # turn on shutter
        yield from shutter_on()

        # Perform the scan
        @bpp.stage_decorator(detectors)

        def inner(speeds, **md):
            ret = {}
            reading = []
            for detector in detectors:
                status = yield from bps.trigger(detector, group='det')

            # status = yield from bps.trigger(pilatus2M, group='det')
            yield from bps.create(name='primary')

            yield from bps.sleep(1)
            for index, period in enumerate(periods):

                print('Step {} : speed = {}V for {}seconds'.format(index, speeds[index], period))
                yield from bps.mv(speed_signal, speeds[index])

                if index == len(periods) - 1:
                    if injection==True:
                        #wait time is counted from the beginning of the spin
                        # wait_time = wait_time - clock# np.sum(periods[:-1])
                        print('Waiting for injection {}s'.format(wait_time))
                        yield from bps.sleep(wait_time)

                        print('Injecting~')
                        # #self.setInjecter(5)               
                        # yield from bps.mv(AO[3].signal, 5)        
                        # # yield from bps.time.sleep(0.1)
                        # time.sleep(0.1)
                        # #self.setInjecter(0) 
                        # yield from bps.mv(AO[3].signal, 0)
                        # # yield from bps.time.sleep(10) # determined by the volume/rate

                        yield from startSyringePumpInfuse() # NOTE: the infusion time depends on the vol/rate, needs to be smaller than period-wait_time
                        injection_time = 1.5
                        yield from bps.sleep(injection_time)
                        yield from startSyringePumpWithdraw()

                        print('Injection is done.')
                        yield from bps.sleep(period-wait_time-injection_time)
                    else:
                        yield from bps.sleep(period)

                else:
                    yield from bps.sleep(period)
                    
            yield from bps.wait(group='det')

            for detector in detectors:
                reading = (yield from bps.read(detector))
                ret.update(reading)
 
            yield from bps.save()

        yield from bpp.run_wrapper(
            #added by Juan 20251013
            inner(speeds),md={'detectors': [d.name for d in detectors], **md} #md=md#{'potentiostats': 'TTL2'}
            )


        yield from bps.mv(speed_signal, 0)
        #get_beamline().beam._test_off(wait_time=0.1)
        yield from shutter_off()

        self.md['measurement_ID'] += 1

        #turn on the dry flow 
        #yield from bps.mv(AO[1].signal, 5)

        #data collected, link uid to file name
        for detector in detectors:
            self.handle_fileseries(detector, num_frames=num_frames, extra=extra, verbosity=verbosity, **md)

        #reset the num_frame back to 1
        for detector in  detectors:
            yield from detector.setExposureNumber(1)



# %run -i /nsls2/data/cms/legacy/xf11bm/data/2024_3/GDoerk/user_spray.py
'''
sample origin position where beam is on the center of sample sealed by vacuum. 

pass-320406 [223]: wsam()
smx = 44.0
smy = 15.21
sth = 0.30093749999999986



'''