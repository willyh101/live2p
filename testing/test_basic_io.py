import json
from ..server import Live2pServer
from ..server import Alert

test_params = {
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

serve = {
    'ip': 'localhost',
    'port': 5010,
    'output_folder': 'test_fake',
    'params': test_params,
    'Ain_path': None,
}


class TestServer(Live2pServer):
    
    async def route(self, payload):
        data = json.loads(payload)
        
        try:
            event_type = data.pop('EVENTTYPE') 
        except KeyError:
            Alert('No event type specified.', 'error')
           
            
        ###-----Route events and data here-----###
        if event_type == 'ACQDONE':
            print('ACQDONE')
                       
        elif event_type == 'SESSIONDONE':
            print('SESSIONDONE')
            
        elif event_type == 'SETUP':
            print('SETUP')
        
        
        ##-----Other useful messages-----###
        elif event_type == 'UHOH':
            print('UHOH')
            Alert('Forced quit from SI.', 'error')
            self.loop.stop()
    
        else:
            Alert(f'EVENTTYPE: {event_type} does not exist. Check server routing.')

def test_run_ws_server():
    s = TestServer(**serve)
    
    
if __name__ == '__main__':
    test_run_ws_server()