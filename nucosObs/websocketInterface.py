import websockets
import asyncio as aio
try:
    import simplejson as json
except:
    import json

try:
    from nucosCR import random, hexdigest_n
    isCR = True
except:
    import random
    isCR = False

from nucosObs import loop, debug
from nucosObs.observer import broadcast


class WebsocketInterface(object):
    def __init__(self, broker, doAuth=False, closeOnClientQuit=False, authenticator=None, sslClient=None, sslServer=None):
        """
        NOTE: authenticator must have a method: startAuth(msg, wsi)
        """
        self.ws = {}
        self.doAuth = doAuth
        self.broker = broker
        self.server = None
        self.authenticator = authenticator
        self.nonce = {}
        self.isAuthenticated = {}
        self.isRefused = []
        self.closeOnClientQuit = closeOnClientQuit
        self.sslClient = sslClient
        self.sslServer = sslServer
        self.approved = []

    async def broadcast(self, msg, client=None):
        for i, antenna in enumerate(self.ws.values()):
            if client is None or i == client:
                await antenna.send(msg)

    async def connect(self, host, port):
        if debug[-1]:
            print("try to start client")
        # self.server = await websockets.connect(self.handler, ip, port)
        if self.sslClient:
            protocol = "wss"
        else:
            protocol = "ws"
        websocket = await websockets.connect('%s://%s:%s' %(protocol, host, str(port)), ssl=self.sslClient)
        self.ws['client'] = websocket
        await self.listener(websocket, 'client')

    async def serve(self, ip, port):
        if debug[-1]:
            print("try to start server")
        self.server = await websockets.serve(self.handler, ip, port, ssl=self.sslServer)
        print("started server", self.server)

    async def handler(self, websocket, path):
        host = websocket.host
        if isCR:
            id_ = random(12).decode()
        else:
            id_ = bytes([random.getrandbits(4) for i in range(12)]).decode()
        self.ws[id_] = websocket
        if debug[-1]:
            print("Partner connected")        
        if self.doAuth:
            if isCR:
                self.nonce[id_] = random(24).decode()
            else:
                self.nonce[id_] = bytes([random.getrandbits(4) for i in range(24)])
            context = {"name": "doAuth",
                       "args": {"nonce": self.nonce[id_], "id": id_},
                       "action": "authenticate"}
            await self.ws[id_].send(json.dumps(context))
        await self.listener(self.ws[id_], id_)

    async def shutdown(self):
        if debug[-1]:
            print("in shutdown process ...")
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
        if self.server is not None:
            for k in [x for x in self.ws.keys()]:
                await self.ws[k].close()

    async def listener(self, ws, id_):
        user = "unknown"
        while True:
            if ws is not None:
                if ws.open:
                    try:
                        msg = await ws.recv()
                    except:
                        if id_ == "client":
                            await self.shutdown()
                            break
                        else:
                            msg = ""
                    if msg:
                        if not id_ in self.isAuthenticated and self.doAuth:
                            id_out, user = await self.authenticator.startAuth(msg, ws, self.nonce[id_])
                            if id_out is not None and id_out == id_:
                                self.isAuthenticated.update({id_: user})
                            else:
                                self.ws.pop(id_)
                                ws.close()
                                break
                        else:
                            await self.broker.put(msg)
                else:
                    if id_ == "client":
                        await self.shutdown()
                        break
                    else:
                        self.ws.pop(id_)
                        if self.closeOnClientQuit:
                            if debug[-1]:
                                print("client died ...")    
                            if len(self.ws) == 0:
                                await self.broker.put("client exit")
                                await self.shutdown()
                        if id_ in self.isAuthenticated:
                            self.isAuthenticated.pop(id_)
                        break

        if debug[-1]:
            print("--- connection of %s stopped " % user)
