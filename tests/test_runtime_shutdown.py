import asyncio

from nucosObs import Runtime
from nucosObs.observable import Observable
from nucosObs.observer import Observer


def test_runtime_shutdown_reports_clean_and_repeated_shutdown():
    runtime = Runtime()

    try:
        first_report = runtime.loop.run_until_complete(runtime.shutdown())
        second_report = runtime.loop.run_until_complete(runtime.shutdown())

        assert first_report == {
            "already_shutdown": False,
            "observers": {"total": 0, "open": 0},
            "tasks": {"pending": 0, "cancelled": 0},
        }
        assert second_report == {
            "already_shutdown": True,
            "observers": {"total": 0, "open": 0},
            "tasks": {"pending": 0, "cancelled": 0},
        }
    finally:
        runtime.close()


def test_runtime_shutdown_stops_observers_and_cancels_runtime_tasks():
    runtime = Runtime()
    observable = Observable(runtime=runtime)
    observer = Observer("scheduled", observable, runtime=runtime)

    async def tick():
        await asyncio.sleep(1)

    try:
        observer.scheduleRegular(tick, 1)
        observer.startSchedule()
        report = runtime.loop.run_until_complete(runtime.shutdown())

        assert observer.stop
        assert observer.stopScheduleLoop
        assert report["observers"] == {"total": 1, "open": 1}
        assert report["tasks"] == {"pending": 1, "cancelled": 1}
    finally:
        runtime.close()