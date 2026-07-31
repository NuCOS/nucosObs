"""Interface sending and receiving directives between observables."""

import asyncio as aio

import nucosObs
from nucosObs import debug
from nucosObs.observer import broadcast

class TwoWayInterface(object):
    """Interface that forwards messages between multiple observables."""

    def __init__(self, observables_dict, send_all=False):
        """Create interface with mapping of names to observables."""
        self.loop = nucosObs.loop
        # Remove deprecated loop parameter when creating the queue
        self.q = aio.Queue()
        self.observables_dict = observables_dict
        self.stop = False
        self.send_all = send_all

    async def put(self, txt):
        """Put a new directive into the internal queue."""
        await self.q.put(txt)

    async def get_ui(self):
        """Process directives from :func:`put` until a stop command arrives."""
        self.stop = False
        while not self.stop:
            directive = dict(await self.q.get())
            if debug[-1]:
                print("interface received", directive)
            if "action" in directive:
                action = directive["action"]
                if "waitTime" in action:
                    t = float(action.split()[-1])
                    await aio.sleep(t)
                    continue
                if action.endswith('stop interface'):
                    self.stop = True
                    await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
                    break
                if "leave_in" in action:
                    self.stop = True
                    t = float(action.split()[-1])
                    await aio.sleep(t)
                    break
            if "obs" in directive:
                nameObs = directive.pop("obs")
                if nameObs in self.observables_dict:
                    await self.observables_dict[nameObs].put(directive)
            elif self.send_all:
                for observable in self.observables_dict.values():
                    await observable.put(dict(directive))


        if debug[-1]:
            print("--- Interface stopped")
