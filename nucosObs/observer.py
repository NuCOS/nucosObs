import asyncio as aio
import time

from nucosObs import loop, allObs, pool, debug, allObservables


def inThread(callback=False):
    def wrapper(func):
        """
        Use this decorator to indicate that the function is not-async and time consuming and should be run in a separate thread.
        The observer awaits the result, other observers are running normally.

        :param callback: True if a callback is defined, default is False
        :type callback: bool
        """
        func.inThread = True
        func.callback = callback
        return func
    return wrapper


class NoCallbackException(Exception):
    """
    Exception which is raised, if a callback is expected but not asigned to the callbacks dict.

    """
    def __init__(self, message):
        self.message = message

class Observer():
    """
    The callback class which reacts on observables. An Observer must register on observables.
    Many Observers can register on one observable.
    One Observer can register only on one observable and not many.

    Concurrent observers are possible. Just add other observers by name in the parameter list concurrent.

    Subclass Observer and add any async function which is then executed when invoked in the observables.
    The parameters for that call must be operated in the parse function.

    """
    def __init__(self, name, observable, concurrent=[]):
        """
        :param name: the name of the observer
        :type name: str
        :param observable: the observable to listen on
        :type observable: observable
        :param concurrent: all other concurrent observers (or just one of them, they share all on queue)
        :type concurrent: list
        """
        self.name = name
        self.queue = None
        self.loop = loop
        allObs.append(self)
        observable.register(self, concurrent)
        self.callbacks = {}


    def parse(self, item):
        """
        Most easiest parse logic. Overwrite this method for compliance with own messages.

        :param item: the message item to be parsed
        :type item: str
        """
        items = item.split(" ")
        item, args = items[0], items[1:]
        try:
            method = getattr(self, item)
        except:
            method = None
        if method is None:
            return False, item, args
        else:
            return True, method, args
        

    async def observe(self):
        """
        Do not overwrite the main observe logic, better overwrite the parse method for incoming string-messages.

        """
        while True:
            if self.queue is None:
                break
            item = await self.queue.get()
            
            if item=="stop":
                break
            isCallable, method, args = self.parse(item)
            
            if isCallable:
                if "inThread" in dir(method):
                    await self.loop.run_in_executor(pool, method, *args)
                    if method.callback:
                        if method in self.callbacks:
                            future = aio.ensure_future(self.callbacks[method]())
                            await future
                        else:
                            raise NoCallbackException("No callback known of method %s" % method)
                else:
                    future = aio.ensure_future(method(*args))
                    await future
            else:
                if debug[-1]:
                    print("swallowed: ", self.name, method, args)
        if debug[-1]:
            print("%s stopped" % self.name)



class BroadcastObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(BroadcastObserver, self).__init__(name, observable, concurrent)
        self.obs = allObservables

    async def broadcast(self, msg):
        if debug[-1]:
            print("shut down all observers ...")
        for o in self.obs:
            await o.put(msg)


