#!/usr/bin/env python
import asyncio as aio
import ssl
try:
    import simplejson as json
except:
    import json

from nucosCR import hexdigest_n

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread
from nucosObs.observable import Observable
from nucosObs.stdinInterface import StdinInterface
from nucosObs.websocketInterface import WebsocketInterface

debug.append(True)

messageBroker = Observable()
user = Observable()

server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) # ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
context.load_verify_locations(cafile=server_cert)

wsi = WebsocketInterface(messageBroker)



class WebSocketObserver(Observer):
    def __init__(self, name, observable, wsi, concurrent=[]):
        super(WebSocketObserver, self).__init__(name, observable, concurrent)
        self.wsi = wsi
        self.authenticated = False
        self.id = ""
        self.user = "test-user"

    async def logger(self, msg):
        print("log from server: %s" % msg, type(msg))

    async def send(self, msg):
        # NOTE inject the session id
        msg["args"][0] = self.user
        msg["args"][1] = self.id
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        if wsi.ws['client'].open:
            await wsi.ws['client'].send(msg)
            print("message send: %s" % msg)
        else:
            print("connection already closed")
      
    def parse(self, item):
        """
        Json parse logic, specialised for clients

        a message is of the form {"name": ..., "args": [A,B,C,...] }

        """
        item = json.loads(item)
        if not isinstance(item, dict):
            print("unknown message format %s, expected dict " % type(item))
            return False, None, None
        if "name" in item:
            fct = item["name"]
        else:
            fct = None
        if "args" in item:
            args = item["args"]
        else:
            args = []
        if not isinstance(args, list):
            args = [args]
        try:
            method = getattr(self, fct)
            return True, method, args
        except:
            if debug[-1]:
                print("ACTION: %s" % item)
            return False, None, None

    async def print(self, *msg):
        print("message received: "," ".join(msg))

    async def doAuth(self, arg):
        print("try auth", arg)
        user = self.user
        pwd = "test123"
        pre_digest = hexdigest_n(pwd, 100)
        challenge = hexdigest_n(pre_digest + arg["nonce"], 100)
        authMsg = {
          "name": 'doAuth',
          "args": {'user': user, 'challenge': challenge, 'id': arg["id"] },
          "action": 'default'
        }
        await self.wsi.ws['client'].send(json.dumps(authMsg))

    async def finalizeAuth(self, args):
        print("finalized auth")
        self.authenticated = args["authenticated"]
        self.id = args["id"]
        if not self.authenticated:
            print("Auth rejected")

        


obs = WebSocketObserver("RO", messageBroker, wsi)

# NOTE to stop stdInInterface enter "x"
ui = StdinInterface(user).get_ui()
aio.ensure_future(obs.scheduleOnce(obs.send, 1.0, {"name": "addUser", "args": ["user", "session_key", "new_user", "secret"], "action": 'default'}))
pwd = "test123"
pre_digest = hexdigest_n(pwd, 100)
nonce = "abcde"
challenge = hexdigest_n(pre_digest + nonce, 100)
aio.ensure_future(obs.scheduleOnce(obs.send, 1.5, {"name": "authenticateThirdUser", "args": ["user", "session_key", "test-user", nonce, challenge], "action": 'default'}))
#start the main loop with Interfaces
main_loop([wsi.connect('127.0.0.1', 5000), ui])


