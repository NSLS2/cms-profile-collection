from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin, DetectorBase, ADBase)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.sim import NullStatus  # TODO: remove after complete/collect are defined
from ophyd import Component as Cpt
from ophyd import DynamicDeviceComponent as DDC
from ophyd.status import SubscriptionStatus, DeviceStatus

from pathlib import PurePath
from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector, Xspress3DetectorSettings, make_rois,
                                       Xspress3Channel, Xspress3FileStore, Xspress3ROI, logger)

# from isstools.trajectory.trajectory import trajectory_manager

import bluesky.plans as bp
import bluesky.plan_stubs as bps

import numpy as np
import itertools
import time as ttime
from collections import deque, OrderedDict
import warnings
from databroker.assets.handlers import XS3_XRF_DATA_KEY as XRF_DATA_KEY


class Xspress3FileStoreFlyable(Xspress3FileStore):
    def warmup(self):
        """
        A convenience method for 'priming' the plugin.
        The plugin has to 'see' one acquisition before it is ready to capture.
        This sets the array size, etc.
        NOTE : this comes from:
            https://github.com/NSLS-II/ophyd/blob/master/ophyd/areadetector/plugins.py
        We had to replace "cam" with "settings" here.
        Also modified the stage sigs.
        """
        print("warming up the hdf5 plugin...")
        self.enable.set(1).wait()
        sigs = OrderedDict([(self.parent.settings.array_callbacks, 1),
                            (self.parent.settings.trigger_mode, 'Internal'),
                            # just in case the acquisition time is set very long...
                            (self.parent.settings.acquire_time, 1),
                            # (self.capture, 1),
                            (self.parent.settings.acquire, 1)])

        original_vals = {sig: sig.get() for sig in sigs}

        # Remove the hdf5.capture item here to avoid an error as it should reset back to 0 itself
        # del original_vals[self.capture]

        for sig, val in sigs.items():
            ttime.sleep(0.1)  # abundance of caution
            sig.set(val).wait()

        ttime.sleep(2)  # wait for acquisition

        for sig, val in reversed(list(original_vals.items())):
            ttime.sleep(0.1)
            sig.set(val).wait()
        print("done")

class Xspress3XDetector(DetectorBase):
    settings = Cpt(Xspress3DetectorSettings, 'det1:')

    external_trig = Cpt(Signal, value=False,
                        doc='Use external triggering')
    total_points = Cpt(Signal, value=-1,
                       doc='The total number of points to acquire overall')
    spectra_per_point = Cpt(Signal, value=1,
                            doc='Number of spectra per point')
    make_directories = Cpt(Signal, value=False,
                           doc='Make directories on the DAQ side')
    rewindable = Cpt(Signal, value=False,
                     doc='Xspress3 cannot safely be rewound in bluesky')

    # channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1)
    # XF:11BM-ES{Xsp:1}

    data_key = XRF_DATA_KEY

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None,
                 # to remove?
                 file_path='', ioc_file_path='', default_channels=None,
                 channel_prefix=None,
                 roi_sums=False,
                 # to remove?
                 **kwargs):

        if read_attrs is None:
            read_attrs = ['channel1', ]

        if configuration_attrs is None:
            configuration_attrs = ['channel1.rois', 'settings']

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

        # get all sub-device instances
        sub_devices = {attr: getattr(self, attr)
                       for attr in self._sub_devices}

        # filter those sub-devices, just giving channels
        channels = {dev.channel_num: dev
                    for attr, dev in sub_devices.items()
                    if isinstance(dev, Xspress3Channel)
                    }

        # make an ordered dictionary with the channels in order
        self._channels = OrderedDict(sorted(channels.items()))

    @property
    def channels(self):
        return self._channels.copy()

    @property
    def all_rois(self):
        for ch_num, channel in self._channels.items():
            for roi in channel.all_rois:
                yield roi

    @property
    def enabled_rois(self):
        for roi in self.all_rois:
            if roi.enable.get():
                yield roi

    def read_hdf5(self, fn, *, rois=None, max_retries=2):
        '''Read ROI data from an HDF5 file using the current ROI configuration

        Parameters
        ----------
        fn : str
            HDF5 filename to load
        rois : sequence of Xspress3ROI instances, optional

        '''
        if rois is None:
            rois = self.enabled_rois

        num_points = self.settings.num_images.get()
        if isinstance(fn, h5py.File):
            hdf = fn
        else:
            hdf = h5py.File(fn, 'r')

        RoiTuple = Xspress3ROI.get_device_tuple()

        handler = Xspress3HDF5Handler(hdf, key=self.data_key)
        for roi in self.enabled_rois:
            roi_data = handler.get_roi(chan=roi.channel_num,
                                       bin_low=roi.bin_low.get(),
                                       bin_high=roi.bin_high.get(),
                                       max_points=num_points)

            roi_info = RoiTuple(bin_low=roi.bin_low.get(),
                                bin_high=roi.bin_high.get(),
                                ev_low=roi.ev_low.get(),
                                ev_high=roi.ev_high.get(),
                                value=roi_data,
                                value_sum=None,
                                enable=None)

            yield roi.name, roi_info


