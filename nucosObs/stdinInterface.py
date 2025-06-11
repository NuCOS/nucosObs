"""Simple stdin based interface to feed observables."""

import sys
import asyncio as aio

from nucosObs import loop, debug
from nucosObs.observer import broadcast

class StdinInterface(object):
    """Interface reading commands from ``stdin``."""

    def __init__(self, observable):
        """Create the interface and attach ``observable`` for output."""
        self.loop = loop
        self.q = aio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)
        self.observable = observable
        self.stop = False

    def got_input(self):
        """Callback for the event loop when input is available."""
        aio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    async def get_ui(self):
        """Coroutine processing the input queue and dispatching commands."""
        out = []
        while not self.stop:
            out = (await self.q.get()).strip()
            if "leave_in" in out:
                # wait async and leave
                print(out)
                self.stop = True
                t = float(out[-1])
                await aio.sleep(t)
                await self.observable.put({"name": "shutdown", "args": []})
                break
            elif out.endswith('x'):
                await self.observable.put({"name": "shutdown", "args": []})
                break
            elif out.endswith('say'):
                await self.observable.put({"name": "say", "args": []})
            elif 'fact' in out:
                await self.observable.put({"name": "fact", "args": [out.split(" ")[-1]]})
            else:
                await self.observable.put(out)
        if debug[-1]:
            print("Stdin-Interface stopped")

