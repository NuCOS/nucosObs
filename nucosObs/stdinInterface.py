import sys
import asyncio as aio

from nucosObs import loop, debug
from nucosObs.observer import broadcast

class StdinInterface(object):
    def __init__(self, observable):
        self.loop = loop
        self.q = aio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)
        self.observable = observable
        self.stop = False

    def got_input(self):
        aio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    async def get_ui(self):
        out = []
        while not self.stop:
            out = (await self.q.get()).strip()
            if "leave_in" in out:
                # wait async and leave
                print(out)
                self.stop = True
                t = float(out[-1])
                await aio.sleep(t)
                await self.observable.put("shutdown")
                break
            if out.endswith('x'):
                await self.observable.put("shutdown")
                break
            await self.observable.put(out)
        if debug[-1]:
            print("Stdin-Interface stopped")

