import asyncio as aio
import sys
import random
import time

from nucosObs import main_loop
from nucosObs.observer import Observer, inThread
from nucosObs.observable import Observable
from nucosObs.stdinInterface import StdinInterface

class HelloObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(HelloObserver, self).__init__(name, observable, concurrent)
      
    async def say(self):
        print("Hello")
        

class FactorialObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(FactorialObserver, self).__init__(name, observable, concurrent)
        self.callbacks.update({self.fact: self.callback})
      
    @inThread(callback=True)
    def fact(self, number):
        f = 1
        number = int(number)
        for i in range(2, number+1):
            print("Task %s: Compute factorial(%s)..." % (self.name, i))
            time.sleep(0.5)
            f *= i
        print("Task %s: factorial(%s) = %s" % (self.name, number, f))
        self.result = f

    async def callback(self):
        print("done ... ", self.result)


A = Observable()
O1 = FactorialObserver("O1", A)
O2 = FactorialObserver("O2", A, concurrent=["O1"])
O3 = HelloObserver("O3", A)
ui = StdinInterface(A).get_ui()
print("type: 'fact 10', 'fact 10', 'say' in short interval")

main_loop([ui])

