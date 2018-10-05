import asyncio as aio

from nucosObs import loop, allObservables


class NoConcurrentObserver(Exception):
    def __init__(self, message):
        self.message = message

class Observable():
    """
    The observable can be observed by one or many observers. Observers are registered in their init.
    The events are produced in tasks which are then put into the async loop from the beginning on.

    """
    def __init__(self):
        self.loop = loop
        self.q = {}
        allObservables.append(self)

    def register(self, observer, concurrent=[]):
        if not concurrent:
            self.q.update({observer.name: aio.Queue(loop=self.loop)})
            observer._queue = self.q[observer.name]
        else:
            concurrentQueues = []
            for c in concurrent:
                if c in self.q:
                    concurrentQueues.append(self.q[c])
            if concurrentQueues:
                observer._queue = concurrentQueues[0]
            else:
                raise NoConcurrentObserver("No known observers %s"%concurrent)

    async def put(self, event):
        for q in self.q.values():
            await q.put(event)

