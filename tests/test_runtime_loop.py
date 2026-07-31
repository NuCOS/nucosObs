import asyncio

import nucosObs
from nucosObs.observable import Observable
from nucosObs.observer import Observer
from nucosObs.stdinInterface import StdinInterface
from nucosObs.twoWayInterface import TwoWayInterface


def test_scheduled_observer_uses_current_package_loop():
    previous_loop = nucosObs.loop
    runtime_loop = asyncio.new_event_loop()
    nucosObs.loop = runtime_loop
    nucosObs.allObs.clear()
    nucosObs.allObservables.clear()

    class ScheduledObserver(Observer):
        def __init__(self, observable):
            super().__init__("scheduled", observable)
            self.ran = False

        async def tick(self):
            self.ran = True
            self.stopSchedule()

    async def wait_for_tick(observer):
        observer.startSchedule()
        for _ in range(20):
            if observer.ran:
                return
            await asyncio.sleep(0.01)
        raise AssertionError("scheduled handler did not run on the current loop")

    try:
        observable = Observable()
        observer = ScheduledObserver(observable)
        observer.scheduleRegular(observer.tick, 0.01)

        runtime_loop.run_until_complete(wait_for_tick(observer))

        assert observable.loop is runtime_loop
        assert observer.loop is runtime_loop
    finally:
        if not runtime_loop.is_closed():
            runtime_loop.close()
        nucosObs.loop = previous_loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()


def test_interfaces_use_current_package_loop():
    previous_loop = nucosObs.loop
    runtime_loop = asyncio.new_event_loop()
    nucosObs.loop = runtime_loop
    nucosObs.allObs.clear()
    nucosObs.allObservables.clear()

    try:
        observable = Observable()
        stdin_interface = StdinInterface(observable)
        two_way_interface = TwoWayInterface({})

        assert stdin_interface.loop is runtime_loop
        assert two_way_interface.loop is runtime_loop
    finally:
        runtime_loop.close()
        nucosObs.loop = previous_loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()