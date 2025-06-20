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
        # `asyncio.Queue` does not take a loop parameter since Python 3.8
        # and specifying it raises an exception on modern versions.
        self.q = aio.Queue()
        try:
            # In test environments ``stdin`` might not be a real file
            # object which would raise ``ValueError`` when registering a
            # reader. Ignore such failures so the interface can still be
            # constructed.
            self.loop.add_reader(sys.stdin, self.got_input)
        except (ValueError, NotImplementedError):
            pass
        self.observable = observable
        self.stop = False

    def got_input(self):
        """Callback for the event loop when input is available."""
        # Schedule putting the input into the queue on the running loop
        self.loop.create_task(self.q.put(sys.stdin.readline()))

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

