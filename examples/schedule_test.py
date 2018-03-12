import asyncio as aio
import sys
import random
import time

from nucosObs import main_loop, debug
from nucosObs.observer import Observer, inThread
from nucosObs.observable import Observable
from nucosObs.stdinInterface import StdinInterface

debug.append(True)

class HelloObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(HelloObserver, self).__init__(name, observable, concurrent)
      
    async def say(self):
        print("Hello")
    async def once(self):
        print("Hello once")        



A = Observable()
Obs = HelloObserver("O3", A)
ui = StdinInterface(A).get_ui()

Obs.scheduleRegular(Obs.say, 1.0)

print("every 1 second ...(to stop type 'x' or 'leave_in 3')")
aio.ensure_future(Obs.scheduleOnce(Obs.once, 4.3))

main_loop([ui])

