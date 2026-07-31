import asyncio
import threading

import pytest

import nucosObs
from nucosObs.observable import Observable
from nucosObs.observer import Observer, inThread


def test_main_loop_keeps_shared_thread_pool_available():
    previous_loop = nucosObs.loop
    runtime_loop = asyncio.new_event_loop()
    nucosObs.loop = runtime_loop
    nucosObs.allObs.clear()
    nucosObs.allObservables.clear()

    try:
        nucosObs.main_loop([], test=True)
        result = runtime_loop.run_until_complete(
            runtime_loop.run_in_executor(nucosObs.pool, lambda: "available")
        )

        assert result == "available"
    finally:
        runtime_loop.close()
        nucosObs.loop = previous_loop


@pytest.mark.asyncio
async def test_in_thread_handler_runs_in_executor_before_callback():
    nucosObs.allObs.clear()
    nucosObs.allObservables.clear()

    class ThreadedObserver(Observer):
        def __init__(self, observable):
            super().__init__("threaded", observable)
            self.callback_completed = asyncio.Event()
            self.execution_thread = None
            self.received = None

        @inThread(callback=True)
        def process(self, value):
            self.execution_thread = threading.get_ident()
            self.received = value

        async def process_complete(self):
            self.callback_completed.set()

    observable = Observable()
    observer = ThreadedObserver(observable)
    observer.callbacks[observer.process] = observer.process_complete
    observer_task = asyncio.create_task(observer.observe())

    try:
        await observable.put({"name": "process", "args": ["value"]})
        await observable.put({"action": "stop_observer"})
        await asyncio.wait_for(observer_task, timeout=1)

        assert observer.received == "value"
        assert observer.execution_thread != threading.get_ident()
        assert observer.callback_completed.is_set()
    finally:
        if not observer_task.done():
            observer_task.cancel()
            await asyncio.gather(observer_task, return_exceptions=True)
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()