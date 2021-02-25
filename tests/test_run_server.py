import asyncio
import json
import logging
from datetime import datetime
from glob import glob
from pathlib import Path

import websockets
from live2p.server import Live2pServer

ip = 'localhost'
port = 7777
folder = 'e:/caiman_scratch/ori_20210209_seed'
data_folder = 'e:/caiman_scratch/ori_20210209'
nplanes = 3
nchannels = 2
mm3d_path = glob(data_folder+'/*.mat')[0]


# LOGFILE = folder + '/caiman/out/pipeline_test.log'
LOGFORMAT = '{relativeCreated:08.0f} - {levelname:8} - [{module}:{funcName}:{lineno}] - {message}'
# logging.basicConfig(level=logging.ERROR, format=LOGFORMAT, filename=LOGFILE, style='{')
logging.basicConfig(level=logging.ERROR, format=LOGFORMAT, style='{')
logger = logging.getLogger('live2p')
logger.setLevel(logging.DEBUG)


test_params_undseeded = {
    'fr': 6.36,
    'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
    'nb': 2,  # background compenents -> nb: 3 for complex
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

test_params_seeded = {
    'fr': 6.36,
    'p': 1,  # deconv 0 is off, 1 is slow, 2 is fast
    'nb': 2,  # background compenents -> nb: 3 for complex
    'decay_time': 1.0,  # sensor tau
    'gSig': (7, 7),  # expected half size of neurons in pixels, very important for proper component detection
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
}

server_settings = {
    'ip': ip,
    'port': port,
    'output_folder': 'test_fake',
    'params': test_params_seeded ,
    'Ain_path': mm3d_path,
    'use_prev_init': False,
    'xslice': slice(110,512-110)
}

def test_run_server():
    serve = Live2pServer(**server_settings)
    
def test_send_setup():
    async def send():
        #setup
        async with websockets.connect(f'ws://{ip}:{port}') as websocket:
            out = {
                'EVENTTYPE':'SETUP',
                'nchannels': nchannels,
                'nplanes': nplanes,
                'fr': 6.36,
                'folder': folder
            }
            await websocket.send(json.dumps(out))
        
    asyncio.get_event_loop().run_until_complete(send())
    
    
def test_send_data(rate):
    async def send():
        async with websockets.connect(f'ws://{ip}:{port}') as websocket:
            all_tiffs = Path(data_folder).glob('*.tif*')
            for f in all_tiffs:
                print(f'Sent tiff {f}')
                out = {
                    'EVENTTYPE':'ACQDONE',
                    'filename': str(f)
                }
                out = json.dumps(out)
                await websocket.send(out)
                await asyncio.sleep(rate)

            # stop
            out = {
                'EVENTTYPE': 'SESSIONDONE'
            }
            await websocket.send(json.dumps(out))
            
    asyncio.get_event_loop().run_until_complete(send())   
         
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print('Last frame (a stop frame) sent at: ', current_time)
    
    
    
if __name__ == '__main__':
    test_run_server()
