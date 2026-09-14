# adopted from CHX

# imports for accessing data from channel archiver
from arvpyf import mgmt, cf
from arvpyf.mgmt import ArchiverConfig
from arvpyf.cf import PVFinder
from arvpyf.ar import ArchiverReader


class archiver(Device):
    # setup for CMS archiver
    def __init__(self):
        self.bpl_url = "http://epics-services-cms.nsls2.bnl.local:11165/mgmt/ui/metrics"
        self.bpl_url = self.bpl_url.removeprefix('http://')
        self.arvconf = ArchiverConfig(self.bpl_url)
        self.cf_update = "/cf-update/"
        self.pvfinder = PVFinder(self.cf_update)
        self.ar_url = "http://epics-services-cms.nsls2.bnl.local:11168"
        self.ar_url = self.ar_url.removeprefix('http://')
        # self.ar_url = 'http://epics-services-cms:11168'
        self.ar_tz = "US/Eastern"
        self.config = {"url": self.ar_url, "timezone": self.ar_tz}
        self.arvReader = ArchiverReader(self.config)

        self.stage = None
        self.PVs_default = []
        self.PVs_name_default = []
        self.PV_dict_default = dict()

    def setStage(self, stage="LinkamTensile"):
        if stage == "LinkamTensile":
            self.PVs_default = [
                "XF:11BM-ES:{LINKAM}:TEMP",
                "XF:11BM-ES:{LINKAM}:TST_MOTOR_POS",
                "XF:11BM-ES:{LINKAM}:TST_FORCE",
                "XF:11BM-ES:{LINKAM}:TST_STRESS",
            ]
            self.PVs_name_default = ["TEMPERATURE", "DISTANCE", "FORCE", "STRESS"]

    def get(self, PV):
        pass

    def getDict(self, PVs=None, PVs_name=None, verbosity=3):
        if PVs == None and PVs_name == None:
            PVs = self.PVs_default
            PVs_name = self.PVs_name_default

        PV_dict = dict()
        for pv, pv_name in zip(PVs, PVs_name):
            PV_dict.update({pv_name: {"PV": pv}})

        if verbosity >= 3:
            print(PV_dict)
        self.PV_dict_default = PV_dict
        return PV_dict
        # return

    def readPVs(self):
        print(self.PV_dict_default)

    def saveArchiver(self, scan_id=None, folder=None, PVs=None, PVs_name=None, plot=True):
        # create the PVs for saving

        PV_dict = self.getDict(PVs=PVs, PVs_name=PVs_name)
        # find the uid
        # idenfity the start and end points of the uid
        #

        uid_list = [[h.start["uid"] for h in db(scan_id=scan_id, experimental_directory=folder)][0]]

        pre = 0
        post = 0

        h0 = db[uid_list[0]]
        md = h0.start
        t0 = h0.start["time"]

        h1 = db[uid_list[-1]]
        t1 = h1.stop["time"]

        since = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0 - pre))
        until = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t1 + post))

        # create pandas for data storage
        PV_df = pds.DataFrame()

        for p in list(PV_dict.keys()):
            pv = PV_dict[p]["PV"]
            df = self.arvReader.get(pv, since, until)

            ep_time = []
            pv_data = []
            for i in range(np.shape(df.time)[0]):
                ep_time.append(datetime.timestamp(df.time[i]))
                pv_data.append(df.data[i])

            PV_df["a_time"] = ep_time
            PV_df[p] = pv_data

            # time_zero=ep_time[0]
            # ep_time=np.array(ep_time);pv_data=np.array(pv_data)

            # if p == 'tot':
            #     pv_data=pv_data-np.average(pv_data)
            #     lab='I$_{tot}$ - <I$_{tot}$>'
            # else:
            #     lab='%s-position [$\mu$m]'%p

            if plot:
                x = ep_time - t0
                y = pv_data
                xf, yf = butterworth_filter(x, y, order=3, span=0.005)

                plt.plot(xf, yf, "-", label=lab)
                plt.grid(True)
                plt.ylabel("BPM position / current")
                plt.xlabel("t$_1$ [s]")  # plt.xlabel('epoch [s]')

        if plot:
            plt.title("uid: %s  sample: %s" % (md["uid"][:8], md["sample"]), fontsize=14)
            plt.ylim(-2, 1)
            plt.legend(loc="upper left", bbox_to_anchor=(1.2, 0.98))

        # publish
        # PV_df.to_csv(output_name, )
        return PV_df


