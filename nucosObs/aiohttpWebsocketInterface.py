import asyncio as aio
from aiohttp import web
import aiohttp
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


class AiohttpWebsocketInterface(object):
    def __init__(self, app, broker, doAuth=False, closeOnClientQuit=False, authenticator=None, sslClient=None, sslServer=None):
        """
        NOTE: authenticator must have a method: startAuth(msg, wsi)
        """
        self.app = app
        self.ws = {}
        self.doAuth = doAuth
        self.broker = broker
        self.server = None
        self.authenticator = authenticator
        self.nonce = {}
        self.isAuthenticated = {}
        self.connectedUser = {}
        self.isRefused = []
        self.closeOnClientQuit = closeOnClientQuit
        self.sslClient = sslClient
        self.sslServer = sslServer
        self.approved = []
        app.router.add_route('GET', '/ws', self.handler)

    async def send(self, msg, user):
        id_ = self.connectedUser.get(user)
        if id_ is None:
            return
        else:
            try:
                await self.ws[id_].send_str(msg)
            except:
                pass

    async def broadcast(self, msg):
        for id_, ws in self.ws.items():
            try:
                await ws.send_str(msg)
            except:
                pass

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


    async def handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        id_ =  ws.headers.get("Sec-Websocket-Accept")
        self.ws.update({id_: ws})
        if debug[-1]:
            print("Partner connected")     
            print(self.ws)   
        if self.doAuth:
            if isCR:
                self.nonce[id_] = random(24).decode()
            else:
                self.nonce[id_] = bytes([random.getrandbits(4) for i in range(24)])
            context = {"name": "doAuth",
                       "args": {"nonce": self.nonce[id_], "id": id_},
                       "action": "authenticate"}
            await ws.send_str(json.dumps(context)) #or send_bytes ??
        await self.listener(ws, id_)
        # NOTE next line is mandatory for preventing a closed websocket to raise exception
        return ws

    async def shutdown(self):
        if debug[-1]:
            print("in shutdown process ...")
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
        if self.server is not None:
            for k in [x for x in self.ws.keys()]:
                await self.ws[k].close()

    async def listener(self, ws, id_):
        user = "unknown"

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.text:
                data = msg.data
                if not id_ in self.isAuthenticated and self.doAuth:
                    id_out, user = await self.authenticator.startAuth(data, ws, self.nonce[id_])
                    if id_out is not None and id_out == id_:
                        self.isAuthenticated.update({id_: user})
                        if user in self.connectedUser:
                            id_old = self.connectedUser.pop(user)
                            self.isAuthenticated.pop(id_old)
                            try:
                                await self.ws[id_old].close()
                            except:
                                pass
                            finally:
                                if debug[-1]:
                                    print("closed one pending connection of user %s" % user)
                            self.connectedUser.update({user : id_})
                        else:
                            self.connectedUser.update({user : id_})
                        # print(self.connectedUser, self.ws)
                    else:
                        await self.ws[id_].close()
                        break
                else:
                    await self.broker.put(data)
        if id_ == "client":
            await self.shutdown()
        else:
            self.ws.pop(id_)
            if self.closeOnClientQuit:
                if debug[-1]:
                    print("client died ...")    
                if len(self.ws) == 0:
                    await self.broker.put("client exit")
                    await self.shutdown()
            if id_ in self.isAuthenticated:
                user = self.isAuthenticated.pop(id_)
                if user in self.connectedUser:
                    self.connectedUser.pop(user)
                if debug[-1]:
                    print("after client left:")
                    print("user...",self.connectedUser)
                    print("ws.....",self.ws)
                


        if debug[-1]:
            print("--- connection of %s stopped " % user)