class Xspress3XChannel(ADBase):
    roi_name_format = 'Det{self.channel_num}_{roi_name}'
    roi_sum_name_format = 'Det{self.channel_num}_{roi_name}_sum'

    rois = DDC(make_rois(range(1, 4)))
    vis_enabled = Cpt(EpicsSignal, 'EnableCallbacks')
    # extra_rois_enabled = Cpt(EpicsSignal, 'PluginControlValExtraROI')

    def __init__(self, prefix, *, channel_num=None, **kwargs):
        self.channel_num = int(channel_num)

        super().__init__(prefix, **kwargs)

    @property
    def all_rois(self):
        for roi in range(1, self.rois.num_rois.get() + 1):
            yield getattr(self.rois, 'roi{:02d}'.format(roi))

    def set_roi(self, index, ev_low, ev_high, *, name=None):
        '''Set specified ROI to (ev_low, ev_high)

        Parameters
        ----------
        index : int or Xspress3ROI
            The roi index or instance to set
        ev_low : int
            low eV setting
        ev_high : int
            high eV setting
        name : str, optional
            The unformatted ROI name to set. Each channel specifies its own
            `roi_name_format` and `roi_sum_name_format` in which the name
            parameter will get expanded.
        '''
        if isinstance(index, Xspress3ROI):
            roi = index
        else:
            if index <= 0:
                raise ValueError('ROI index starts from 1')
            roi = list(self.all_rois)[index - 1]

        roi.configure(ev_low, ev_high)
        if name is not None:
            roi_name = self.roi_name_format.format(self=self, roi_name=name)
            roi.name = roi_name
            roi.value.name = roi_name
            roi.value_sum.name = self.roi_sum_name_format.format(self=self,
                                                                 roi_name=name)

    def clear_all_rois(self):
        '''Clear all ROIs'''
        for roi in self.all_rois:
            roi.clear()

xsx = QASXspress3XDetector('XF:11BM-ES{Xsp:1}:', name='xspress3-1')

