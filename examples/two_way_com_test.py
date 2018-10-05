import asyncio as aio

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread, broadcast
from nucosObs.observable import Observable
from nucosObs.twoWayInterface import TwoWayInterface

debug.append(True)

class HelloObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(HelloObserver, self).__init__(name, observable, concurrent)
      
    async def say(self, name):
        print("Hello %s" % name)


forward = Observable()
backward = Observable()
interf = TwoWayInterface({"forward":forward, "backward":backward}, send_all=True)
O1 = HelloObserver("O1", forward)
O2 = HelloObserver("O2", backward)

aio.ensure_future(interf.put({"obs": "forward",  "name": "say", "args": ["Joe"]}))
aio.ensure_future(interf.put({"obs": "backward",  "name": "say", "args": ["Moe"]}))
aio.ensure_future(interf.put({"name": "say", "args": ["Toe"]}))
aio.ensure_future(interf.put({"action": "stop interface"}))
ui = interf.get_ui()
main_loop([ui])

