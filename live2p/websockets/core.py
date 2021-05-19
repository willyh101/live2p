import functools
from ..start_live2p import DEFAULT_IP, DEFAULT_PORT
import websockets
import asyncio
import json
import concurrent.futures

from . import events as events_module

class WebSocketServer:
        
    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        self.ip = ip
        self.port = port
        self.url = f'ws://{ip}:{port}'
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.event_mapping = {}
        self.loop = asyncio.get_event_loop()
        
    def event(self, name):
        # this works if called as @wss.event('SETUP)
        def event_wrapper(func):
            self.event_mapping[name] = func
            return func
        return event_wrapper
    
    async def call_event(self, name, *args, **kwargs):
        # get from events module
        event = getattr(events_module, name.lower(), None)
        if event is None:
            raise NameError(f'No event registered to {name}')
        return await event(*args, **kwargs)
    
    async def call_registered(self, name, *args, **kwargs):
        event = self.event_mapping.get(name, None)
        if event is None:
            raise NameError(f'No event registered to {name}')
        return await event(*args, **kwargs)
    
    def run_server(self):
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
            event = data.pop('EVENTTYPE')
            # await self.call_registered(event, data)
            await self.call_event(event, data)