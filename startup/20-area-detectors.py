print(f'Loading {__file__}')

from ophyd import (
    ProsilicaDetector,
    SingleTrigger,
    TIFFPlugin,
    ImagePlugin,
    DetectorBase,
    HDF5Plugin,
    AreaDetector,
    EpicsSignal,
    EpicsSignalRO,
    ROIPlugin,
    TransformPlugin,
    ProcessPlugin,
    PilatusDetector,
    ProsilicaDetectorCam,
    PilatusDetectorCam,
    StatsPlugin,
)
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.base import ADComponent, EpicsSignalWithRBV
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd import Component as Cpt, Signal
from ophyd.utils import set_and_wait
from nslsii.ad33 import SingleTriggerV33, StatsPluginV33

from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin #,register_plugin,PluginBase

import time
import asyncio


# Generic Configuration Settings

Pilatus2M_on = True
# Pilatus2M_on = 'h5'  # 'h5' for h5 mode
Camera_on=True
Pilatus300_on = False

HDF5_on = False
# ONLY 1 Pilatus800 will be turned on at the same time. changed by RL, 20210831
#
print("The current stage is {}".format(beamline_stage))
# beamline_stage = 'default' #for using chamber
# beamline_stage = 'open_MAXS' #for using the upstream stage
if beamline_stage == "open_MAXS" or beamline_stage == "BigHuber":
    Pilatus800_on = False
    Pilatus800_2_on = True
elif beamline_stage == "default":
    Pilatus800_on = True
    Pilatus800_2_on = False
elif beamline_stage == "Temp":
    Pilatus800_on = False
    Pilatus800_2_on = False
    Pilatus300_on = True

# Pilatus800_on = True
# Pilatus800_2_on = True
# Pilatus800_2_on = False
# Pilatus2M_on = False

''' H5Plugin = HDF5Plugin  ''' 


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    def describe(self):
        ret = super().describe()
        key = self.parent._image_name
        color_mode = self.parent.cam.color_mode.get(as_string=True)
        if color_mode == 'Mono':
            ret[key]['shape'] = [
                self.parent.cam.num_images.get(),
                #self.array_size.depth.get(),
                self.array_size.height.get(),
                self.array_size.width.get()
                ]

        elif color_mode in ['RGB1', 'Bayer']:
            ret[key]['shape'] = [self.parent.cam.num_images.get(), *self.array_size.get()]
        else:
            raise RuntimeError("Color mode not supported")

        cam_dtype = self.parent.cam.data_type.get(as_string=True)
        type_map = {'UInt8': '|u1', 'UInt16': '<u2', 'Float32':'<f4', "Float64":'<f8', "Int8": "|i1"}
        if cam_dtype in type_map:
            ret[key].setdefault('dtype_str', type_map[cam_dtype])
        return ret

class HDF5PluginWithFileStore(HDF5Plugin, FileStoreHDF5IterativeWrite):
    pass

class ProsilicaDetectorCamV33(ProsilicaDetectorCam):
    """This is used to update the standard prosilica to AD33."""

    wait_for_plugins = Cpt(EpicsSignal, "WaitForPlugins", string=True, kind="config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs["wait_for_plugins"] = "Yes"

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()

    #added by RL
    def ensure_blocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_blocking"):
                try:
                    cpt.ensure_blocking()
                except:
                    pass

class StandardProsilica(SingleTrigger, ProsilicaDetector):
    tiff = Cpt(TIFFPluginWithFileStore,
               suffix='TIFF1:',
               write_path_template='',)
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    trans1 = Cpt(TransformPlugin, "Trans1:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)

class StandardProsilicaV33(SingleTriggerV33, ProsilicaDetector):
    tiff = Cpt(TIFFPluginWithFileStore,
               suffix='TIFF1:',
               write_path_template='',)
    cam = Cpt(ProsilicaDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    trans1 = Cpt(TransformPlugin, "Trans1:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    @property
    def hints(self):
        return {'fields': [self.stats1.total.name]}

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)
    
    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(self.cam.acquire_time, self.cam.acquire_time.get())  # noop

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, self.cam.acquire_period.get())  # noop

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, self.cam.num_images.get())  # noop
    
class PilatusDetectorCamV33(PilatusDetectorCam):
    """This is used to update the standard prosilica to AD33."""

    wait_for_plugins = Cpt(EpicsSignal, "WaitForPlugins", string=True, kind="config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs["wait_for_plugins"] = "Yes"

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()

class PilatusV33(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template="/nsls2/xf11bm/Pilatus300/%Y/%m/%d/",
        root="/nsls2/xf11bm",
    )

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )
        # caput('XF:11BMB-ES{Det:SAXS}:cam1:AcquireTime', exposure_time)
        # caput('XF:11BMB-ES{Det:SAXS}:cam1:AcquirePeriod', exposure_time+0.1)

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

class Pilatus800V33(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template = "",
    )

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )
        
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquireTime', exposure_time)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquirePeriod', exposure_time+0.1)

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

