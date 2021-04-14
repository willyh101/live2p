import argparse
import logging
import importlib


def make_args():
    parser = argparse.ArgumentParser()
    
    # add arguments here
    # turns on all debugging, incl websocket package
    parser.add_argument('-d', '--debug', 
                        default=0, 
                        choices=[0,1,2,3],
                        help="""set debugging level. 
                                0 for off, 
                                1 for live2p, 
                                2 for live2p + caiman, 
                                3 for live2p + websockets""")
    
    # specifies the rigfile to use
    parser.add_argument('-r', '--rigfile', 
                        default='frankenscope',
                        help='selects the rigfile to use. just type the name in quotes w/o the .py')
    
    return parser



def main():
    
    # parse args
    parser = make_args()
    args = parser.parse_args()
    
    # handle debug
    debug_dict = {
        'caiman': logging.ERROR,
        'live2p': logging.INFO,
        'websockets': False
    }
    
    if args.debug >= 1:
        # for all cases turn on live2p debugging
        debug_dict.update(live2p=logging.DEBUG)
    elif args.debug == 2:
        debug_dict.update(caiman=logging.DEBUG)
    elif args.debug == 3:
        debug_dict.update(live2p=logging.DEBUG, debug_ws=True)
        
    # get vals from rigfile
    rigfile = importlib.import_module('rig_files.' + args.rigfile)
    
    # loggformat
    logformat = rigfile.LOGFORMAT
    logging.basicConfig(level=debug_dict['caiman'], format=logformat, style='{') #sets caiman loglevel
    logger = logging.getLogger('live2p')
    logger.setLevel(debug_dict['live2p'])
    
    # start it
    rigfile.start_live2p()

    
if __name__ == '__main__':
    main()