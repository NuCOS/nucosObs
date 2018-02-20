#!/usr/bin/env python
import asyncio as aio
from nucosCR import hexdigest_n

from nucosObs import main_loop, loop, debug, broadcast
from nucosObs.observer import Observer, inThread
from nucosObs.observable import Observable
from nucosObs.stdinInterface import StdinInterface
from nucosObs.websocketInterface import WebsocketInterface

debug.append(True)

messageBroker = Observable()
user = Observable()
wsi = WebsocketInterface(messageBroker)

class AuthClientObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(AuthClientObserver, self).__init__(name, observable, concurrent)
        self.approved = False

    async def startAuth(self, *args):
        try:
            self.nonce = args[0]
        except:
            await self.shutdown()

    async def authenticate(self, user, password):
        pre_digest = hexdigest_n(password, 100)
        challenge = hexdigest_n(pre_digest + self.nonce, 100)
        print("challenge",challenge)
        await wsi.ws.send(" ".join([user,challenge]))

    async def endAuth(self, *args):
        if args[0]=="approved":
            self.approved = True
        else:
            await self.shutdown()

    async def shutdown(self):
        print("Auth failed")
        await wsi.ws.close()

class SendObserver(Observer):
    def __init__(self, name, observable, concurrent=[], auth=None):
        super(SendObserver, self).__init__(name, observable, concurrent)
        self.auth = auth

    def parse(self, item):
        """
        Example of specialized parse function. Here every message is sent immediately.

        """
        if self.auth is not None:
            if not self.auth.approved:
                try:
                    user, pwd = item.split(" ")
                except:
                    return True, self.send, (item,)    
                return True, self.authenticate, (user, pwd) 
        return True, self.send, (item,)

    async def authenticate(self, user, pwd):
        await self.auth.authenticate(user, pwd)
        

    async def send(self, item):
        await wsi.ws.send(item)
        print("message send: %s"%item)

class ReceiveObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(ReceiveObserver, self).__init__(name, observable, concurrent)
      
    async def print(self, *msg):
        print("message received: "," ".join(msg))
        


ro = ReceiveObserver("RO", messageBroker)
ao = AuthClientObserver("AO", messageBroker)
so = SendObserver("SO", user, auth=ao)
ui = StdinInterface(user).get_ui()

#start the main loop with Interfaces
main_loop([wsi.connect('192.168.178.39',8765), ui])
