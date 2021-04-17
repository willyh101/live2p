import argparse
import importlib
from .start_live2p import start_live2p


def make_args():
    parser = argparse.ArgumentParser()
    
    # add arguments here
    # turns on all debugging, incl websocket package
    parser.add_argument('-d', '--debug', 
                        default=0, 
                        choices=[0,1,2,3],
                        type=int,
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
    
    rigfile = importlib.import_module('rig_files.' + args.rigfile)
    
    params = getattr(rigfile, rigfile.mode)
    
    start_live2p(rigfile.server_settings, params, debug_level=args.debug)

    
if __name__ == '__main__':
    main()