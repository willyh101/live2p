import asyncio
import concurrent.futures
import json
import logging
import queue
from pathlib import Path

import numpy as np
import scipy.io as sio
from ScanImageTiffReader import ScanImageTiffReader

from ..alerts import Alert
from ..analysis import process_data
from ..guis import openfilesgui
from ..utils import now
from ..workers import RealTimeQueue

import websockets

logger = logging.getLogger('live2p')

class Live2pServer:
    def __init__(self, ip, port, params, 
                  output_folder=None, Ain_path=None, num_frames_max=10000, 
                  postprocess_kws=None, use_init_gui=True, **kwargs):
        
        self.ip = ip
        self.port = port
        self.url = f'ws://{ip}:{port}'
        self.clients = set()
        
        # if output_folder is not None:
        self.output_folder = Path(output_folder) if output_folder else None
            
        self.params = params
        self.Ain_path = Ain_path     
        self.num_frames_max = num_frames_max
        self.init_files = None
        self.qs = []
        self.workers = None
        self.lengths = []
        self.kwargs = kwargs
        self.postprocess_kws = postprocess_kws
        
        # custom settings
        self.use_init_gui = use_init_gui
        
        # these are assigned by send_setup
        self.folder = None
        self.fr = None
        self.nplanes = 3
        self.nchannels = 2
        
        # these are recieved from the daq
        # self.stim_times = 1
        
        # other logs
        self.trialtimes_all = []
        self.trialtimes_success = []
        
        self.executor = concurrent.futures.ThreadPoolExecutor()
        
        if kwargs.pop('debug_ws', False):
            wslogs = logging.getLogger('websockets')
            wslogs.setLevel(logging.DEBUG)
                
        Alert(f'Starting WS server ({self.url})...', 'success')
        
        self._start_ws_server()
        
        
    def _start_ws_server(self):
        """Starts the WS server."""
        serve = websockets.serve(self.handle_incoming_ws, self.ip, self.port)
        asyncio.get_event_loop().run_until_complete(serve)
        self.server = serve.ws_server
        Alert('Ready to launch!', 'success')
        
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self._wakeup())
        self.loop.set_default_executor(self.executor)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            Alert('KeyboardInterrupt! Shutting down.', 'error')
            self._teardown()
            Alert('Shutdown complete.', 'error')
        
    def _teardown(self):
        self.server.close()
        self.executor.shutdown()
        self.loop.stop()
        
    async def _wakeup(self):
        # enables ctrl-c killing of webserver
        # might be redundant in py>3.8
        while True:
            await asyncio.sleep(1)
        
    async def handle_incoming_ws(self, websocket, path):
        """Handle incoming data via websocket."""
        
        # ! I think this could go in context manager for graceful failures
        async for payload in websocket:
            await self.route(payload)
            
            
    async def route(self, payload):
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
            self.trialtimes_all.append(now())
            await self.put_tiff_frames_in_queue(tiff_name=data.get('filename', None))
            
        elif event_type == 'SESSIONDONE':
            await self.stop_queues()
            
        elif event_type == 'SETUP':
            await self.handle_setup(data)
            
        elif event_type == 'START':
            # since self.run_queues() awaits the results of the long running queues, it needs to
            # scheduled as a co-routine. allows other socket messages to arrive in the socket.
            asyncio.create_task(self.run_queues())
            
        
        ##-----Other useful messages-----###
        
        elif event_type == 'TEST':
            logger.debug('TEST RECVD')
            
        elif event_type == 'UHOH':
            Alert('Forced quit from SI.', 'error')
            self._teardown()
    
        else:
            Alert(f'EVENTTYPE: {event_type} does not exist. Check server routing.')
            
     
    async def handle_setup(self, data):
        """Handle the initial setup data from ScanImage."""
        
        Alert('Recieved setup data from SI', 'success')
        
        # update with the incoming data
        for key, value in data.items():
            setattr(self, key, value)
            Alert(f'{key} set to {value}', 'info')
            
        # either glob the tiffs from the epoch folder or get them from a GUI
        tiffs = list(Path(self.folder).glob('*.tif*'))
        
        # get from GUI pop-up if no tiffs present
        if len(tiffs) == 0 or self.use_init_gui:
            # do GUI in seperate thread, openfilesgui should return a list/tuple
            tiffs = await self.loop.run_in_executor(None, openfilesgui, 
                                             Path(self.folder).parent,
                                             'Select seed image.')
            
            # why didn't you select any?
            if not isinstance(tiffs, tuple):
                logger.error("You didn't select a file and there were none in the epoch folder. Quitting...")
                self.loop.stop()
                
        self.init_files = tiffs
        
        # spawn queues and workers (without launching queue)
        # self.workers = [self.start_worker(p) for p in range(self.nplanes)]
        tasks = [self.loop.run_in_executor(None, self.start_worker, p) for p in range(self.nplanes)]
        self.workers = await asyncio.gather(*tasks)
        
        # finished setup, ready to go
        Alert("Ready to process online!", 'success')
            
                
    async def run_queues(self):
        # start the queues on their loop and wait for them to return a result
        tasks = [self.loop.run_in_executor(None, w.process_frame_from_queue) for w in self.workers]
        results = await asyncio.gather(*tasks)
        
        # from here do final analysis
        # results will be a list of dicts
        Alert('Processing and saving final data.', 'info')
        
        if self.folder is not None:
            # added to make sure in some weird case self.folder doesn't get assigned
            self.process_and_save(results, save_path=self.folder)
        
        if self.output_folder is not None:
            # if not specified, don't save it!
            self.process_and_save(results)
        
        # Return True to release back to main loop
        # return True
        
        # or stop the loop when it's all over
        Alert('Live2p finished. Shutting down server.', 'success')
        self.loop.stop()
         
         
    def start_worker(self, plane):
        self.qs.append(queue.Queue())
        Alert(f'Starting RealTimeWorker {plane}', 'info')
        
        worker = RealTimeQueue(self.init_files, plane, self.nchannels, self.nplanes,
                               self.params, self.qs[plane], Ain_path=self.Ain_path, **self.kwargs)
        return worker

    async def put_tiff_frames_in_queue(self, tiff_name=None):
        # added sleep because last tiff isn't closed in time I think
        await asyncio.sleep(0.5)

        short_tiff_threshold = 15
        
        try:
            # TODO:  fold this into below so there is less opening and closing of tiffs
            if tiff_name is None:
                tiff_name = self.get_last_tiff()
            
            # open data 
            with ScanImageTiffReader(str(tiff_name)) as reader:
                data = reader.data()
            
            # check if valid tiff
            if data.shape[0] > short_tiff_threshold:    
                # first, log trial time
                self.trialtimes_success.append(now())
                # iterate through planes to get lengths and add to queue
                for p in range(self.nplanes):
                    # slice movie for this plane
                    t_slice = slice(p*self.nchannels,-1,self.nchannels*self.nplanes)
                    mov = data[t_slice, :, :]
                    
                    # get lengths for one plane only/once per tiff
                    if p==0:
                        self.lengths.append(mov.shape[0])
                    
                    # add frames to the queue
                    for f in mov:
                        self.qs[p].put_nowait(f.squeeze())

            else:
                logger.warning(f'A tiff that was too short (<{short_tiff_threshold} frames total) was attempted to be added to the queue and was skipped.')
                return
            
        except Exception: # ScanImage can't open file is a generic exception
            # this will skip the last file since we can't open it until ScanImage aborts
            logger.warning('Failed to add tiff to queue. If this was the last acq, this is expected. Otherwise something is wrong.')

    
    # ? does this need to be async??
    async def stop_queues(self):
        Alert('Recieved acqAbort. Workers will continue running until all frames are completed.', 'info')
        for q in self.qs:
            q.put_nowait('STOP')
            
            
    def get_last_tiff(self):
        """Get the last tiff and make sure it's the correct size."""
        
        last_tiffs = list(Path(self.folder).glob('*.tif*'))[-4:-2]
        
        # pull the last few tiffs to make sure none are weirdos and get trial lengths
        for tiff in last_tiffs:
            with ScanImageTiffReader(str(tiff)) as reader:
                data = reader.data()
                # check for bad tiffs
                if data.shape[0] < 10: 
                    last_tiffs.remove(tiff)

        return str(last_tiffs[-1])
    
    
    def process_and_save(self, results, save_path=None):
        """
        Concatenate 'C' data across planes from results. Saves the raw data C and trial lengths, then
        processes the data, making it trialwise, min subtracting, and scaling. Saves output data in 
        several formats including json, npy, and mat.

        Args:
            results (list): list of results returned by plane workers
            save_path (str, optional): Path to save data. Defaults to None which saves in the
                                       self.output_folder directory
        """
        
        if save_path is None:
            save_path = self.output_folder
        else:
            save_path = Path(save_path)
        
        c_list = [r['C'] for r in results]
        c_all = np.concatenate(c_list, axis=0)
        out = {
            'c': c_all.tolist(),
            'splits': self.lengths,
            'trialtimes': self.trialtimes_success
        }
        
        # first save the raw data in case it fails (concatentated)
        # added a try-except block here so the server will eventually quit if it fails
        try:
            fname = save_path/'raw_data.json'
            with open(fname, 'w') as f:
                json.dump(out, f)
            
            # do proccessing and save trialwise json
            # ! fix this, traces is actually getting psths and this is confusing AF
            _, traces = process_data(**out, normalizer='zscore', fr=self.fr, stim_times=None)
            out = {
                'traces': traces.tolist(),
            }
            fname = save_path/'traces_data.json'
            with open(fname, 'w') as f:
                json.dump(out, f)
                
            # save it as a npy also
            fname = save_path/'traces.npy'
            np.save(fname, c_all)
            fname = save_path/'psths.npy'
            np.save(fname, traces)
            
            # save as matlab
            fname = save_path/'data.mat'
            mat = {
                'onlineTraces': c_all,
                'onlinePSTHs': traces,
                'onlineTrialLengths': self.lengths
            }
            sio.savemat(str(fname), mat)
            
        except Exception:
            Alert('Something with data saving has failed. Check printed error message.', 'error')
            logger.exception('Saving data failed Check printed error message.')
 