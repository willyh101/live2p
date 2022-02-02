import logging
import os
import warnings
import json
from pathlib import Path
from datetime import datetime

import numpy as np
from ScanImageTiffReader import ScanImageTiffReader

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    import caiman as cm
    from caiman.source_extraction.cnmf.online_cnmf import OnACID
    from caiman.source_extraction.cnmf.params import CNMFParams

from .utils import format_json, make_ain, tic, toc, tiffs2array, tictoc
from .analysis.spatial import find_com

logger = logging.getLogger('live2p')


class Worker:
    """Base class for workers that process data (usually by slicing out planes)."""
    
    def __init__(self, files, plane, nchannels, nplanes, params):
        """
        Base class for implementing live2p. Don't call this class directly, rather call or
        make a subclass.

        Args:
            files (list): list of files to process
            plane (int): plane number to process, serves a slice through each tiff
            nchannels (int): total number of channels total, helps slicing ScanImage tiffs
            nplanes (int): total number of z-planes imaged, helps slicing ScanImage tiffs
            params (dict): caiman params dict
        """
        self.files = files
        self.plane = plane
        self.nchannels = nchannels
        self.nplanes = nplanes
        
        # setup the params object
        logger.debug('Setting up params...')
        self._params = CNMFParams(params_dict=params)
        
        self.data_root = Path(self.files[0]).parent
        self.caiman_path = Path()
        self.temp_path = Path()
        self.all_path = Path()
        self._setup_folders()
        
        # these get set up by _start_cluster, called on run so workers can be queued w/o 
        # ipyparallel clusters clashing
        self.c = None # little c is ipyparallel related
        self.dview = None
        self.n_processes = None
        
    @property
    def params(self):
        return self._params
    
    @params.setter
    def params(self, params):
        if isinstance(params, dict):
            self._params = CNMFParams(params_dict=params)
        elif isinstance(params, CNMFParams):
            self._params = params
        else:
            raise ValueError('Please supply a dict or cnmf params object.')
        
    def __del__(self):
        self._stop_cluster()
        logger.debug('Worker object destroyed on delete.')
        
    def _start_cluster(self, **kwargs):
        # get default values if not specified in kwargs
        kwargs.setdefault('backend', 'local')
        kwargs.setdefault('n_processes', os.cpu_count()-2) # make room for matlab
        kwargs.setdefault('single_thread', False)
        
        for key, value in kwargs.items():
            logger.debug(f'{key} set to {value}')
        
        logger.debug('Starting local cluster.')
        try:
            self.c, self.dview, self.n_processes = cm.cluster.setup_cluster(**kwargs)
        except:
            logger.error("Local ipyparallel cluster already working. Can't create another.")
            raise
        logger.debug('Local cluster ready.')
        
    def _stop_cluster(self):
        try:
            cm.stop_server(dview=self.dview)
            logger.debug('Cluster stopped.')
        except:
            logger.warning('No cluster to shutdown.')
                
    def _setup_folders(self):
        existing_folders = sorted(self.data_root.glob('live2p*'))
        if len(existing_folders) > 0:
            logger.debug('Found existing live2p folder.')
            num_existing = len(existing_folders)
            live2p_folder = self.data_root/f'live2p_{num_existing+1:03}'
        else:
            live2p_folder = self.data_root/'live2p'
        
        self.temp_path = live2p_folder/'tmp'
        self.out_path = live2p_folder/'out'
            
        self.temp_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f'Set temp_path to {self.temp_path}')
        
        self.out_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f'Set out_path to {self.out_path}')
        
        # set the CWD to the temp path
        os.chdir(self.temp_path)
        logger.debug(f'Set working dir to {self.temp_path}')
        
    def _validate_tiffs(self, bad_tiff_size=5):
        """
        Finds the weird small tiffs and removes them. Arbitrarily set to <5 frame because it's not too
        small and not too big. Also gets the lengths of all good tiffs.

        Args:
            bad_tiff_size (int, optional): Size tiffs must be to not be trashed. Defaults to 5.
        """
        
        crap = []
        lengths = []
        
        for tiff in self.files:
            with ScanImageTiffReader(str(tiff)) as reader:
                data = reader.data()
                if data.shape[0] < bad_tiff_size:
                    # remove them from the list of tiffs
                    self.files.remove(tiff)
                    # add them to the bad tiff list for removal from HD
                    crap.append(tiff)
                else:
                    # otherwise we append the length of tiff to the lengths list
                    lengths.append(data.shape[0])             
        for crap_tiff in crap:
            os.remove(crap_tiff)
            
        self.splits = (np.array(lengths) / (self.nchannels * self.nplanes)).astype(np.int)
    
    def cleanup_tmp(self, ext='*'):
        """
        Deletes all the files in the tmp folder.

        Args:
            ext (str, optional): Removes files with given extension. Defaults to '*' (all extensions).
        """
        
        files = self.temp_path.glob('*.' + ext)
        for f in files:
            try:
                # try to remove the file
                f.unlink()
            except:
                # warn if the file is still in use
                logger.warning(f'Unable to remove file: {f}')
                
                
                    
