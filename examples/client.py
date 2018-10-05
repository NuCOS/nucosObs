#!/usr/bin/env python
import asyncio as aio

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
wsi = WebsocketInterface(messageBroker)



class SendObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(SendObserver, self).__init__(name, observable, concurrent)
        self.auth = False

    async def send(self, item):
        await wsi.ws.send(item)
        print("message send: %s"%item)

class ReceiveObserver(Observer):
    def __init__(self, name, observable, wsi, concurrent=[]):
        super(ReceiveObserver, self).__init__(name, observable, concurrent)
        self.wsi = wsi
        self.authenticated = False
      
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
        user = "test-user"
        pwd = "test123"
        pre_digest = hexdigest_n(pwd, 100)
        challenge = hexdigest_n(pre_digest + arg["nonce"], 100)
        authMsg = {
          "name": 'doAuth',
          "args": {'user': user, 'challenge': challenge, 'id': arg["id"] },
          "action": 'default'
        }
        await self.wsi.ws['client'].send(json.dumps(authMsg))

    async def finalizeAuth(self, arg):
        print("finalized auth")
        self.authenticated = arg["authenticated"]

        


ro = ReceiveObserver("RO", messageBroker, wsi)
so = SendObserver("SO", user)
ui = StdinInterface(user).get_ui()

#start the main loop with Interfaces
main_loop([wsi.connect('127.0.0.1',8765), ui])
