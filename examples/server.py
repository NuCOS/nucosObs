import websockets
import asyncio as aio

from nucosObs import main_loop, loop, debug, broadcast
from nucosObs.observer import Observer, inThread
from nucosObs.observable import Observable
from nucosObs.websocketInterface import WebsocketInterface

debug.append(False)

messageBroker = Observable()
user = Observable()

wsi = WebsocketInterface(messageBroker)

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


so = SendObserver("SO", messageBroker)
ro = ReceiveObserver("RO", messageBroker)

#start the main loop with Interfaces
main_loop([wsi.serve('localhost',8765)])



