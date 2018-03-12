import websockets
import asyncio as aio

try:
    from nucosCR import random
    isCR = True
except:
    import random
    isCR = False
from nucosObs import loop, debug 
from nucosObs.observer import broadcast

class WebsocketInterface(object):
    def __init__(self, broker, auth=None, closeOnClientQuit=False):
        self.ws = None
        self.loop = loop
        self.broker = broker
        self.server = None
        self.auth = auth
        self.closeOnClientQuit = closeOnClientQuit


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
        print("start handshake")
        self.handshake = True
        
        
    async def handler(self, websocket, path):
        self.ws = websocket
        if debug[-1]:
            print("Client connected")
        if isCR:
            self.nonce = random(24).decode()
        else:
            self.nonce = bytes([random.getrandbits(8) for i in range(24)])
        if self.auth:
            await self.ws.send("startAuth "+ self.nonce)
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
                        if self.auth is not None and not self.auth.approved:
                                authmsg = "startAuth " + self.nonce + " " + msg
                                await self.broker.put(authmsg)                        
                        await self.broker.put(msg)
                else:
                    if self.server is None:
                        await self.shutdown()
                        break
                    else:
                        if debug[-1]:
                            print("client died ...")
                        await self.broker.put("client exit")
                        self.ws = None
                        if self.auth:
                            self.auth.approved = False
            else:
                if self.closeOnClientQuit:
                    print("shutdown ...")
                    break
                else:
                    await aio.sleep(1.0)
        if debug[-1]:
            print("WebsocketInterface stopped")


