"""Helper functions and globals used by ``nucosObs``."""

import asyncio as aio

from concurrent.futures import ThreadPoolExecutor
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


def main_loop(ui, test=False):
    """Run the event loop with all observers and optional UI coroutines."""
    # the workers should be closed first
    obs = [o.observe() for o in allObs]
    if debug[-1]:
        print([o.name for o in allObs])
    schedules = [o.scheduleLoop()
                 for o in allObs if o.schedule_task is not None]
    loop.run_until_complete(aio.gather(*ui, *obs, *schedules))
    if debug[-1]:
        print("try to shutdown pool")
    pool.shutdown(wait=False)
    if debug[-1] and not test:
        print("try to close loop")
    if not test:
        loop.close()


# from nucosObs.observable import Observable
# from nucosObs.observer import BroadcastObserver