# CHX example

ARV = archiver()



bpl_url = "http://epics-services-cms.nsls2.bnl.local:11165/mgmt/ui/metrics"
arvconf = ArchiverConfig(bpl_url)
cf_update = '/cf-update/'
pvfinder = PVFinder(cf_update)
ar_url = "http://epics-services-cms.nsls2.bnl.local:11168"
ar_tz = 'US/Eastern'
config = {'url': ar_url, 'timezone': ar_tz}
arvReader = ArchiverReader(config)
# arvReader = ArchiverReader({"url": "http://epics-services-cms.nsls2.bnl.local:11168", "timezone": "US/Eastern"})
#


def get_acquisition_start_from_fs(uid,verbose=False):
    """
    determine start of data acquisition for Eigers for a given uid from the fast shutter position:
    assumption: signal to close fast shutter is send at end of data acquisition without delay
    returns: data_start_time [epoch] =  time when the detector actually started taking frames & shutter_close_time [epoch] =  time when the shutter-close signal was sent
    data_start_time = shutter_close_time-(acquire period * number of images)
    [data_start_time, shutter_close_time]
    by LW 04/28/2022
    """
    h=db[uid]
    # pv = 'XF:11IDB-ES{Zebra}:SOFT_IN:B0'
    pre=.5 #additional time included in the beginning [s]
    post=.5 #additional time included in the end [s]
    since=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h.start['time']-pre))
    until=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h.stop['time']+post))
    df = arvReader.get(pv, since, until)
    #if np.min(df.data.to_numpy()==np.array([0,1,0]))==True:
    if df.data.to_numpy()[-1]==0:
    # got the expected sequence ending with shutter closed
        shutter_close_time=datetime.timestamp(df.time.to_numpy()[-1])
        data_start_time=shutter_close_time-float(h.start['acquire period'])*float(h.start['number of images'])
    else:
        print(df.data.to_numpy())
        data_start_time=np.nan;shutter_close_time=np.nan
        print("couldn't determine data_start_time from shutter position...")
    if verbose:
        print('uid: %s\nstart time of data acquisition: %s  ->   epoch: %ss\nend time of data acquisition: %s   ->  epoch: %ss'
              %(uid,time.strftime('%Y-%m-%d %H:%M:%S:%mS', time.localtime(data_start_time)),data_start_time,time.strftime('%Y-%m-%d %H:%M:%S:%mS',time.localtime(shutter_close_time)),shutter_close_time))
    return [data_start_time,shutter_close_time]


