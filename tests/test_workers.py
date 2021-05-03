import logging
from glob import glob
from queue import Queue
import sys
from pathlib import Path

from live2p.utils import ptoc, tic, get_true_mm3d_range
from live2p.offline import prepare_init
from live2p.workers import RealTimeQueue

# logging setup
# change for more or less information...
caiman_loglevel = logging.ERROR
live2p_loglevel = logging.ERROR

# changes how logs/updates are printed
logformat = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
logging.basicConfig(level=caiman_loglevel, format=logformat, style='{') #sets caiman loglevel
logger = logging.getLogger('live2p')
logger.setLevel(live2p_loglevel) # sets live2p debug level

# experiment info
# put the makeMasks3D image mat file in the folder with your data
if sys.platform == 'linux':
    tiff_folder = '/mnt/e/caiman_scratch/test_data/ori/data'
else:
    tiff_folder = 'e:/caiman_scratch/test_data/ori/data'

nplanes = 1 # for running multiple planes
plane = 0 # index starts at 0 (for single plane)
fr = 6.36

# x_start and x_end need to be the same or larger than what is in mm3d
# x_start = 110
# x_end = 512-110
# we can auto-determine them now...
# but note: if the stim/vis artifact is in the cropped range, there will be problems
# with motion correction and/or F extraction
mm3d_path = glob(tiff_folder + '/*.mat')[0]
x_start, x_end = get_true_mm3d_range(mm3d_path)
print(f'makeMasks3D range determine to be: {x_start} to {x_end} (pixels)')

# pre-allocated frame buffer, per plane
max_frames = 30000

n_init = 500

params = {
    'fr': fr,
    'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
    'nb': 3,  # background compenents -> nb: 3 for complex
    'decay_time': 1.0,  # sensor tau
    'gSig': (7, 7),  # expected half size of neurons in pixels, very important for proper component detection
    'init_method': 'seeded',
    'motion_correct': True,
    'expected_comps': 300,
    'update_num_comps': False,
    'update_freq': 100,
    'niter_rig': 2,
    'pw_rigid': False,
    'dist_shape_update': False,
    'normalize': True,
    'sniper_mode': False,
    'test_both': False,
    'ring_CNN': False,
    'simultaneously': True,
    'use_cuda': False,
}

def _prepare_test_init(plane):
    q = Queue()
    tiff_files = Path(tiff_folder).glob('*.tif*')
    init_list, nchannels, nplanes, _ = prepare_init(plane, n_init, tiff_files)
    return init_list, plane, nchannels, nplanes, params, q

init = _prepare_test_init(plane)
    
def test_no_init():
    try:
        worker = RealTimeQueue(*init, num_frames_max=max_frames, 
                           Ain_path=mm3d_path, xslice=slice(x_start, x_end), no_init=True)
        print('OK... RealTimeWorker ran __init__ without OnACID initialization.')
    except:
        print('*** FAILED: pycuda ImportError ***')
        raise
    
def test_class_init():
    try:
        worker = RealTimeQueue(*init, num_frames_max=max_frames, 
                           Ain_path=mm3d_path, xslice=slice(x_start, x_end), no_init=False)
        
        print('OK... RealTimeWorker default initialized from tiffs successfullly.')
    except:
        print('*** FAILED: RealTimeWorker did not initialize or OnACID initialization failed. ***')
        raise
    
def test_onacid_init_from_tiffs():
    try:
        worker = RealTimeQueue(*init, num_frames_max=max_frames, 
                           Ain_path=mm3d_path, xslice=slice(x_start, x_end), no_init=True)
        init_mmap = worker.make_init_mmap()
        acid = worker.initialize(init_mmap)
        print('OK... RealTimeWorker initialized from tiffs successfullly.')
    except:
        print('*** FAILED: RealTimeWorker OnACID initialization from tiffs failed. ***')
        raise
    
def test_onacid_init_from_file():
    try:
        worker = RealTimeQueue(*init, num_frames_max=max_frames, 
                           Ain_path=mm3d_path, xslice=slice(x_start, x_end), no_init=True)
        acid = worker.initialize_from_file()
        print('OK... RealTimeWorker initialized from hdf5 file (previous init) successfullly.')
    except:
        print('*** FAILED: RealTimeWorker OnACID initialization from hdf5 file (previous init) failed. ***')
        raise
    
def test_all():
    test_no_init()
    test_class_init()
    test_onacid_init_from_tiffs()
    # test_onacid_init_from_file()
    
if __name__ == '__main__':
    test_all()