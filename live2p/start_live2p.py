import logging
import warnings
from importlib_metadata import version
from sklearn.exceptions import ConvergenceWarning

warnings.simplefilter('ignore', category=ConvergenceWarning)
warnings.simplefilter('ignore', category=DeprecationWarning)


def start_live2p(server_settings, params_dict, debug_level, **kwargs):
    # welcome the user
    msg = f"""
    
    Welcome to live2p (v{version('live2p')})!

* A popup GUI will ask you to select you seed image by default.
* Still create a new epoch folder for the tiffs, so the results of live2p don't overwrite themselves if you run it multiple times.

* The seed image should be ~500 frames and will take ~ 30 seconds to process before you start the experiment.

* CTRL-C has been re-enabled, but we are relying on Windows to close ports and threads for now...
* As Windows is Windows, there could be cases in which processes need to be manually closed via task manager.
* The most obvious symptoms would be: 
* 1. Unable to start live2p server due to socket already in use.
* 2. Exceedingly high RAM or CPU usage in the background.
* If this is the case force close any python.exe tasks.

Loading...

"""

    print(msg)
    
    from .server import Live2pServer


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
    Live2pServer(**server_settings, params=params_dict, **kwargs)