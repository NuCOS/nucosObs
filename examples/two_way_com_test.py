import asyncio as aio

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread, broadcast
from nucosObs.observable import Observable
from nucosObs.twoWayInterface import TwoWayInterface

debug.append(True)

class HelloObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(HelloObserver, self).__init__(name, observable, concurrent)
      
    async def say(self):
        print("%s Hello" % self.name)


forward = Observable()
backward = Observable()
interf = TwoWayInterface({"forward":forward, "backward":backward}, send_all=True)
O1 = HelloObserver("O1", forward)
O2 = HelloObserver("O2", backward)

aio.ensure_future(interf.put("forward say"))
aio.ensure_future(interf.put("backward say"))
aio.ensure_future(interf.put("say"))

ui = interf.get_ui()
main_loop([ui])

