from live2p.workers import RealTimeQueue, Worker
import pytest
import sys
from glob import glob
from live2p.utils import get_true_mm3d_range
from live2p.offline import prepare_init
from queue import Queue
from pathlib import Path



if sys.platform == 'linux':
    tiff_folder = '/mnt/e/caiman_scratch/test_data/ori/data'
else:
    tiff_folder = 'e:/caiman_scratch/test_data/ori/data'

nplanes = 1 # for running multiple planes
plane = 0 # index starts at 0 (for single plane)
fr = 6.36
mm3d_path = glob(tiff_folder + '/*.mat')[0]
x_start, x_end = get_true_mm3d_range(mm3d_path)
print(f'makeMasks3D range determine to be: {x_start} to {x_end} (pixels)')
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

@pytest.fixture
def tiff_path():
    return tiff_folder
    
@pytest.fixture
def live2p_worker():
    q = Queue()
    tiff_files = Path(tiff_folder).glob('*.tif*')
    init_list, nchannels, nplanes, _ = prepare_init(plane, n_init, tiff_files)
    worker = RealTimeQueue(init_list, plane, nchannels, nplanes, params, q, 
                           num_frames_max=max_frames, Ain_path=mm3d_path, 
                           xslice=slice(x_start, x_end), no_init=True)
    return worker

@pytest.fixture
def base_worker():
    tiff_files = Path(tiff_folder).glob('*.tif*')
    init_list, nchannels, nplanes, _ = prepare_init(plane, n_init, tiff_files)
    worker = Worker(init_list, plane, nchannels, nplanes, params)
    return worker