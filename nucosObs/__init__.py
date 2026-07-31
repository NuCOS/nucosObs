"""Helper functions and globals used by ``nucosObs``."""

import asyncio as aio
from .version import version as __version__
from concurrent.futures import ThreadPoolExecutor


class Runtime:
    """Own the event loop and mutable state for an observer application."""

    def __init__(self, loop=None):
        self.loop = loop or aio.new_event_loop()
        self.pool = ThreadPoolExecutor(4)
        self.allObs = []
        self.allObservables = []
        self.debug = [False]
        self._tasks = set()
        self._shutdown = False

    def create_task(self, coroutine):
        """Create and track work owned by this runtime."""
        task = self.loop.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self):
        """Request observer shutdown and return a structured state report."""
        open_observers = [observer for observer in self.allObs if not observer.stop]
        pending_tasks = [task for task in self._tasks if not task.done()]
        report = {
            "already_shutdown": self._shutdown,
            "observers": {
                "total": len(self.allObs),
                "open": len(open_observers),
            },
            "tasks": {"pending": len(pending_tasks), "cancelled": 0},
        }
        if self._shutdown:
            return report

        self._shutdown = True
        for observer in self.allObs:
            observer.stop = True
            observer.stopSchedule()
        for observable in self.allObservables:
            await observable.put({"action": "stop_observer"})
        for task in pending_tasks:
            task.cancel()
        if pending_tasks:
            await aio.gather(*pending_tasks, return_exceptions=True)
        report["tasks"]["cancelled"] = len(pending_tasks)
        return report

    def main_loop(self, ui, test=False):
        """Run this runtime's observers and optional UI coroutines."""
        _run_main_loop(self, ui, test)

    def close(self):
        """Release this runtime's worker pool and event loop."""
        self.pool.shutdown(wait=False)
        if not self.loop.is_closed():
            self.loop.close()


pool = ThreadPoolExecutor(4)
allObs = []
allObservables = []

# Create a default event loop on import so that modules relying on the loop
# do not trigger a deprecation warning with ``get_event_loop``.
loop = aio.new_event_loop()
aio.set_event_loop(loop)
debug = [False]


def get_all_pending_futures(ui=[]):
    """Return coroutines for all registered observers and schedules."""
    obs = [o.observe for o in allObs]
    schedules = [o.scheduleLoop
                 for o in allObs if o.schedule_task is not None]
    return [*ui, *obs, *schedules]


def _run_main_loop(runtime, ui, test=False):
    """Run the event loop with all observers and optional UI coroutines."""
    # the workers should be closed first
    obs = [o.observe() for o in runtime.allObs]
    if runtime.debug[-1]:
        print([o.name for o in runtime.allObs])
    schedules = [o.scheduleLoop()
                 for o in runtime.allObs if o.schedule_task is not None]

    async def run_all():
        await aio.gather(*ui, *obs, *schedules)

    runtime.loop.run_until_complete(run_all())
    if runtime.debug[-1] and not test:
        print("try to close loop")
    if not test:
        runtime.loop.close()


def main_loop(ui, test=False):
    """Run the default module runtime with observers and UI coroutines."""
    _run_main_loop(__import__(__name__), ui, test)


# from nucosObs.observable import Observable
# from nucosObs.observer import BroadcastObserver