def get_archived_pvs_from_uid(pv_list,uid,pre=0,post=0,verbose=True):
    """
    get_archived_pvs_from_uid(pv_list,uid,pre=0,post=0,verbose=True)
    -> get archived data for a list of PVs, time: between start and stop document of run(uid); use pre and post to extend time before and after
    Note: time of start document is t=0s, "pre" times are negative
   
    pv_list: list of strings that are the PVs for which we want archived data
    uid: uid or short uid of dataset
    pre: time [s] to get data befor time in start document for uid
    post: time [s] to get data past time in stop document for uid
   
    returns: dictionary: {'pv1':{'time':np.array(time [s]),'data':np.array(pv data from archiver)}}
    """
    # datetime has changed from datetime.datetime.timestamp to datetime.timestamp... make sure it works with current and legocy environments
    try:
        datetime.timestamp(datetime.now())
        current=True
    except:
        current=False
    h=db[uid]
    t0=h.start['time'];tmax=h.stop['time']
    since=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0-pre))
    until=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tmax+post))
    if verbose:
        print('getting archived data for PVs %s\nuid: %s\ntime: start of uid - %ss to end of uid +%ss\n%s - %s'%(pv_list,uid,pre,post,since,until))
    pv_dict = {}
    for p in pv_list:
        df = arvReader.get(p, since, until)
        ep_time=[]
        pv_data=[]
        for i in range(np.shape(df.time)[0]):
            if current:
                ep_time.append(datetime.timestamp(df.time[i]))
            else:
                p_time.append(datetime.datetime.timestamp(df.time[i]))
            pv_data.append(df.data[i])
        time_zero=ep_time[0]
        ep_time=np.array(ep_time);pv_data=np.array(pv_data)
        #x=ep_time-t0;y=pv_data
        pv_dict[p]={'time':ep_time-t0,'data':pv_data}
    return pv_dict

# pv_tot_cur='XF:11IDB-BI{XBPM:02}Ampl:CurrTotal-I' # total BPM current
# pv_bpm_x='XF:11IDB-BI{XBPM:02}Pos:X-I' # BPM position X
# pv_bpm_y='XF:11IDB-BI{XBPM:02}Pos:Y-I' # BPM position Y

# bpm_dict={'x':{'pv':pv_bpm_x},'y':{'pv':pv_bpm_y},'tot':{'pv':pv_tot_cur}}

# pre=0 #additional time included in the beginning [s]
# post=0 #additional time included in the end [s]
# h=db[uid_list[0]];md=h.start
# t0=h.start['time'];tmax=h.stop['time']
# since=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0-pre))
# until=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tmax+post))

# for p in list(bpm_dict.keys()):
#     pv=bpm_dict[p]['pv']
#     df = arvReader.get(pv, since, until)
#     ep_time=[]
#     pv_data=[]
#     for i in range(np.shape(df.time)[0]):
#         ep_time.append(datetime.timestamp(df.time[i]))
#         pv_data.append(df.data[i])
#     time_zero=ep_time[0]
#     ep_time=np.array(ep_time);pv_data=np.array(pv_data)

#     if p == 'tot':
#         pv_data=pv_data-np.average(pv_data)
#         lab='I$_{tot}$ - <I$_{tot}$>'
#     else:
#         lab='%s-position [$\mu$m]'%p

#     x=ep_time-t0;y=pv_data
#     xf,yf=butterworth_filter(x,y,order=3,span=.005)

#     plt.plot(xf,yf,'-',label=lab);
#     plt.grid(True);plt.ylabel('BPM position / current');plt.xlabel('t$_1$ [s]')#plt.xlabel('epoch [s]')
# plt.title('uid: %s  sample: %s'%(md['uid'][:8],md['sample']),fontsize=14)
# plt.ylim(-2,1)
# plt.legend(loc='upper left',bbox_to_anchor=(1.2,.98))

#### CMS customized Archiver decorators
#### Added by Siyu Wu, 2025/08

from functools import wraps

arvReader = ArchiverReader({"url": "http://epics-services-cms.nsls2.bnl.local:11168", 
                            "timezone": "US/Eastern"})

