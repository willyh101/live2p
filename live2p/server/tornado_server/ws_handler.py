import json
import asyncio
import queue
import warnings

import tornado.websocket
import tornado.ioloop


from ...utils import slice_movie
from live2p.server import Alert
from ...workers import Worker
from live2p.server.models import Experiment

warnings.filterwarnings(
    action='ignore',
    lineno=1969, 
    module='scipy')

warnings.filterwarnings(
    action='ignore',
    lineno=1963, 
    module='scipy')

class WSHandler(tornado.websocket.WebSocketHandler):
    
    def __init__(self, output_folder, params, Ain_path, num_frames_max):
        super().__init__()
        
        self.expt = Experiment(output_folder, params, Ain_path, num_frames_max)
        self.loop = tornado.ioloop.IOLoop.current()
        self.qs = []
        self.workers = None
        
    def on_message(self, payload):
        self.route(payload)
        
    def route(self, payload):
        """
        Route the incoming message to the appropriate consumer/message handler. Incoming
        data should be a JSON that is parsed into a Python dictionary (aka MATLAB struct). You can 
        add new routes here that correspond to websocket or tcp socket events from MATLAB. All
        events need at least an 'EVENTTYPE' field.
        
        To define a new event type route:
            1.) Define an async function in this class.
            2.) Add it below as an 'elif' event_type=='YOUREVENT' and await the result of your
                new function.
                
        
        EVENT TYPES:
        ===========
        
        ACQDONE -> triggered on trial ends (acqDone), puts  the named tiff into the processing
                   queue, calls 'self.put_tiff_frames_in_queue()'
                   
        SESSIONDONE -> triggered when ScanImage is done (acqAbort), puts a stop signal in the
                       processing queue and waits for the queues to complete. since we are awaiting
                       the future results of the queues, server will wait for queues to finish and
                       then do final processing before shutting down. call 'self.stop_queues()'
                       
        SETUP ->
        
        

        Args:
            payload (str): incoming string, formatted as a JSON
        """
        data = json.loads(payload)
        
        try:
            event_type = data.pop('EVENTTYPE') 
        except KeyError:
            Alert('No event type specified.', 'error')
           
            
        ###-----Route events and data here-----###
        if event_type == 'ACQDONE':
            self.put_tiff_frames_in_queue()
                       
        elif event_type == 'SESSIONDONE':
            self.stop_queues()
            
        elif event_type == 'SETUP':
            self.handle_setup(**data)
        
        
        ##-----Other useful messages-----###
        # elif event_type == 'UHOH':
        #     Alert('Forced quit from SI.', 'error')
        #     self.loop.stop()
    
        else:
            Alert(f'EVENTTYPE: {event_type} does not exist. Check server routing.')
                
            
    async def handle_setup(self, data):
        """Handle the initial setup data from ScanImage."""
        
        Alert('Recieved setup data from SI', 'success')
        
        # update the experiment with the incoming data
        self.expt.update(data)
        
        # spawn queues and workers (without launching queue)
        self.workers = [self.start_worker(p) for p in range(self.nplanes)]
        
        # finished setup, ready to go
        Alert("Ready to process online!", 'success')
        
        # run the queues
        await self.run_queues()
                
    async def run_queues(self):
        # start the queues on their loop and wait for them to return a result
        tasks = [self.loop.run_in_executor(None, w.process_frame_from_queue) for w in self.workers]
        results = await asyncio.gather(*tasks)
        
        # from here do final analysis
        # results will be a list of dicts
        Alert('Processing and saving final data.', 'info')
        self.expt.process_and_save(results)
        
        # Return True to release back to main loop
        # return True
        
        # or stop the loop when it's all over
        Alert('Live2p finished. Shutting down server.', 'success')
         
    def start_worker(self, plane):
        self.qs.append(queue.Queue())
        Alert(f'Starting RealTimeWorker {plane}', 'info')
        worker = Worker(self.files, plane, self.nchannels, self.nplanes, self.opts, self.qs[plane],
                                num_frames_max=self.num_frames_max, Ain_path=self.Ain_path, **self.kwargs)
        return worker

    async def put_tiff_frames_in_queue(self):
        # added sleep because last tiff isn't closed in time I think
        await asyncio.sleep(0.5)
        tiff = self.get_last_tiff()
        for p in range(self.nplanes):
            mov = slice_movie(str(tiff), x_slice=None, y_slice=None, t_slice=slice(p*self.nchannels,-1,self.nchannels*self.nplanes))
            if p==0:
                # only want to do this once per tiff!
                self.lengths.append(mov.shape[0])
            for f in mov:
                f_ = f.astype('float32')
                self.qs[p].put_nowait(f_.squeeze())
    
    async def stop_queues(self):
        Alert('Recieved acqAbort. Workers will continue running until all frames are completed.', 'info')
        for q in self.qs:
            q.put_nowait('STOP')
