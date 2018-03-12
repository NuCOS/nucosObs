import asyncio as aio
import time

from nucosObs import loop, allObs, pool, debug, allObservables
from nucosObs.observable import Observable


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
        :param concurrent: all other concurrent observers (or just one of them, they share all on _queue)
        :type concurrent: list
        """
        self.name = name
        self._queue = None
        self.loop = loop
        allObs.append(self)
        observable.register(self, concurrent)
        self.callbacks = {}
        self.schedule_time = 1.0
        self.schedule_task = None
        self.stop = False
        self._bridge_ = {}

    def scheduleRegular(self, method, t):
        self.schedule_task = method
        self.schedule_time = t

    async def shutdown(self):
        if debug[-1]:
            print("shutdown now...")
        self.stop = True
        await broadcast.put("broadcast stop")

    async def scheduleOnce(self, method, t):
        await aio.sleep(t)
        await method()

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

    async def scheduleLoop(self):
        self.stop = False
        while not self.stop:
            await aio.sleep(self.schedule_time)
            if self.schedule_task:
                await self.schedule_task()
        if debug[-1]:
            print("leave scheduleLoop")

    async def observe(self):
        """
        Do not overwrite the main observe logic, better overwrite the parse method for incoming string-messages.

        """
        self.stop = False
        while not self.stop:
            if self._queue is None:
                break
            item = await self._queue.get()
            if debug[-1]:
                print("observer %s received %s"% (self.name , item))
            if item == "stop":
                self.stop = True
                break
            try:
                isCallable, method, args = self.parse(item)
            except:
                isCallable = False
                method = None
                args = None

            if isCallable:
                if "inThread" in dir(method):
                    await self.loop.run_in_executor(pool, method, *args)
                    if method.callback:
                        if method in self.callbacks:
                            future = aio.ensure_future(
                                self.callbacks[method]())
                            await future
                        else:
                            raise NoCallbackException(
                                "No callback known of method %s" % method)
                else:
                    #if isinstance(args, list):
                    future = aio.ensure_future(method(*args))
                    #else:
                    #    future = aio.ensure_future(method(args))
                    await future
            else:
                if debug[-1]:
                    print("swallowed: ", self.name, method, args)
        if debug[-1]:
            print("%s stopped %s" % (self.name, self.stop))

    def set_bridge_method(self, method_name, method_hook):
        """
        Defines bridge methods which are just follow-ups to communicate with ApplicationSessions

        """
        self._bridge_.update({method_name: method_hook})

    async def bridge(self, method, *args):
        if debug[-1]:
            print("bridge call %s" % method)
        if method not in self._bridge_:
            return
        else:
            await self._bridge_[method](*args)


class BroadcastObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(BroadcastObserver, self).__init__(name, observable, concurrent)
        self.obs = allObservables

    async def broadcast(self, msg):
        if debug[-1] and msg == "stop":
            print("shut down all observers ...")
        for o in self.obs:
            await o.put(msg)


broadcast = Observable()
broadcastObserver = BroadcastObserver("broadcastObserver", broadcast)
