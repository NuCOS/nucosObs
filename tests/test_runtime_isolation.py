import asyncio

from nucosObs import Runtime
from nucosObs.observable import Observable
from nucosObs.observer import Observer


def test_runtime_instances_keep_observers_and_events_isolated():
    first_runtime = Runtime()
    second_runtime = Runtime()

    class RecordingObserver(Observer):
        def __init__(self, name, observable, runtime):
            super().__init__(name, observable, runtime=runtime)
            self.received = []

        async def record(self, value):
            self.received.append(value)

    try:
        first_observable = Observable(runtime=first_runtime)
        second_observable = Observable(runtime=second_runtime)
        first_observer = RecordingObserver("first", first_observable, first_runtime)
        second_observer = RecordingObserver("second", second_observable, second_runtime)

        first_runtime.loop.create_task(
            first_observable.put({"name": "record", "args": ["first event"]})
        )
        first_runtime.loop.create_task(
            first_observable.put({"action": "stop_observer"})
        )
        first_runtime.main_loop([], test=True)

        second_runtime.loop.create_task(
            second_observable.put({"name": "record", "args": ["second event"]})
        )
        second_runtime.loop.create_task(
            second_observable.put({"action": "stop_observer"})
        )
        second_runtime.main_loop([], test=True)

        assert first_observer.received == ["first event"]
        assert second_observer.received == ["second event"]
        assert first_runtime.allObs == [first_observer]
        assert second_runtime.allObs == [second_observer]
        assert first_runtime.allObservables == [first_observable]
        assert second_runtime.allObservables == [second_observable]
    finally:
        first_runtime.close()
        second_runtime.close()