
import asyncio as aio

from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(4)
allObs = []
allObservables = []

loop = aio.get_event_loop()
debug = [False]


def get_all_pending_futures(ui=[]):
    obs = [o.observe for o in allObs]
    schedules = [o.scheduleLoop
                 for o in allObs if o.schedule_task is not None]
    return [*ui, *obs, *schedules]


def main_loop(ui, test=False):
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
