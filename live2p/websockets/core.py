import functools
from ..start_live2p import DEFAULT_IP, DEFAULT_PORT
import websockets
import asyncio
import json
import concurrent.futures

EVENT_KEY = 'EVENTTYPE'

class WebSocketServer:
        
    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        self.ip = ip
        self.port = port
        self.url = f'ws://{ip}:{port}'
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.event_mapping = {}
        self.loop = asyncio.get_event_loop()
        
    def event(self, name):
        """
        Decorater to register event into websocket server. The decorated function will be called
        when the websocket server receives the corresponding text string. By default the JSON key
        used is 'EVENTTYPE'.
        
        Usage:
        
          wss = WebSocketServer()
        
          @wss.event('HELLO')
          def handle_hello(data):
              print('Hello!')
              ...
              
        -In this example when the websocket server receives the key:value pair 'EVENTTYPE':'HELLO',
         this function will be called. key:value pairs can be specified in Python as dictionaries
         and in MATLAB as struct fields.
         
         eg:
            (MATLAB)
            out.EVENTTYPE = 'HELLO'
            out = jsonencode(out);
            ws.send(out);
            
            (PYTHON)
            out = {
                'EVENTTYPE': 'HELLO'
            }
            out = json.dumps(out)
            ws.send(out)
            
            

        Args:
            name (str): Name of event to register. Corresponds to the JSON 'EVENTTYPE' field (or
                        custom fieldname if EVENT_KEY is changed).
        """
        def event_wrapper(func):
            self.event_mapping[name] = func
            return func
        return event_wrapper
    
    async def call_registered(self, name, *args, **kwargs):
        event = self.event_mapping.get(name, None)
        if event is None:
            raise NameError(f'No event registered to {name}')
        return await event(*args, **kwargs)
    
    def run_server(self):
        """
        Runs the server and allows for keyboard interrupts.
        """
        serve = websockets.serve(self.handle_incoming, self.ip, self.port)
        self.wss = serve.ws_server
        loop = asyncio.get_event_loop()
        loop.run_until_complete(serve)
        
        loop.create_task(self._wakeup())
        loop.set_default_executor(self.executor)
        
        try:
            print('ready')
            loop.run_forever()
        except KeyboardInterrupt:
            self._teardown()
            
    def _teardown(self):
        self.wss.close()
        try:
            self.executor.shutdown()
        except Exception:
            pass
        asyncio.get_event_loop().stop()
        
    async def _wakeup(self):
        while True:
            await asyncio.sleep(1)
            
    async def handle_incoming(self, websocket, path):
        async for payload in websocket:
            data = json.loads(payload)
            event = data.pop(EVENT_KEY)
            await self.call_registered(event, data)
            
    def in_background(self):
        def decorator(func):
            @functools.wraps
            def exector_wrapper(*args, **kwargs):
                task = self.loop.run_in_executor(
                    None, lambda: func(*args, **kwargs)
                )
                return task
            return exector_wrapper
        return decorator
                