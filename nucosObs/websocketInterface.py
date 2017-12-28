import websockets
import asyncio as aio

from nucosObs import loop, debug, broadcast

class WebsocketInterface(object):
    def __init__(self, broker):
        self.ws = None
        self.loop = loop
        self.broker = broker
        self.server = None

    async def connect(self, ip, port):
        print("try to connect")
        websocket = await websockets.connect('ws://%s:%s' %(ip,str(port)))
        self.ws = websocket   
        print("done")
        await self.listener()

    async def serve(self, ip, port):
        print("try to start server")
        self.server = await websockets.serve(self.handler, ip, port)
        print("done")

    async def handler(self, websocket, path):
        self.ws = websocket
        await self.listener()

    async def shutdown(self):
        print("Websocket connection closed...")
        await broadcast.put("broadcast stop")


    async def listener(self):
        while True:
            if self.ws is not None:
                if self.ws.open:
                    try:
                        msg = await self.ws.recv()
                    except:                        
                        if self.server is None:
                            await self.shutdown()
                            break
                        else:
                            msg = ""
                    if msg:
                        await self.broker.put(msg)
                else:
                    if self.server is None:
                        await self.shutdown()
                        break
                    else:
                        if debug[-1]:
                            print("client died ...")
                        self.ws = None
            else:
                await aio.sleep(0.1)
        if debug[-1]:
            print("WebsocketInterface stopped")