def archived(output_file, pv_list=None, dt=0.1, verbose=True):
    """
    Decorator to archive PVs using Archiver between function start and end.
    """
        
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            t_start = time.time()
            t_start_str = datetime.fromtimestamp(t_start).strftime("%Y-%m-%d %H:%M:%S")
            if verbose:
                print(f"[Archiver] Recording PVs from {t_start_str}")

            try:
                result = await func(*args, **kwargs)
            except KeyboardInterrupt:
                print("[Archiver] Interrupted! Archiving up to this point.")
                raise

            finally:
                t_end = time.time()
                t_end_str = datetime.fromtimestamp(t_end).strftime("%Y-%m-%d %H:%M:%S")
                if verbose:
                    print(f"[Archiver] Recording PVs until {t_end_str}")

                if dt is not None and dt > 0:
                    # Build fixed time grid
                    n_points = int((t_end - t_start) / dt) + 1
                    time_grid = np.linspace(t_start, t_end, n_points)
                    df_sync = pd.DataFrame({'timestamp': time_grid})
                    df_sync['time_elapsed'] = df_sync['timestamp'] - t_start

                    # For each PV, interpolate or forward-fill to time grid
                    for pv in pv_list:
                        try:
                            df = arvReader.get(pv, t_start_str, t_end_str)
                            # Convert archiver times to epoch seconds
                            pv_times = pd.to_datetime(df['time']).astype(np.int64) / 1e9
                            pv_data = df['data'].to_numpy()
                            # Interpolate to grid (linear, or nearest if only one point)
                            if len(pv_times) > 1:
                                interp_data = np.interp(time_grid, pv_times, pv_data)
                            elif len(pv_times) == 1:
                                interp_data = np.full_like(time_grid, pv_data[0])
                            else:
                                interp_data = np.full_like(time_grid, np.nan)
                            df_sync[f"{pv}_data"] = interp_data
                            if verbose:
                                print(f"[Archiver] {pv}: {len(pv_data)} points, interpolated to {len(interp_data)}")
                        except Exception as e:
                            print(f"[Archiver] Skipping PV '{pv}': {e}")
                            df_sync[f"{pv}_data"] = np.full_like(time_grid, np.nan)

                    # Move time_elapsed to first column
                    cols = ['time_elapsed'] + [c for c in df_sync.columns if c != 'time_elapsed']
                    df_sync = df_sync[cols]

                    df_sync.to_csv(output_file, index=False)
                    print(f"[Archiver] Saved {len(df_sync)} rows to {output_file}")
                
                else:
                    since = t_start_str
                    until = t_end_str
                    df_all = pd.DataFrame()
                    for pv in pv_list:
                        try:
                            df = arvReader.get(pv, since, until)
                            ep_time = [pd.Timestamp(t).timestamp() for t in df['time']]
                            pv_data = df['data'].to_numpy()
                            df_pv = pd.DataFrame({f"{pv}_time": ep_time, f"{pv}_data": pv_data})
                            df_all = pd.concat([df_all, df_pv], axis=1)
                            if verbose:
                                print(f"[Archiver] {pv}: {len(df_pv)} points")
                        except Exception as e:
                            print(f"[Archiver] Skipping PV '{pv}': {e}")
                    df_all.to_csv(output_file, index=False)
                    print(f"[Archiver] Saved {len(df_all)} rows to {output_file}")
            return result
        return wrapper
    return decorator

# Example Usage:

# linkam_pvs = [
#     "XF:11BM-ES:{LINKAM}:TEMP",            # Temperature
#     "XF:11BM-ES:{LINKAM}:TST_FORCE",       # Force
#     "XF:11BM-ES:{LINKAM}:TST_STRESS",      # Stress
# ]
# @archived("linkam_archiver_record.csv", pv_list=linkam_pvs)
# def run_linkam_steps():
#     LThermal.run_step(0)

# custom_pvs = [
#     "XF:11BMB-ES{Chm:Smpl-Ax:X}Mtr.RBV",            # X
#     "XF:11BMB-ES{Chm:Smpl-Ax:Y}Mtr.RBV",       # Y
#     "XF:11BMB-ES{Chm:Smpl-Ax:theta}Mtr.RBV",      # theta
# ]
# @archived("linkam_archiver_record.csv", pv_list=custom_pvs)
# def run_custom_steps():
#     sam.measureIncidentAngles(angles = [0, 0.05, 0.1], exposure_time = 1)
