import asyncio as aio

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
        self.stopTimeFraction = 1
        self.stop = False
        self._bridge_ = {}

    def scheduleRegular(self, method, t, stopTimeFraction=1):
        self.schedule_task = method
        self.schedule_time = t
        self.stopTimeFraction = stopTimeFraction

    async def shutdown(self):
        if debug[-1]:
            print("shutdown now...")
        self.stop = True
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})

    async def scheduleOnce(self, method, t, *args):
        await aio.sleep(t)
        await method(*args)

    def parse(self, item):
        """
        Dict parse logic + str parse logic, overwrite if necessary

        a message is of the form {"name": function-name, "args": [A,B,C,...] }
        or "function-name A B C"

        """
        if isinstance(item, dict):
            if "name" in item:
                fct = item["name"]
            else:
                fct = None
            if "args" in item:
                args = item["args"]
            else:
                args = []
            if hasattr(self, fct):
                method = getattr(self, fct)
                if hasattr(method, '__call__'):
                    return True, method, args
                else:
                    return False, None, None
            else:
                return False, None, None
        elif isinstance(item, str):
            items = item.split(" ")
            fct, args = items[0], items[1:]

            if hasattr(self, fct):
                # print(fct, args)
                method = getattr(self, fct)
                if hasattr(method, '__call__'):
                    return True, method, args
                else:
                    return False, None, None
            else:
                return False, None, None
        else:
            return False, None, None

    async def scheduleLoop(self):
        self.stop = False
        while not self.stop:
            n = 0
            while n < self.stopTimeFraction:
                n += 1
                await aio.sleep(self.schedule_time / self.stopTimeFraction)
                if self.stop:
                    break
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
                print("observer %s received %s, type %s" %
                      (self.name, item, type(item)))
            try:
                isCallable, method, args = self.parse(item)
            except:
                # NOTE for self created parse function and failures therein
                if debug[-1]:
                    print("parse failed: %s" % item)
                isCallable = False
            if isCallable:
                if "inThread" in dir(method):
                    await self.loop.run_in_executor(pool, method, *args)
                    if method.callback:
                        if method in self.callbacks:
                            await self.callbacks[method]()
                        else:
                            raise NoCallbackException(
                                "No callback known of method %s" % method)
                else:
                    await method(*args)
            elif isinstance(item, dict) and "action" in item:
                if debug[-1]:
                    print("....", item)
                if item["action"] == "stop_observer":
                    self.stop = True
                break
            elif isinstance(item, str) and "stop_observer" in item:
                # print(".....", isCallable, method, args, item)
                self.stop = True
                break
            else:
                if debug[-1]:
                    print("swallowed: %s %s" % (self.name, item))
        if debug[-1]:
            print("--- Observer: %s stopped %s" % (self.name, self.stop))

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
        if debug[-1]:
            print("broadcast ...", msg, type(msg))
        if "action" in msg:
            if debug[-1] and msg["action"] == "stop_observer":
                print("shut down all observers ...")
        for o in self.obs:
            await o.put(msg)


broadcast = Observable()
broadcastObserver = BroadcastObserver("broadcastObserver", broadcast)
