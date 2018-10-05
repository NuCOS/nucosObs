import websockets
import asyncio as aio
try:
    import simplejson as json
except:
    import json
from nucosCR import hexdigest_n

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread, broadcast
from nucosObs.observable import Observable
from nucosObs.websocketInterface import WebsocketInterface

debug.append(True)

messageBroker = Observable()
user = Observable()


class Authenticator():
    def __init__(self):
        # next line is for testing purpose and means test-user with pwd: test123
        # for real worl application use another source for user-credentials
        self.users = {
            'test-user': '7d0bff4edd541774e07692b71c8f1af082682d6f1b158e1c29e156d1838c624b'}
        self.approved = False

    async def startAuth(self, msg, wsi, nonce):
        inp = json.loads(msg)
        args = inp["args"]
        try:
            user, challenge, id_ = args["user"], args["challenge"], args["id"]
        except:
            return
        if debug[-1]:
            print("start auth", msg)
        if self.authenticate(id_, user, nonce, challenge):
            
            context = {"name": "finalizeAuth",
                       "args": {"authenticated": True},
                       "action": "authenticated"}
            await wsi.send(json.dumps(context))
            if debug[-1]:
                print("Authenticate accepted")
            return id_, user
        else:
            context = {"name": "finalizeAuth",
                       "args": {"authenticated": False},
                       "action": "authenticated"}
            await wsi.send(json.dumps(context))
            if debug[-1]:
                print("Authenticate refused")
            return None, None

    def authenticate(self, id_, user, nonce, challenge):
        # pre = hexdigest_n('test123', 100)
        # print("PRE local", pre)
        digest = hexdigest_n(self.users[user] + nonce, 100)
        # print(digest, challenge, pre)
        return digest == challenge


class SendObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(SendObserver, self).__init__(name, observable, concurrent)

    async def send(self, *msg):
        await wsi.ws.send(' '.join(msg))
        print("message send: %s"%' '.join(msg))

class ReceiveObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(ReceiveObserver, self).__init__(name, observable, concurrent)

    async def print(self, *msg):
        print("message received: "," ".join(msg))

    def parse(self, item):
        method = self.print
        args = item.split(" ")
        return True, method, args
    

so = SendObserver("SO", messageBroker)
ro = ReceiveObserver("RO", messageBroker)

wsi = WebsocketInterface(messageBroker, doAuth=True, closeOnClientQuit=False, authenticator=Authenticator())

#start the main loop with Interfaces
main_loop([wsi.serve('127.0.0.1',8765)])



