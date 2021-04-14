import logging
from live2p.server import Live2pServer
from importlib_metadata import version


### ----- THINGS YOU HAVE TO CHANGE! ----- ###
# Set these first to match makeMasks3D!!!
# I recommend using removing 110 pixels from each side. Maybe 120 for holography. Maybe less for vis stim. But 
# it has to match whatever you did in MakeMasks3D.
# also set the max number of frames you expect, is an upper limit so it can be really high (used for memory allocation)
x_start = 120
x_end = 512-120

max_frames = 20000

# choose one
mode = 'seeded' # or 'unseeded' but also untested

### ----- THINGS YOU PROBABLY DON'T NEED TO CHANGE ----- ###
# makeMasks3D path
# in most cases it can live in a central folder, but you could also specify
template_path = 'D:/live2p_temp/template/makeMasks3D_img.mat'

# extra trimming options if you want them but I haven't adjusted the output locs
# for them so it could be weird
y_start = 0
y_end = 512

# networking options
# this computers IP (should be static at 192.168.10.104)
# the corresponding IP addresses in networking.py must match exactly
# you could also use 'localhost' if not sending any info from the DAQ
IP = 'localhost'
PORT = 6000

# path to caiman data output folder on server, doesn't need to change as long as the server is there
# (it doesn't have to be a server folder, is just convenient for transferring to the DAQ)
# outputs are also save in the epoch folder with your tiffs
output_folder = 'F:/live2p_out'

# motion correction params
dxy = (1.5, 1.5) # spatial resolution in x and y in (um per pixel)
max_shift_um = (12., 12.) # maximum shift in um
patch_motion_xy = (100., 100.) # patch size for non-rigid correction in um

# CNMF params
background = 3 # number of background components (default, 2 or 3).
# a bigger number here decreases the background but too much can reduce the signal

# logging level (print more or less processing info)
# change logger.setLevel(logging.DEBUG) for more or logger.setLevel(logging.INFO) for less
LOGFORMAT = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
logging.basicConfig(level=logging.ERROR, format=LOGFORMAT, style='{')
logger = logging.getLogger('live2p')
logger.setLevel(logging.DEBUG) # more
# logger.setLevel(logging.INFO) # less


# caiman specific
# some specified earlier, can make more changes here

params_seeded = {
    'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
    'nb': background,  # background compenents -> nb: 3 for complex
    'decay_time': 1.0,  # sensor tau
    'gSig': (7, 7),  # expected half size of neurons in pixels, very important for proper component detection
    'init_method': 'seeded', # or 'cnmf'
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
}

params_undseeded = {
    'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
    'nb': background,  # background compenents -> nb: 3 for complex
    'decay_time': 1.0,  # sensor tau
    'gSig': (7, 7),  # expected half size of neurons in pixels, very important for proper component detection
    'init_method': 'bare',
    'motion_correct': True,
    'expected_comps': 750,
    'update_num_comps': True,
    'update_freq': 100,
    'niter_rig': 2,
    'pw_rigid': False,
    'dist_shape_update': False,
    'normalize': True,
    'sniper_mode': False,
    'test_both': False,
    'ring_CNN': False,
    'simultaneously': True,
}


def assign_params(mode):
    if mode == 'seeded':
        params = params_seeded
    elif mode == 'unseeded':
        params = params_undseeded
    else:
        raise NotImplementedError('Not a mode! You can choose seeded or unseeded.')
    return params


def start_live2p():
    params = assign_params(mode)
    Live2pServer(IP, PORT,  params, 
                 output_folder = output_folder,
                 Ain_path = template_path,
                 yslice = slice(y_start, y_end),
                 num_frames_max=max_frames
                 )

# run everything
if __name__ == '__main__':
    start_live2p()