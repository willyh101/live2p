from live2p.start_live2p import start_live2p

### ----- THINGS YOU HAVE TO CHANGE! ----- ###
# Set these first to match makeMasks3D!!!
# I recommend using removing 110 pixels from each side. Maybe 120 for holography. Maybe less for vis stim. But 
# it has to match whatever you did in MakeMasks3D.
# also set the max number of frames you expect, is an upper limit so it can be really high (used for memory allocation)
x_start = 120
x_end = 512-120

# choose one
mode = 'seeded' # or 'unseeded' but also untested

# makeMasks3D path
# in most cases it can live in a central folder, but you could also specify
template_path = 'D:/live2p_temp/template/makeMasks3D_img.mat'


### ----- THINGS YOU PROBABLY DON'T NEED TO CHANGE ----- ###

# extra trimming options if you want them but I haven't adjusted the output locs
# for them so it could be weird
y_start = 0
y_end = 512

# pre-allocated frame buffer
max_frames = 200000

# networking options
# this computers IP (should be static at 192.168.10.104)
# the corresponding IP addresses in networking.py must match exactly
# you could also use 'localhost' if not sending any info from the DAQ
ip = '192.168.10.104'
port = 6000

# path to caiman data output folder on server, doesn't need to change as long as the server is there
# (it doesn't have to be a server folder, is just convenient for transferring to the DAQ)
# outputs are also save in the epoch folder with your tiffs
output_folder = 'F:/live2p_out'

# motion correction params
dxy = (1.5, 1.5) # spatial resolution in x and y in (um per pixel)
max_shift_um = (10., 10.) # maximum shift in um
patch_motion_xy = (100., 100.) # patch size for non-rigid correction in um

# CNMF params
background = 3 # number of background components (default, 2 or 3).
# a bigger number here decreases the background but too much can reduce the signal

# logging level (print more or less processing info)
# 0 is no debug (INFO for live2p and ERROR for caiman)
# 1 is debug live2p
# 2 is live2p + caiman
# 3 is live2p + websockets
log_level = 1


# caiman specific
# some specified earlier, can make more changes here

seeded = {
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

undseeded = {
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

server_settings = {
    'ip': ip,
    'port': port,
    'output_folder': output_folder,
    'Ain_path': template_path,
    'xslice': slice(x_start, x_end),
    'yslice': slice(y_start, y_end),
    'num_frames_max': max_frames,
}

# run everything
if __name__ == '__main__':
    params = locals()[mode]
    start_live2p(params_dict=params, debug_level=log_level, **server_settings)