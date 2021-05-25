import logging
import warnings
from importlib_metadata import version
from sklearn.exceptions import ConvergenceWarning

warnings.simplefilter('ignore', category=ConvergenceWarning)
warnings.simplefilter('ignore', category=DeprecationWarning)

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 6000

def start_live2p(params_dict, debug_level, ip=DEFAULT_IP, port=DEFAULT_PORT, **kwargs):
    # welcome the user
    msg = f"""
    
    Welcome to live2p (v{version('live2p')})!

* Realtime, multiplane motion correction and source extraction using CaImAn OnACID, ScanImage, and websockets.

* A popup GUI will ask you to select you seed image by default.
* The seed image should be ~500 frames and will take ~ 30 seconds to process before you start the experiment.

Loading...

"""

    print(msg)
    
    from live2p.websockets.server import Live2pServer


    # handle debug
    debug_dict = {
        'caiman': logging.ERROR,
        'live2p': logging.INFO,
        'websockets': False
    }
    
    if debug_level >= 1:
        # for all cases turn on live2p debugging
        debug_dict.update(live2p=logging.DEBUG)
    elif debug_level == 2:
        debug_dict.update(caiman=logging.DEBUG)
    elif debug_level == 3:
        debug_dict.update(live2p=logging.DEBUG, debug_ws=True)
    
    
    # loggformat
    logformat = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
    logging.basicConfig(level=debug_dict['caiman'], format=logformat, style='{') #sets caiman loglevel
    logger = logging.getLogger('live2p')
    logger.setLevel(debug_dict['live2p'])
    
    
    # start server
    Live2pServer(ip, port, params=params_dict, **kwargs)