class Pilatus8002V33(PilatusV33):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template="", # "/ramdisk/",
        # root="/ramdisk/",
    )

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)


class Pilatus2MV33(SingleTriggerV33, PilatusDetector):#, h5=False):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")
    trans1 = Cpt(TransformPlugin, "Trans1:")

    # self.h5 = h5
    # if h5:
    #     h5 = Cpt(
    #         HDF5PluginWithFileStore,
    #         suffix="HDF1:",
    #         write_path_template = "",
    #     )
    # else:         
    #     tiff = Cpt(
    #         TIFFPluginWithFileStore,
    #         suffix="TIFF1:",
    #         write_path_template = "",
    #     )
    tiff = Cpt(
            TIFFPluginWithFileStore,
            suffix="TIFF1:",
            write_path_template = "",
        )

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)


    # def stage(self, *args, **kwargs):
    #     if h5:
    #         self.h5.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
    #         self.h5.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
    #         self.h5.reg_root = assets_path() + f'{self.name}'

    #         # wrap the staging process in a retry loop
    #         error = None
    #         for retry in range(5):
    #             try:
    #                 return super().stage()
    #             except TimeoutError as err:
    #                 # Staging failed becasue the IOC did not answer
    #                 # some request in a resonable time
    #                 # Stash the exception as the variable 'error'
    #                 error = err
    #             else:
    #                 # Staging worked. Stop retyring.
    #                 break
    #         else:
    #             # We exhausted all retires and none worked.
    #             # Raise the error captured above to produce a useful error message.
    #             raise error
    #         return super().stage(*args, **kwargs)
    
    #     else:
    #         self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
    #         self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
    #         self.tiff.reg_root = assets_path() + f'{self.name}'
    #         return super().stage(*args, **kwargs)

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )    
        print('Setting exposure time to ', exposure_time)
        while self.cam.acquire_time.get() != exposure_time:
            #yield from asyncio.sleep(0.1)
            yield from bps.sleep(0.1)
            print('Waiting for exposure time to be set correctly...')

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

class Pilatus300V33(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template = "",
    )

    def stage(self, *args, **kwargs):
        self.tiff.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.tiff.reg_root = assets_path() + f'{self.name}'
        return super().stage(*args, **kwargs)

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )
        
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquireTime', exposure_time)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquirePeriod', exposure_time+0.1)

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

class PilatusV33_h5(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")
    trans1 = Cpt(TransformPlugin, "Trans1:")

    h5 = Cpt(
        HDF5PluginWithFileStore,
        suffix="HDF1:",
        write_path_template = "",
    )

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquireTime', exposure_time)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquirePeriod', exposure_time+0.1)

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

    def stage(self):
        self.h5.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.h5.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.h5.reg_root = assets_path() + f'{self.name}'

        # wrap the staging process in a retry loop
        error = None
        for retry in range(5):
            try:
                return super().stage()
            except TimeoutError as err:
                # Staging failed becasue the IOC did not answer
                # some request in a resonable time
                # Stash the exception as the variable 'error'
                error = err
            else:
                # Staging worked. Stop retyring.
                break
        else:
            # We exhausted all retires and none worked.
            # Raise the error captured above to produce a useful error message.
            raise error
        return super().stage(*args, **kwargs)

