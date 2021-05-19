from live2p.wrappers import run_in_executor
from live2p.workers import RealTimeQueue
from live2p.websockets.core import WebSocketServer
from live2p.alerts import Alert

from pathlib import Path
from live2p.guis import openfilesgui
import logging
import asyncio
import queue
from glob import glob

logger = logging.getLogger('live2p')

init_folder = 'e:/caiman_scratch/ori_20210209_seed'
data_folder = 'e:/caiman_scratch/ori_20210209'



wss = WebSocketServer()
wss.qs = []
wss.use_init_gui = False
wss.Ain_path = glob(data_folder+'/*.mat')[0]
wss.params = {
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
    'use_cuda': False,
}

# @wss.event('SETUP')
# async def run_setup(data):
#     """Handle the initial setup data from ScanImage."""
#     for key, value in data.items():
#         setattr(wss, key, value)
#         Alert(f'{key} set to {value}', 'info')
        
#     tiffs = list(Path(wss.folder).glob('*.tif*'))
    
#     if len(tiffs) == 0 or wss.use_init_gui:
#         # do GUI in seperate thread, openfilesgui should return a list/tuple
#         tiffs = await wss.loop.run_in_executor(None, openfilesgui, 
#                                             Path(wss.folder).parent,
#                                             'Select seed image.')
        
#         # why didn't you select any?
#         if not isinstance(tiffs, tuple):
#             logger.error("You didn't select a file and there were none in the epoch folder. Quitting...")
#             wss._teardown()
            
#     wss.init_files = tiffs
#     tasks = [start_worker(p) for p in range(wss.nplanes)]
    
#     wss.workers = await asyncio.gather(*tasks)
    
#     # finished setup, ready to go
#     Alert("Ready to process online!", 'success')
    
# @run_in_executor
# def start_worker(p):
#     wss.qs.append(queue.Queue())
#     worker = RealTimeQueue(wss.init_files, p, wss.nchannels, wss.nplanes,
#                             wss.params, wss.qs[p], Ain_path=wss.Ain_path)
        
#     return worker
        
if __name__ == '__main__':
    wss.run_server()