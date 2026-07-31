import asyncio

import pytest

import nucosObs
from nucosObs.observable import Observable
from nucosObs.observer import Observer


@pytest.mark.asyncio
async def test_observer_waits_for_handler_before_processing_next_event():
    nucosObs.allObs.clear()
    nucosObs.allObservables.clear()

    class OrderedObserver(Observer):
        def __init__(self, observable):
            super().__init__("ordered", observable)
            self.started = asyncio.Event()
            self.release = asyncio.Event()
            self.completed = False

        async def process(self):
            self.started.set()
            await self.release.wait()
            self.completed = True

    observable = Observable()
    observer = OrderedObserver(observable)
    observer_task = asyncio.create_task(observer.observe())

    try:
        await observable.put({"name": "process"})
        await observable.put({"action": "stop_observer"})
        await asyncio.wait_for(observer.started.wait(), timeout=1)
        await asyncio.sleep(0)

        assert not observer_task.done()

        observer.release.set()
        await asyncio.wait_for(observer_task, timeout=1)
        assert observer.completed
    finally:
        if not observer_task.done():
            observer_task.cancel()
            await asyncio.gather(observer_task, return_exceptions=True)
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()