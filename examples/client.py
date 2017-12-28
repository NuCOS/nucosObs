#!/usr/bin/env python
import asyncio as aio

from nucosObs import main_loop, loop, debug, broadcast
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
      
    def parse(self, item):
        """
        Example of specialized parse function. Here every message is send immediately.

        """
        return True, self.send, (item,)

    async def send(self, item):
        await wsi.ws.send(item)
        print("message send: %s"%item)

class ReceiveObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(ReceiveObserver, self).__init__(name, observable, concurrent)
      
    async def print(self, *msg):
        print("message received: "," ".join(msg))
        

so = SendObserver("SO", user)
ro = ReceiveObserver("RO", messageBroker)

ui = StdinInterface(user).get_ui()

#start the main loop with Interfaces
main_loop([wsi.connect('192.168.178.42',8765), ui])
