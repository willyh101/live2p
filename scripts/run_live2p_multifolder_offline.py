import logging
import time
from pathlib import Path

import scipy.io as sio

from live2p.offline import run_plane_offline_multifolder
from live2p.utils import tic, ptoc

# logging setup
# change for more or less information...
caiman_loglevel = logging.INFO
live2p_loglevel = logging.DEBUG

# changes how logs/updates are printed
logformat = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
logging.basicConfig(level=caiman_loglevel, format=logformat, style='{') #sets caiman loglevel
logger = logging.getLogger('live2p')
logger.setLevel(live2p_loglevel) # sets live2p debug level

# IMPORTANT!!!
# put the makeMasks3D image mat file into the ROOT tiff folder

tiff_base = 'x:/ian'
load_path = 'e:/outfiles'

load_list = [
    '210517_I147_outfile.mat',
    '210518_I147_outfile.mat',
    '220127_HB120_outfile.mat',
    '220131_HB120_outfile.mat',
    '220131_HB113_outfile.mat'
]


### sub functions ####
def retrieve_exp_data(outfile_path):
    mat = sio.loadmat(outfile_path)
    date = mat['out'][0]['info'][0]['date'][0][0][0]
    mouse = mat['out'][0]['info'][0]['mouse'][0][0][0]
    fpath = Path(mat['out'][0]['info'][0]['path'][0][0][0])
    epoch_list = fpath.stem.split('_')
    tiff_root = str(Path(tiff_base, mouse, date))
    return tiff_root, epoch_list
    

def do_offline_expt(tiff_root, epoch_list):
    tiff_folders = ['/'.join([tiff_root, e]) for e in epoch_list]

    nplanes = 3 # for running multiple planes
    fr = 6

    # x_start and x_end need to be the same or larger than what is in mm3d
    x_start = 110
    x_end = 512-110
    # we can auto-determine them now...
    # but note: if the stim/vis artifact is in the cropped range, there will be problems
    # with motion correction and/or F extraction
    # mm3d_path = glob(tiff_folder + '/*.mat')[0]
    # x_start, x_end = get_true_mm3d_range(mm3d_path)
    # print(f'makeMasks3D range determine to be: {x_start} to {x_end} (pixels)')

    # pre-allocated frame buffer, per plane
    # make sure this is > than the number of frames in your experiment
    max_frames = 50000

    n_init = 500

    params = {
        'fr': fr,
        'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
        'nb': 3,  # background compenents -> nb: 3 for complex
        'decay_time': 1.,  # sensor tau
        'gSig': (5, 5),  # expected half size of neurons in pixels, very important for proper component detection
        'init_method': 'seeded',
        'motion_correct': True,
        'expected_comps': 500,
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

    add_cells = {
        'only_init':True,
        'rf':None,
        'update_num_comps':True
    }

    # uncomment and use if you want to add cells during the experiment
    # note: this may require re-running the CNMF fit to get trace data for detected cells before they were detected
    # params = {**params, **add_cells}

    # run all planes offline
    # as run_plane_offline is already multi-process, so the simplest way to do this is to run planes sequentially

    t = tic()
    for p in range(nplanes):
        print(f'***** Starting Plane {p} *****')
        run_plane_offline_multifolder(p, tiff_folders, params, x_start, x_end, n_init, max_frames)
        time.sleep(5)
    print('All done!')
    ptoc(t, 'Whole thing took')
    
    
def main():
    pths = [Path(load_path, i) for i in load_list]
    for p in pths:
        print(f'******** Starting Experiment {p} ************')
        tiff_root, epoch_list = retrieve_exp_data(p)
        do_offline_expt(tiff_root, epoch_list)
    
    
if __name__ == '__main__':
    main()