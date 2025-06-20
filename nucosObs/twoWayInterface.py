"""Interface sending and receiving directives between observables."""

import sys
import asyncio as aio

from nucosObs import loop, debug
from nucosObs.observer import broadcast

class TwoWayInterface(object):
    """Interface that forwards messages between multiple observables."""

    def __init__(self, observables_dict, send_all=False):
        """Create interface with mapping of names to observables."""
        self.loop = loop
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
            directive = await self.q.get()
            if debug[-1]:
                print("interface received", directive)
            if "action" in directive:
                action = directive["action"]
                if "waitTime" in action:
                    # just wait
                    t = float(action[-1])
                    await aio.sleep(t)
                    continue
                if action.endswith('stop interface'):
                    # broadcast here the stop event
                    await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
                    break
                if "leave_in" in action:
                    # wait async and leave
                    t = float(action[-1])
                    await aio.sleep(t)
                    break
            if "obs" in directive:
                nameObs = directive.pop("obs")
                if nameObs in self.observables_dict:
                    await self.observables_dict[nameObs].put(directive)
            elif self.send_all:
                for k,v in self.observables_dict.items():
                    print("send to ",k)
                    await v.put(directive)


        if debug[-1]:
            print("--- Interface stopped")
