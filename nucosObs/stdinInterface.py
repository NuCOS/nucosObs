"""Simple stdin based interface to feed observables."""

import sys
import asyncio as aio

import nucosObs
from nucosObs import debug
from nucosObs.observer import broadcast

class StdinInterface(object):
    """Interface reading commands from ``stdin``."""

    def __init__(self, observable, input_stream=None, loop=None):
        """Create the interface and attach ``observable`` for output."""
        self.observable = observable
        self.input_stream = input_stream or sys.stdin
        self.loop = loop or getattr(observable, "loop", nucosObs.loop)
        self.q = aio.Queue()
        try:
            self.loop.add_reader(self.input_stream, self.got_input)
        except (OSError, ValueError, NotImplementedError):
            pass
        self.stop = False

    def got_input(self):
        """Callback for the event loop when input is available."""
        self.loop.create_task(self.q.put(self.input_stream.readline()))

    async def get_ui(self):
        """Coroutine processing the input queue and dispatching commands."""
        out = []
        while not self.stop:
            out = (await self.q.get()).strip()
            if "leave_in" in out:
                self.stop = True
                t = float(out.split()[-1])
                await aio.sleep(t)
                await self.observable.put({"name": "shutdown", "args": []})
                break
            elif out.endswith('x'):
                self.stop = True
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