class QASXspress3XDetector(XspressTrigger, Xspress3XDetector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel1 = Cpt(Xspress3XChannel, 'C1_', channel_num=1, read_attrs=['rois'])
    # create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')

    mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')

    cnt_time = Cpt(EpicsSignal, 'C1_SCA0:Value_RBV')

    # channel6 = Cpt(Xspress3Channel, 'C6_', channel_num=6)

    #TODO change folder to xspress3
    # hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF1:',
    #            read_path_template='/nsls2/data/qas-new/legacy/raw/x3x/%Y/%m/%d/',
    #            root='/nsls2/data/qas-new/legacy/raw/',
    #            write_path_template='/nsls2/data/qas-new/legacy/raw/x3x/%Y/%m/%d/',
    #            )
    hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF1:',write_path_template='',)

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'hdf5', 'settings.acquire_time']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.set_channels_for_hdf5()

        self._asset_docs_cache = deque()
        self._datum_counter = None

        self.channel1.rois.roi01.configuration_attrs.append('bin_low')

    # Step-scan interface methods.
    def stage(self, *args, **kwargs):
        if self.spectra_per_point.get() != 1:
            raise NotImplementedError(
                "multi spectra per point not supported yet")
        self.hdf5.write_path_template = assets_path() + f'{xsx.name}/%Y/%m/%d/'
        self.hdf5.read_path_template = assets_path() + f'{xsx.name}/%Y/%m/%d/'
        self.hdf5.reg_root = assets_path() + f'{xsx.name}'
        ret = super().stage(*args, **kwargs)
        self._datum_counter = itertools.count()
        return ret

    def trigger(self):

        self._status = DeviceStatus(self)
        self.settings.erase.put(1)
        self._acquisition_signal.put(1, wait=False)
        trigger_time = ttime.time()

        for sn in self.read_attrs:
            if sn.startswith('channel') and '.' not in sn:
                ch = getattr(self, sn)
                self.generate_datum(ch.name, trigger_time)

        self._abs_trigger_count += 1
        return self._status

    def unstage(self):
        self.settings.trigger_mode.put(1)  # 'Software'
        super().unstage()
        self._datum_counter = None

    def stop(self):
        ret = super().stop()
        self.hdf5.stop()
        return ret

    def collect(self):
        # TODO: try to separate it from the xspress3 class
        collected_frames = self.settings.array_counter.get()

        # This is a hack around the issue with .NORD (number of elements to #
        # read) that does not match .NELM (number of elements to that the array
        # will hold)
        dpb_sec_nelm_count = int(dpb_sec_nelm.get())
        dpb_nsec_nelm_count = int(dpb_nsec_nelm.get())
        dpb_sec_values = np.array(dpb_sec.get(count=dpb_sec_nelm_count),
                                  dtype='float128')[:collected_frames * 2: 2]
        dpb_nsec_values = np.array(dpb_nsec.get(count=dpb_nsec_nelm_count),
                                   dtype='float128')[:collected_frames * 2: 2]

        di_timestamps = dpb_sec_values + dpb_nsec_values * 1e-9

        len_di_timestamps = len(di_timestamps)
        len_datum_ids = len(self._datum_ids)

        if len_di_timestamps != len_datum_ids:
            warnings.warn(f'The length of "di_timestamps" ({len_di_timestamps}) '
                          f'does not match the length of "self._datum_ids" ({len_datum_ids})')

        num_frames = min(len_di_timestamps, len_datum_ids)
        num_frames = len_datum_ids
        for frame_num in range(num_frames):
            datum_id = self._datum_ids[frame_num]
            # ts = di_timestamps[frame_num]
            ts = di_timestamps

            data = {self.name: datum_id}
            # TODO: fix the lost precision as pymongo complained about np.float128.
            ts = float(ts)

            yield {'data': data,
                   'timestamps': {key: ts for key in data},
                   'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
                   'filled': {key: False for key in data}}

    def set_channels_for_hdf5(self, channels=(1)):
        """
        Configure which channels' data should be saved in the resulted hdf5 file.
        Parameters
        ----------
        channels: tuple, optional
            the channels to save the data for
        """
        # The number of channel
        for n in channels:
            getattr(self, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in [1]]
        self.hdf5.num_extra_dims.put(0)
        self.settings.num_channels.put(8)


def initialize_Xspress3X(xsx, hdf5_warmup=True):
    # TODO: do not put on startup or do it conditionally, if on beamline.
    xsx.channel1.vis_enabled.put(1)
    xsx.total_points.put(1)

    # This is necessary for when the ioc restarts
    # we have to trigger one image for the hdf5 plugin to work correctly
    # else, we get file writing errors
    if hdf5_warmup:
        xsx.hdf5.warmup()

    # Hints:
    for n in [1, 2]:  # TODO: 8?
        getattr(xsx, f'channel{n}').rois.roi01.value.kind = 'hinted'

    xsx.settings.configuration_attrs = ['acquire_period',
                                       'acquire_time',
                                       'gain',
                                       'image_mode',
                                       'manufacturer',
                                       'model',
                                       'num_exposures',
                                       'num_images',
                                       'temperature',
                                       'temperature_actual',
                                       'trigger_mode',
                                       'config_path',
                                       'config_save_path',
                                       'invert_f0',
                                       'invert_veto',
                                       'xsp_name',
                                       'num_channels',
                                       'num_frames_config',
                                       'run_flags',
                                       'trigger_signal']

    for n, d in xsx.channels.items():
        roi_names = ['roi{:02}'.format(j) for j in [1]]
        d.rois.read_attrs = roi_names
        d.rois.configuration_attrs = roi_names
        for roi_n in roi_names:
            getattr(d.rois, roi_n).value_sum.kind = 'omitted'