class Pilatus800V33_h5(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")
    trans1 = Cpt(TransformPlugin, "Trans1:")

    h5 = Cpt(
        HDF5PluginWithFileStore,
        suffix="HDF1:",
        write_path_template = "",
    )

    def setExposureTime(self, exposure_time, verbosity=3):
        yield from mv(
            self.cam.acquire_time,
            exposure_time,
            # self.cam.acquire_period,
            # exposure_time + 0.1,
        )
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquireTime', exposure_time)
        # caput('XF:11BMB-ES{Det:PIL2M}:cam1:AcquirePeriod', exposure_time+0.1)

    def setExposurePeriod(self, exposure_period, verbosity=3):
        yield from mv(self.cam.acquire_period, exposure_period)

    def setExposureNumber(self, exposure_number, verbosity=3):
        yield from mv(self.cam.num_images, exposure_number)

    def stage(self):
        self.h5.write_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.h5.read_path_template = assets_path() + f'{self.name}/%Y/%m/%d/'
        self.h5.reg_root = assets_path() + f'{self.name}'

        # wrap the staging process in a retry loop
        error = None
        for retry in range(5):
            try:
                return super().stage()
            except TimeoutError as err:
                # Staging failed becasue the IOC did not answer
                # some request in a resonable time
                # Stash the exception as the variable 'error'
                error = err
            else:
                # Staging worked. Stop retyring.
                break
        else:
            # We exhausted all retires and none worked.
            # Raise the error captured above to produce a useful error message.
            raise error
        return super().stage(*args, **kwargs)

if Camera_on==True:

    # time.sleep(1)
    fs1 = StandardProsilicaV33('XF:11BMA-BI{FS:1-Cam:1}', name='webcam-1')
    # time.sleep(1)
    fs2 = StandardProsilicaV33("XF:11BMA-BI{FS:2-Cam:1}", name="webcam-2")
    # time.sleep(1)
    # fs3 = StandardProsilicaV33("XF:11BMB-BI{FS:3-Cam:1}", name="webcam-3")

    fs3 = fs2
    # time.sleep(1)
    fs4 = StandardProsilicaV33("XF:11BMB-BI{FS:4-Cam:1}", name="webcam-4")
    # mobile camera
    fs5 = StandardProsilicaV33("XF:11BMB-BI{FS:Test-Cam:1}", name="webcam-5")
    # off-axis camera
    fs6 = StandardProsilicaV33("XF:11BMB-BI{OffAxis-Cam:1}", name="webcam-6")
    # on-axis camera
    fs8 = StandardProsilicaV33("XF:11BMB-BI{Cam:08}", name="webcam-8")
    fs9 = StandardProsilicaV33("XF:11BMB-BI{OnAxis-Cam:2}", name="webcam-9")

    # all_standard_pros = [fs2, fs3, fs4]
    all_standard_pros = [fs2, fs4]


    time.sleep(1)

    # for cam_number, fs in zip([1,2,3,4], [fs1, fs2, fs3, fs4]):
    # for cam_number, fs in zip([2, 3, 4], [fs2, fs3, fs4]):
    for cam_number, fs in zip([2, 4], [fs2, fs4]):
        G, port_dict = fs.get_asyn_digraph()
        cam = port_dict["cam{:02}".format(cam_number)]
        for v in port_dict.values():
            try:
                if v.nd_array_port.get() == "CAM":
                    v.nd_array_port.set("cam{:02}".format(cam_number))
            except AttributeError:
                pass
        fs.validate_asyn_ports()




    # fs1.tiff.read_attrs = []
    # fs1.stats3.total.kind = "hinted"
    # fs1.stats4.total.kind = "hinted"
    # STATS_NAMES = ["stats1", "stats2", "stats3", "stats4", "stats5"]
    # fs1.read_attrs = ["tiff"] + STATS_NAMES
    # for stats_name in STATS_NAMES:
    #     stats_plugin = getattr(fs1, stats_name)
    #     stats_plugin.read_attrs = ["total"]

    # for item in fs1.stats1.configuration_attrs:
    #     item_check = getattr(fs1.stats1, item)
    #     item_check.kind = "omitted"

    # for item in fs1.stats2.configuration_attrs:
    #     item_check = getattr(fs1.stats2, item)
    #     item_check.kind = "omitted"

    # for item in fs1.stats3.configuration_attrs:
    #     item_check = getattr(fs1.stats3, item)
    #     item_check.kind = "omitted"

    # for item in fs1.stats4.configuration_attrs:
    #     item_check = getattr(fs1.stats4, item)
    #     item_check.kind = "omitted"

    # for item in fs1.stats5.configuration_attrs:
    #     item_check = getattr(fs1.stats5, item)
    #     item_check.kind = "omitted"

    # for item in fs1.tiff.configuration_attrs:
    #     item_check = getattr(fs1.tiff, item)
    #     item_check.kind = "omitted"

    # for item in fs1.cam.configuration_attrs:
    #     item_check = getattr(fs1.cam, item)
    #     item_check.kind = "omitted"

    # all_standard_pros = [fs1, fs2, fs3, fs4, fs5, fs6, fs8, fs9]
    all_standard_pros = [fs1, fs2, fs4, fs5, fs6, fs8, fs9]
    for camera in all_standard_pros:
        camera.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']
        # camera.tiff.read_attrs = []  # leaving just the 'image'
        for stats_name in ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']:
            stats_plugin = getattr(camera, stats_name)
            stats_plugin.read_attrs = ['total']
        camera.cam.ensure_nonblocking()

        camera.read_attrs.append('tiff')
        camera.tiff.read_attrs = []
        # camera.cam.ensure_nonblocking()


# class StandardsimDetectorV33(SingleTriggerV33, ProsilicaDetector):
#     # tiff = Cpt(TIFFPluginWithFileStore,
#     #           suffix='TIFF1:',
#     #           write_path_template='/XF11ID/data/')
#     cam = Cpt(ProsilicaDetectorCamV33, 'cam1:')
#     image = Cpt(ImagePlugin, 'image1:')
#     stats1 = Cpt(StatsPluginV33, 'Stats1:')
#     stats2 = Cpt(StatsPluginV33, 'Stats2:')
#     stats3 = Cpt(StatsPluginV33, 'Stats3:')
#     stats4 = Cpt(StatsPluginV33, 'Stats4:')
#     stats5 = Cpt(StatsPluginV33, 'Stats5:')
#     trans1 = Cpt(TransformPlugin, 'Trans1:')
#     roi1 = Cpt(ROIPlugin, 'ROI1:')
#     roi2 = Cpt(ROIPlugin, 'ROI2:')
#     roi3 = Cpt(ROIPlugin, 'ROI3:')
#     roi4 = Cpt(ROIPlugin, 'ROI4:')
#     proc1 = Cpt(ProcessPlugin, 'Proc1:')

# simDetector = StandardsimDetectorV33('13SIM1:', name='simDetector')


# all_standard_pros = [fs1, fs2, fs3, fs4, fs5, simDetector]
# all_standard_pros = [fs1, fs2, fs3, fs4]
# all_standard_pros = [fs2, fs3, fs4]
# all_standard_pros = [fs2, fs4]


# for camera in all_standard_pros:
#     camera.read_attrs = ['stats1', 'stats2','stats3','stats4','stats5']
#     # camera.tiff.read_attrs = []  # leaving just the 'image'
#     for stats_name in ['stats1', 'stats2','stats3','stats4','stats5']:
#         stats_plugin = getattr(camera, stats_name)
#         stats_plugin.read_attrs = ['total']
#         #camera.stage_sigs[stats_plugin.blocking_callbacks] = 1

# camera.stage_sigs[camera.roi1.blocking_callbacks] = 1
# camera.stage_sigs[camera.trans1.blocking_callbacks] = 1
# camera.cam.ensure_nonblocking()

# camera.stage_sigs[camera.cam.trigger_mode] = 'Fixed Rate'


# for camera in [xray_eye1_writing, xray_eye2_writing, xray_eye3_writing]:
#    camera.read_attrs.append('tiff')
#    camera.tiff.read_attrs = []

# pilatus300 section is marked out as the detector sever cannot be reached after AC power outrage. 121417-RL
# pilatus300 section is unmarked.  032018-MF
# pilatus300 section is marked out for bluesky upgrade.  010819-RL




# # pilatus300 section
# # Deprecated Old detector for SAXS
# # if True:
# if Pilatus300_on == True:
#     pilatus300 = Pilatus300V33("XF:11BMB-ES{Det:SAXS}:", name="pilatus300k-1")
#     # pilatus300 = PilatusV33('XF:11BMB-ES{Det:SAXS}:', name="pilatus300k-1")
#     pilatus300.tiff.read_attrs = []
#     pilatus300.stats3.total.kind = "hinted"
#     pilatus300.stats4.total.kind = "hinted"
#     STATS_NAMES = ["stats1", "stats2", "stats3", "stats4", "stats5"]
#     pilatus300.read_attrs = ["tiff"] + STATS_NAMES
#     for stats_name in STATS_NAMES:
#         stats_plugin = getattr(pilatus300, stats_name)
#         stats_plugin.read_attrs = ["total"]

#     pilatus300.cam.ensure_nonblocking()
# else:
#     pilatus300 = "Pil300ISNOTWORKING"

# pilatus800 section
if Pilatus800_on == True:
    pilatus800 = Pilatus800V33("XF:11BMB-ES{Det:PIL800K}:", name="pilatus800k-1")
    pilatus800.tiff.read_attrs = []
    pilatus800.stats3.total.kind = "hinted"
    pilatus800.stats4.total.kind = "hinted"
    STATS_NAMES = ["stats1", "stats2", "stats3", "stats4", "stats5"]
    pilatus800.read_attrs = ["tiff"] + STATS_NAMES
    # pilatus800.cam.ensure_blocking()

    for stats_name in STATS_NAMES:
        stats_plugin = getattr(pilatus800, stats_name)
        stats_plugin.read_attrs = ["total"]

    for item in pilatus800.stats1.configuration_attrs:
        item_check = getattr(pilatus800.stats1, item)
        item_check.kind = "omitted"

    for item in pilatus800.stats2.configuration_attrs:
        item_check = getattr(pilatus800.stats2, item)
        item_check.kind = "omitted"

    for item in pilatus800.stats3.configuration_attrs:
        item_check = getattr(pilatus800.stats3, item)
        item_check.kind = "omitted"

    for item in pilatus800.stats4.configuration_attrs:
        item_check = getattr(pilatus800.stats4, item)
        item_check.kind = "omitted"

    for item in pilatus800.stats5.configuration_attrs:
        item_check = getattr(pilatus800.stats5, item)
        item_check.kind = "omitted"

    for item in pilatus800.tiff.configuration_attrs:
        item_check = getattr(pilatus800.tiff, item)
        item_check.kind = "omitted"

    for item in pilatus800.cam.configuration_attrs:
        item_check = getattr(pilatus800.cam, item)
        item_check.kind = "omitted"
else:
    pilatus800 = "Pil800ISNOTWORKING"

# pilatus800_2 section  changed by RL, 20210831
# if False:
# if True:
if Pilatus800_2_on == True:
    # TODO:
    pilatus8002 = Pilatus8002V33("XF:11BMB-ES{Det:PIL800K2}:", name="pilatus800k-2")  # change PV
    pilatus8002.tiff.read_attrs = []
    pilatus8002.stats3.total.kind = "hinted"
    pilatus8002.stats4.total.kind = "hinted"
    STATS_NAMES = ["stats1", "stats2", "stats3", "stats4", "stats5"]
    pilatus8002.read_attrs = ["tiff"] + STATS_NAMES
    for stats_name in STATS_NAMES:
        stats_plugin = getattr(pilatus8002, stats_name)
        stats_plugin.read_attrs = ["total"]

    for item in pilatus8002.stats1.configuration_attrs:
        item_check = getattr(pilatus8002.stats1, item)
        item_check.kind = "omitted"

    for item in pilatus8002.stats2.configuration_attrs:
        item_check = getattr(pilatus8002.stats2, item)
        item_check.kind = "omitted"

    for item in pilatus8002.stats3.configuration_attrs:
        item_check = getattr(pilatus8002.stats3, item)
        item_check.kind = "omitted"

    for item in pilatus8002.stats4.configuration_attrs:
        item_check = getattr(pilatus8002.stats4, item)
        item_check.kind = "omitted"

    for item in pilatus8002.stats5.configuration_attrs:
        item_check = getattr(pilatus8002.stats5, item)
        item_check.kind = "omitted"

    for item in pilatus8002.tiff.configuration_attrs:
        item_check = getattr(pilatus8002.tiff, item)
        item_check.kind = "omitted"

    for item in pilatus8002.cam.configuration_attrs:
        item_check = getattr(pilatus8002.cam, item)
        item_check.kind = "omitted"
else:
    pilatus8002 = "Pil800-2ISNOTWORKING"

# pilatus2M section
# if False:
if Pilatus2M_on == True:
    pilatus2M = Pilatus2MV33("XF:11BMB-ES{Det:PIL2M}:", name="pilatus2m-1")
    pilatus2M.tiff.read_attrs = []

    STATS_NAMES2M = ["stats1", "stats2", "stats3", "stats4"]
    pilatus2M.read_attrs = ["tiff"] + STATS_NAMES2M
    for stats_name in STATS_NAMES2M:
        stats_plugin = getattr(pilatus2M, stats_name)
        stats_plugin.read_attrs = ["total"]
    # pilatus2M.cam.ensure_nonblocking() #changed by RL 25-11-15, 
    # pilatus2M.cam.ensure_blocking() #changed by RL 25-11-15, 
    pilatus2M.tiff.ensure_blocking()
    pilatus2M.stats3.total.kind = "hinted"
    pilatus2M.stats4.total.kind = "hinted"

    for item in pilatus2M.stats1.configuration_attrs:
        item_check = getattr(pilatus2M.stats1, item)
        item_check.kind = "omitted"

    for item in pilatus2M.stats2.configuration_attrs:
        item_check = getattr(pilatus2M.stats2, item)
        item_check.kind = "omitted"

    for item in pilatus2M.stats3.configuration_attrs:
        item_check = getattr(pilatus2M.stats3, item)
        item_check.kind = "omitted"

    for item in pilatus2M.stats4.configuration_attrs:
        item_check = getattr(pilatus2M.stats4, item)
        item_check.kind = "omitted"

    for item in pilatus2M.stats5.configuration_attrs:
        item_check = getattr(pilatus2M.stats5, item)
        item_check.kind = "omitted"

    for item in pilatus2M.tiff.configuration_attrs:
        item_check = getattr(pilatus2M.tiff, item)
        item_check.kind = "omitted"

    for item in pilatus2M.cam.configuration_attrs:
        item_check = getattr(pilatus2M.cam, item)
        item_check.kind = "omitted"

else:
    pilatus2M = "Pil2MISNOTWORKING"

if Pilatus300_on == True:
    pilatus300 = Pilatus300V33("XF:11BM-ES{Det-P300K:2}:", name="pilatus300k")
    pilatus300.tiff.read_attrs = []
    pilatus300.stats3.total.kind = "hinted"
    pilatus300.stats4.total.kind = "hinted"
    STATS_NAMES = ["stats1", "stats2", "stats3", "stats4", "stats5"]
    pilatus300.read_attrs = ["tiff"] + STATS_NAMES
    # pilatus300.cam.ensure_blocking()

    for stats_name in STATS_NAMES:
        stats_plugin = getattr(pilatus300, stats_name)
        stats_plugin.read_attrs = ["total"]

    for item in pilatus300.stats1.configuration_attrs:
        item_check = getattr(pilatus300.stats1, item)
        item_check.kind = "omitted"

    for item in pilatus300.stats2.configuration_attrs:
        item_check = getattr(pilatus300.stats2, item)
        item_check.kind = "omitted"

    for item in pilatus300.stats3.configuration_attrs:
        item_check = getattr(pilatus300.stats3, item)
        item_check.kind = "omitted"

    for item in pilatus300.stats4.configuration_attrs:
        item_check = getattr(pilatus300.stats4, item)
        item_check.kind = "omitted"

    for item in pilatus300.stats5.configuration_attrs:
        item_check = getattr(pilatus300.stats5, item)
        item_check.kind = "omitted"

    for item in pilatus300.tiff.configuration_attrs:
        item_check = getattr(pilatus300.tiff, item)
        item_check.kind = "omitted"

    for item in pilatus300.cam.configuration_attrs:
        item_check = getattr(pilatus300.cam, item)
        item_check.kind = "omitted"
else:
    pilatus300 = "Pil300K-2_IS_NOT_WORKING"

# HDF5 plugin section for Pilatus detectors
if HDF5_on == True:

    # Pilatus2M detector with HDF5 plugin section
    if Pilatus2M_on == True:

        pilatus2M_h5 = PilatusV33_h5("XF:11BMB-ES{Det:PIL2M}:", name="pilatus2m-1")
        pilatus2M_h5.h5.read_attrs = []
        pilatus2M_h5.cam.ensure_nonblocking()

        STATS_NAMES2M = ["stats1", "stats2", "stats3", "stats4"]
        pilatus2M_h5.read_attrs = ["h5"] + STATS_NAMES2M
        # for stats_name in STATS_NAMES2M:
        #     stats_plugin = getattr(pilatus2M_h5, stats_name)
        #     stats_plugin.read_attrs = ["total"]
        # pilatus2M_h5.cam.ensure_nonblocking()
        # pilatus2M_h5.h5.ensure_blocking()
        # pilatus2M_h5.stats3.total.kind = "hinted"
        # pilatus2M_h5.stats4.total.kind = "hinted"

        for item in pilatus2M_h5.stats1.configuration_attrs:
            item_check = getattr(pilatus2M_h5.stats1, item)
            item_check.kind = "omitted"

        for item in pilatus2M_h5.stats2.configuration_attrs:
            item_check = getattr(pilatus2M_h5.stats2, item)
            item_check.kind = "omitted"

        for item in pilatus2M_h5.stats3.configuration_attrs:
            item_check = getattr(pilatus2M_h5.stats3, item)
            item_check.kind = "omitted"

        for item in pilatus2M_h5.stats4.configuration_attrs:
            item_check = getattr(pilatus2M_h5.stats4, item)
            item_check.kind = "omitted"

        for item in pilatus2M_h5.stats5.configuration_attrs:
            item_check = getattr(pilatus2M_h5.stats5, item)
            item_check.kind = "omitted"

        # for item in pilatus2M_h5.tiff.configuration_attrs:
        #     item_check = getattr(pilatus2M_h5.tiff, item)
        #     item_check.kind = "omitted"

        for item in pilatus2M_h5.cam.configuration_attrs:
            item_check = getattr(pilatus2M_h5.cam, item)
            item_check.kind = "omitted"


    # Pilatus800 detector with HDF5 plugin section
    if Pilatus800_on == True:
        pilatus800_h5 = PilatusV33_h5("XF:11BMB-ES{Det:PIL800K}:", name="pilatus800k-1")
        pilatus800_h5.h5.read_attrs = []
        pilatus800_h5.cam.ensure_nonblocking()

        STATS_NAMES2M = ["stats1", "stats2", "stats3", "stats4"]
        pilatus800_h5.read_attrs = ["h5"] + STATS_NAMES2M

        for stats_name in STATS_NAMES:
            stats_plugin = getattr(pilatus800_h5, stats_name)
            stats_plugin.read_attrs = ["total"]

        for item in pilatus800_h5.stats1.configuration_attrs:
            item_check = getattr(pilatus800_h5.stats1, item)
            item_check.kind = "omitted"

        for item in pilatus800_h5.stats2.configuration_attrs:
            item_check = getattr(pilatus800_h5.stats2, item)
            item_check.kind = "omitted"

        for item in pilatus800_h5.stats3.configuration_attrs:
            item_check = getattr(pilatus800_h5.stats3, item)
            item_check.kind = "omitted"

        for item in pilatus800_h5.stats4.configuration_attrs:
            item_check = getattr(pilatus800_h5.stats4, item)
            item_check.kind = "omitted"

        for item in pilatus800_h5.stats5.configuration_attrs:
            item_check = getattr(pilatus800_h5.stats5, item)
            item_check.kind = "omitted"

        # for item in pilatus800_h5.tiff.configuration_attrs:
        #     item_check = getattr(pilatus800_h5.tiff, item)
        #     item_check.kind = "omitted"

        for item in pilatus800_h5.cam.configuration_attrs:
            item_check = getattr(pilatus800_h5.cam, item)
            item_check.kind = "omitted"

    # Pilatus800_2 detector with HDF5 plugin section
    if Pilatus800_2_on == True:
        pilatus8002_h5 = PilatusV33_h5("XF:11BMB-ES{Det:PIL800K2}:", name="pilatus800k-2")
        pilatus8002_h5.h5.read_attrs = []

        STATS_NAMES2M = ["stats1", "stats2", "stats3", "stats4"]
        pilatus8002_h5.read_attrs = ["h5"] + STATS_NAMES2M
        pilatus8002_h5.cam.ensure_nonblocking()

        for stats_name in STATS_NAMES:
            stats_plugin = getattr(pilatus8002_h5, stats_name)
            stats_plugin.read_attrs = ["total"]

        for item in pilatus8002_h5.stats1.configuration_attrs:
            item_check = getattr(pilatus8002_h5.stats1, item)
            item_check.kind = "omitted"

        for item in pilatus8002_h5.stats2.configuration_attrs:
            item_check = getattr(pilatus8002_h5.stats2, item)
            item_check.kind = "omitted"

        for item in pilatus8002_h5.stats3.configuration_attrs:
            item_check = getattr(pilatus8002_h5.stats3, item)
            item_check.kind = "omitted"

        for item in pilatus8002_h5.stats4.configuration_attrs:
            item_check = getattr(pilatus8002_h5.stats4, item)
            item_check.kind = "omitted"

        for item in pilatus8002_h5.stats5.configuration_attrs:
            item_check = getattr(pilatus8002_h5.stats5, item)
            item_check.kind = "omitted"

        # for item in pilatus8002_h5.tiff.configuration_attrs:
        #     item_check = getattr(pilatus8002_h5.tiff, item)
        #     item_check.kind = "omitted"

        for item in pilatus8002_h5.cam.configuration_attrs:
            item_check = getattr(pilatus8002_h5.cam, item)
            item_check.kind = "omitted"



# define the current pilatus detector: pilatus_name and _Epicsname, instead of
# pilatus300 or pilatus2M
# pilatus_name = pilatus800
# pilatus_Epicsname = '{Det:PIL800K}'
pilatus_name = pilatus2M
pilatus_Epicsname = "{Det:PIL2M}"

# pilatus_name = pilatus800
# pilatus_Epicsname = '{Det:PIL800K}'


#######################################################
# These are test functions added by Julien
# We should remove them once we find the source of the
# current "None"type bug at CMS (TRAC ticket [2284]
def get_stage_sigs(dev, dd):
    for cpt_name in dev.component_names:
        cpt = getattr(dev, cpt_name)
        if hasattr(cpt, "stage_sigs"):
            dd.update(cpt.stage_sigs)
        if hasattr(cpt, "component_names"):
            get_stage_sigs(cpt, dd)


def stage_unstage_forever_plan(det):
    i = 0
    print("Started the stage_unstage_plan, running infinite loop...")
    while True:
        i += 1
        # print(f"Staging {i}th time")
        yield from bps.stage(det)
        yield from bps.unstage(det)


def trigger_forever_plan(det):
    i = 0
    print("Started the stage_unstage_plan, running infinite loop...")
    while True:
        i += 1
        # print(f"Staging {i}th time")
        yield from bps.stage(det)
        yield from bps.trigger(det, group="det")
        yield from bps.wait("det")
        yield from bps.unstage(det)


def count_forever_plan(det):
    i = 0
    print("Started the count_forever plan, running infinite loop...")
    while True:
        i += 1
        # print(f"Staging {i}th time")
        yield from bp.count([det])


def stage_unstage_once_plan(det):
    # print(f"Staging {i}th time")
    yield from bps.stage(det)
    yield from bps.unstage(det)


def count_no_save_plan(det):
    # print(f"Staging {i}th time")
    yield from bps.stage(det)
    yield from bps.trigger(det)
    yield from bps.unstage(det)


# to get stage sigs
# from collections import OrderedDict
# stage_sigs = OrderedDict()
# get_stage_sigs(pilatus2M, stage_sigs)


#######################################################

# pilatus_name = pilatus300
# pilatus_Epicsname = '{Det:SAXS}'



print(f'Loading {__file__}')



def pil2M_test():
    for ii in range(10):
        # pilatus2M.cam.acquire_time.set(5)
        yield from pilatus2M.setExposureTime(10)
        yield from count([pilatus2M])
        yield from pilatus2M.setExposureTime(5)
        yield from count([pilatus2M])


def pil2M_test2():
    for ii in range(10):
        pilatus2M.cam.acquire_time.set(10)
        RE(count([pilatus2M]))
        pilatus2M.cam.acquire_time.set(5)
        for jj in range(300):
            print(pilatus2M.cam.acquire_time.get())
            time.sleep(0.01)
        RE(count([pilatus2M]))
