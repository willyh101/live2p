import argparse
import importlib
import logging
from .start_live2p import start_live2p, DEFAULT_IP, DEFAULT_PORT

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
    
    parser.add_argument('--ip',
                        default=DEFAULT_IP,
                        help='set IP for server to run on.')
    
    parser.add_argument('-p', '--port',
                        type=int,
                        default=DEFAULT_PORT,
                        help='set port for server to run on.')
    
    return parser


def main():
    
    # parse args
    parser = make_args()
    args = parser.parse_args()
    
    rigfile = importlib.import_module('rig_files.' + args.rigfile)
    
    # add cli logger
    logger_cli = logging.getLogger('live2p_cli')
    logformat = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
    logging.basicConfig(level=logging.INFO, format=logformat, style='{') #sets caiman loglevel
    if args.debug > 0:
        logger_cli.setLevel(logging.DEBUG)
    logger_cli.debug(f'Will load settings using rigfile: {args.rigfile}.py')
    
    params = getattr(rigfile, rigfile.mode)
    settings = getattr(rigfile, 'server_settings')
    
    for k, v in settings.items():
        logger_cli.debug(f'{k}: {v}')
    
    settings.pop('ip')
    settings.pop('port')
    
    start_live2p(params_dict=params, debug_level=args.debug, ip=args.ip, port=args.port, **settings)