initialize_Xspress3X(xsx)


def xsx_count(acq_time: float = 1, num_frames: int = 1):
    yield from bps.mv(xsx.settings.erase, 0)
    yield from bp.count([xsx], acq_time)


class QASXspress3XDetectorStream(QASXspress3XDetector):

    def stage(self, acq_rate, traj_time, *args, **kwargs):
        self.hdf5.file_write_mode.put(2)  # put it to Stream |||| IS ALREADY STREAMING
        self.external_trig.put(True)
        self.set_expected_number_of_points(acq_rate, traj_time)
        self.spectra_per_point.put(1)
        self.settings.trigger_mode.put(3)  # put the trigger mode to TTL in

        super().stage(*args, **kwargs)
        # note, hdf5 is already capturing at this point
        self.settings.acquire.put(1)  # start recording data

    def set_expected_number_of_points(self, acq_rate, traj_time):
        self._num_points = int(acq_rate * (traj_time + 1))
        self.total_points.put(self._num_points)

    def describe_collect(self):
        return_dict = {self.name:
                           {f'{self.name}': {'source': 'XS',
                                             'dtype': 'array',
                                             'shape': [self.settings.num_images.get(),
                                                       self.hdf5.array_size.height.get(),
                                                       self.hdf5.array_size.width.get()],
                                             'filename': f'{self.hdf5.full_file_name.get()}',
                                             'external': 'FILESTORE:'}}}
        return return_dict

    def collect(self):
        num_frames = len(self._datum_ids)

        # break num_frames up and yield in sections?

        for frame_num in range(num_frames):
            datum_id = self._datum_ids[frame_num]
            data = {self.name: datum_id}

            ts = ttime.time()

            yield {'data': data,
                   'timestamps': {key: ts for key in data},
                   'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
                   'filled': {key: False for key in data}}
            # print(f"-------------------{ts}-------------------------------------")

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item

xsx_stream = QASXspress3XDetectorStream('XF:11BM-ES{Xsp:1}:', name='xsx_stream')
initialize_Xspress3X(xsx_stream, hdf5_warmup=True)


from itertools import product
import pandas as pd
from databroker.assets.handlers import HandlerBase, Xspress3HDF5Handler


class QASXspress3XHDF5Handler(Xspress3HDF5Handler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._roi_data = None
        self._num_channels = None

    def _get_dataset(
            self):  # readpout of the following stuff should be done only once, this is why I redefined _get_dataset method - Denis Leshchev Feb 9, 2021
        # dealing with parent
        super()._get_dataset()

        # finding number of channels
        if self._num_channels is not None:
            return
        print('determining number of channels')
        shape = self.dataset.shape
        if len(shape) != 3:
            raise RuntimeError(f'The ndim of the dataset is not 3, but {len(shape)}')
        self._num_channels = shape[1]

        if self._roi_data is not None:
            return
        print('reading ROI data')
        self.chanrois = [f'CHAN{c}ROI{r}' for c, r in product([1], [1])]
        _data_columns = [self._file['/entry/instrument/detector/NDAttributes'][chanroi][()] for chanroi in
                         self.chanrois]
        data_columns = np.vstack(_data_columns).T
        self._roi_data = pd.DataFrame(data_columns, columns=self.chanrois)

    def __call__(self, *args, frame=None, **kwargs):
        self._get_dataset()
        return_dict = {f'ch_{i + 1}': self._dataset[frame, i, :] for i in range(self._num_channels)}
        return_dict_rois = {chanroi: self._roi_data[chanroi][frame] for chanroi in self.chanrois}
        return {**return_dict, **return_dict_rois}


# heavy-weight file handler
db.reg.register_handler(QASXspress3XHDF5Handler.HANDLER_NAME,
                        QASXspress3XHDF5Handler, overwrite=True)
