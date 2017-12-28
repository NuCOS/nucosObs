import asyncio as aio

from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(4)
allObs = []
allObservables = []

loop = aio.get_event_loop()
debug = [False]

def main_loop(ui):
    # the workers should be closed first
    obs = [o.observe() for o in allObs]
    loop.run_until_complete(aio.gather(*ui, *obs))
    if debug[-1]:
        print("try to shutdown pool")
    pool.shutdown(wait=True)
    if debug[-1]:
        print("try to close loop")
    loop.close()

from nucosObs.observable import Observable
from nucosObs.observer import BroadcastObserver

broadcast = Observable()
broadcastObserver = BroadcastObserver("broadcastObserver", broadcast)
