from live2p.server.websockets.server import Live2pServer
from importlib_metadata import version
import logging


def start_live2p(server_settings, params_dict, debug_level, **kwargs):
    # welcome the user
    msg = f"""
    
    Welcome to live2p (v{version('live2p')})!

* Note: to quit out you will probably need to close the console window. Ctrl-C is unlikely to work for now...
* Remember to place your seed image as the only tiff in the current epoch directory!
    
Loading...

"""

    print(msg)


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
    

    