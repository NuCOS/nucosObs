"""Helper functions and globals used by ``nucosObs``."""

import asyncio as aio
from .version import version as __version__
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

    async def run_all():
        await aio.gather(*ui, *obs, *schedules)

    loop.run_until_complete(run_all())
    if debug[-1] and not test:
        print("try to close loop")
    if not test:
        loop.close()


# from nucosObs.observable import Observable
# from nucosObs.observer import BroadcastObserver