class RealTimeQueue(Worker):
    """Processing queue for real-time CNMF (OnACID)."""
    def __init__(self, files, plane, nchannels, nplanes, params, q, 
                 num_frames_max=10000, Ain_path=None, no_init=False, **kwargs):

        super().__init__(files, plane, nchannels, nplanes, params)

        self.q = q
        self.num_frames_max = num_frames_max
        logger.debug(f'Max frames set to {self.num_frames_max}')
        
        # set slicing
        self.tslice = kwargs.get('tslice', slice(plane*nchannels, None, nchannels * nplanes))
        self.xslice = kwargs.get('xslice', slice(0, 512))
        self.yslice = kwargs.get('yslice', slice(0, 512))

        # look for Ain
        if isinstance(Ain_path, str):
            self.Ain = make_ain(Ain_path, plane, self.xslice.start, self.xslice.stop)
        else:
            self.Ain = None
        
        # other options
        self.use_CNN = False
        self.update_freq = 500
        self.use_prev_init = kwargs.get('use_prev_init', False)
        
        # setup initial parameters
        self.t = 0 # current frame is on
        self.live_frame_count = 0
        self.trial_starts = []
        self.trial_ends = []
        self.trial_lengths = []
        
        # placeholders
        self.acid = None
        
        # extra pathing for realtime
        # add folder to hold inits
        self.init_fname = f'realtime_init_plane_{self.plane}.hdf5'
        # self.init_dir = self.data_root.parent/'live2p_init' # moved to tmp folder
        self.init_dir = self.temp_path
        self.init_path = self.init_dir/self.init_fname
        
        
        logger.info('Starting live2p worker.')
        
        if not no_init:
            # use_prev_init is not fully working yet
            self.initialize_onacid()
        else:
            logger.info('Skipping OnACID initialization.')

    def initialize_onacid(self):
        if self.use_prev_init:
            logger.warning('Using a previous initialization is not yet supported. Setting use_prev_init = False.')
            self.use_prev_init = False
        # run OnACID initialization if needed,            
        # check for the fname so it's organized by plane
        if self.init_path.exists() and self.use_prev_init:
            self.acid = self._initialize_from_file()
        # or do the init        
        else:
            logger.info(f'Starting new OnACID initialization for live2p.')
            init_mmap = self.make_init_mmap()
            self.acid = self._initialize_new(init_mmap)
        
    def make_init_mmap(self):
        logger.debug('Making init memmap...')
        self.init_dir.mkdir(exist_ok=True, parents=True)
        self._validate_tiffs()
        mov = tiffs2array(movie_list=self.files, 
                          x_slice=self.xslice, 
                          y_slice=self.yslice,
                          t_slice=self.tslice)
        
        self.frame_start = mov.shape[0] + 1
        self.t = mov.shape[0] + 1
        
        self.params.change_params(dict(init_batch=mov.shape[0]))
        m = cm.movie(mov.astype('float32'))
        
        save_path = f'initplane{self.plane}.mmap'
        
        init_mmap = m.save(save_path, order='C')
        
        logger.debug(f'Init mmap saved to {init_mmap}.')
        
        return init_mmap
    
    @tictoc
    def _initialize_new(self, fname_init):
        """
        Initialize OnACID from a tiff to generate initial model. Saves CNMF/OnACID object
        into ../live2p_init. Runs the initialization specified in params ('bare', 'seeded', etc.).

        Args:
            fname_init (Path-like): Path or str to tiff to initalize from

        Returns:
            initialized OnACID object
        """
        
        # change params to use new mmap as init file
        self.params.change_params(dict(fnames=str(fname_init)))

        # setup caiman object
        acid = OnACID(dview=None, params=self.params)
        acid.estimates.A = self.Ain
        
        # do initialization
        acid.initialize_online(T=self.num_frames_max)
        
        # save for next time to init path
        # need to update acid object for loading from init
        self.save_acid(acid_obj=acid, fname=self.init_path)
        
        logger.debug('OnACID initialized.')
        
        return acid
    
    @tictoc
    def _initialize_from_file(self):
        """
        Initialize OnACID from a previous initialization or full OnACID session (not yet
        implemented).
        
        Need to prepare object with Yr and T.

        Returns:
            initialized OnACID object
        """
        
        logger.info(f'Loading previous OnACID initialization from {self.init_path}.')
        
        # load
        acid = self.load_acid(self.init_path)
        
        # mmap path has to be globbed
        mmap_path_glob = list(self.init_dir.glob(f'initplane{self.plane}*.mmap'))
        
        if len(mmap_path_glob) == 0:
            logger.error('Initialization folder has no mmap file. Running init from scratch.')
            return self._initialize_new()
        
        elif len(mmap_path_glob) > 1:
            logger.error('Multiple matching mmap files found. There can only be one per plane. Starting init from scratch.')
            return self._initialize_new()
        
        mmap_path = str(mmap_path_glob[0])
        Yr, dims, T = cm.load_memmap(mmap_path)
        
        # set frame counters
        acid._prepare_object(Yr, T)
        init_batch = acid.params.online['init_batch']
        self.frame_start = init_batch + 1
        self.t = init_batch + 1
        
        return acid
    
    def process_frame_from_queue(self):
        """
        The main loop. Pulls data from the queue and processes it, fitting data to the model. Stops
        upon recieving a 'STOP' string.

        Returns:
            json representation of the OnACID model
        """
        
        frame_time = []
        while True:
            frame = self.q.get()
            
            ###-----FRAME DATA-----###
            if isinstance(frame, np.ndarray):
                
                t = tic()
                
                frame_ = frame[self.yslice, self.xslice].copy().astype(np.float32)
                frame_cor = self.acid.mc_next(self.t, frame_)
                self.acid.fit_next(self.t, frame_cor.ravel(order='F'))
                
                # update counters
                self.t += 1
                self.live_frame_count += 1
                
                frame_time.append(toc(t))
                
                if self.t % self.update_freq == 0:
                    logger.info(f'Total of {self.t} frames processed. (Queue {self.plane})')
                    # calculate average time to process
                    mean_time = np.mean(frame_time) * 1000 # in ms
                    mean_hz = round(1/np.mean(frame_time),2)
                    logger.info(f'Average processing time: {int(mean_time)} ms. ({mean_hz} Hz) (Queue {self.plane})')
            
            ###-----STOP PROCESSING-----###
            elif isinstance(frame, str):
                if frame == 'TRIAL START':
                    # will reflect the actual start frame of a trial
                    # add one as it has not been incr. yet
                    self.trial_starts.append(self.t + 1) 
                
                elif frame == 'TRIAL END':
                    # will reflect the last frame + 1 of a trial (eg. for exclusive slicing)
                    # add one as it has not been incr. yet
                    self.trial_ends.append(self.t + 1)
                    trial_length = self.trial_ends[-1] - self.trial_starts[-1]
                    self.trial_lengths.append(trial_length)
                    
                elif frame == 'STOP':                 
                    logger.info('Stopping live2p....')
                    now = datetime.now()
                    current_time = now.strftime("%H:%M:%S")
                    logger.debug(f'Processing done at: {current_time}')
                    logger.info('Getting final results...')

                    self.update_acid()
                    
                    # save
                    try:
                        self.save_acid()
                    except Exception:
                        # need to catch exception here because we want to complete the future and
                        # process the final data
                        logger.exception('Error with saving OnACID hdf5.')
                        
                    # self.save_json()
                    data = self._model2dict()

                    break 
                
                else:
                    logger.warning(f"Queue got str message '{frame}' does not have a matching method.")
                    continue         
                 
        return data
                
    def update_acid(self, **kwargs):
        # ! THIS ISN'T ACTUALLY CALLED ANYWHERE AND NO KWARGS ARE PASSED
        for k,v in kwargs.items():
            setattr(self.acid.estimates, k, v)
    
    def get_model(self):
        model_dict = {
            # A = spatial component (cells)
            'A': self.acid.estimates.Ab[:, self.acid.params.get('init', 'nb'):].toarray(),
            # b = background components (neuropil)
            'b': self.acid.estimates.Ab[:, :self.acid.params.get('init', 'nb')].toarray(),
            # C = denoised trace for cells
            'C': self.acid.estimates.C_on[self.acid.params.get('init', 'nb'):self.acid.M, self.frame_start:self.t],
            # f = denoised neuropil signal
            'f': self.acid.estimates.C_on[:self.acid.params.get('init', 'nb'), self.frame_start:self.t],
            # nC a.k.a noisyC very close to the raw F trace
            'nC': self.acid.estimates.noisyC[self.acid.params.get('init', 'nb'):self.acid.M, self.frame_start:self.t],
            # frame shifts, keep as list
            'shifts': np.array(self.acid.estimates.shifts)[self.frame_start:,:]
        }
        # YrA = signal noise, important for dff calculation
        # computed from nC and C so do add to dict
        YrA = model_dict['nC'] - model_dict['C']
        model_dict['YrA'] = YrA
        
        return model_dict
    
    def _model2dict(self):
        model = self.get_model()
        model = format_json(**model)
        
        coords = find_com(model['A'], self.acid.estimates.dims, self.xslice.start)
        dims = self.acid.estimates.dims
        
        data = {
            'plane': int(self.plane),
            't': self.t,
            'CoM':coords.tolist(),
            'dims':dims,
            'trial_lengths': self.trial_lengths,
        }
        
        data.update(model)
        
        return data
 
    def save_json(self, fname='realtime'):
        data = self._model2dict()
        fname += f'_plane_{self.plane}.json'
        save_path = self.out_path/fname
        with open(save_path, 'w') as f:
            json.dump(data, f)
        logger.info(f'Saved JSON to {str(save_path)}')
        
    def save_acid(self, acid_obj=None, fname=None):
        if fname is None:
            fname = f'realtime_results_plane_{self.plane}.hdf5'
            
        if acid_obj is None:
            acid_obj = self.acid
            
        save_path = str(self.out_path/fname)                 
        acid_obj.save(save_path)
        logger.info(f'Saved OnACID hdf5 to {save_path}')
        
    def load_acid(self, filepath):
        logger.info('Loading existing OnACID object file.')
        return cm.source_extraction.cnmf.online_cnmf.load_OnlineCNMF(filepath)