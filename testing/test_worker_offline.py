"""
Tests the worker by using the offline pipeline on all planes. Runs start to end.
"""

import logging
from glob import glob
import sys

from live2p.utils import ptoc, tic, get_true_mm3d_range
from live2p.offline import run_plane_offline

# logging setup
# change for more or less information...
caiman_loglevel = logging.WARNING
live2p_loglevel = logging.DEBUG

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
    'gSig': (5, 5),  # expected half size of neurons in pixels, very important for proper component detection
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

def run_test():
    t = tic()
    data = []
    for p in range(nplanes):
        print(f'***** Starting Plane {p} *****')
        result = run_plane_offline(p, tiff_folder, params, x_start, x_end, n_init, max_frames)
        data.append(result)
    print('All done!')
    ptoc(t,'Whole thing took')
    return result

if __name__ == '__main__':
    run_test()