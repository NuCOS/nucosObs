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
    def __init__(self, broker, doAuth=False, closeOnClientQuit=False):
        self.ws = {}
        self.doAuth = doAuth
        self.broker = broker
        self.server = None
        self.nonce = {}
        self.isAuthenticated = {}
        self.closeOnClientQuit = closeOnClientQuit
        self.users = {
            'test-user': '7d0bff4edd541774e07692b71c8f1af082682d6f1b158e1c29e156d1838c624b'}
        self.approved = []

    async def broadcast(self, msg):
        for antenna in self.ws.values():
            await antenna.send(msg)

    async def startAuth(self, msg):
        inp = json.loads(msg)
        args = inp["args"]
        try:
            user, challenge, id_ = args["user"], args["challenge"], args["id"]
        except:
            return
        if debug[-1]:
            print("start auth", msg)
        if self.authenticate(id_, user, challenge):
            self.isAuthenticated.update({id_: user})
            context = {"name": "Auth",
                       "args": {"authenticated": True},
                       "action": "authenticated"}
            await self.ws[id_].send(json.dumps(context))
            if debug[-1]:
                print("Authenticate accepted")
        else:
            context = {"name": "Auth",
                       "args": {"authenticated": False},
                       "action": "authenticated"}
            await self.ws[id_].send(json.dumps(context))
            if debug[-1]:
                print("Authenticate refused")

    def authenticate(self, id_, user, challenge):
        # pre = hexdigest_n('test123', 100)
        # print("PRE local", pre)
        digest = hexdigest_n(self.users[user] + self.nonce[id_], 100)
        # print(digest, challenge, pre)
        return digest == challenge

    async def serve(self, ip, port):
        if debug[-1]:
            print("try to start server")
        self.server = await websockets.serve(self.handler, ip, port)
        self.handshake = True

    async def handler(self, websocket, path):
        host = websocket.host
        if isCR:
            id_ = random(12).decode()
        else:
            id_ = bytes([random.getrandbits(4) for i in range(12)]).decode()
        self.ws[id_] = websocket
        if debug[-1]:
            print("Client connected")
        if isCR:
            self.nonce[id_] = random(24).decode()
        else:
            self.nonce[id_] = bytes([random.getrandbits(4) for i in range(24)])
        context = {"name": "Auth",
                   "args": {"nonce": self.nonce[id_], "id": id_},
                   "action": "authenticate"}
        await self.ws[id_].send(json.dumps(context))
        await self.listener(self.ws[id_], id_)

    async def shutdown(self):
        if debug[-1]:
            print("Websocket connection closed...")
        await broadcast.put("broadcast stop")

    async def listener(self, ws, id_):
        while True:
            if ws is not None:
                if ws.open:
                    try:
                        msg = await ws.recv()
                    except:
                        if self.server is None:
                            await self.shutdown()
                            break
                        else:
                            msg = ""
                    if msg:
                        if not id_ in self.isAuthenticated and self.doAuth:
                            await self.startAuth(msg)
                        else:
                            await self.broker.put(msg)
                else:
                    if self.server is None:
                        await self.shutdown()
                        break
                    else:
                        if debug[-1]:
                            print("client died ...")
                        await self.broker.put("client exit")
                        if id_ in self.isAuthenticated:
                            self.isAuthenticated.pop(id_)
                        break
            else:
                if self.closeOnClientQuit:
                    if debug[-1]:
                        print("shutdown ...")
                    break
                else:
                    await aio.sleep(1.0)
        if debug[-1]:
            print("WebsocketInterface stopped")
