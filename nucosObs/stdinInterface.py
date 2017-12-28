import sys
import asyncio as aio

from nucosObs import loop, debug

class StdinInterface(object):
    def __init__(self, observable):
        self.loop = loop
        self.q = aio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)
        self.observable = observable

    def got_input(self):
        aio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    async def get_ui(self):
        out = []
        while True:
            out = (await self.q.get()).strip()
            if out.endswith('x'):
                await self.observable.put("stop")
                break
            await self.observable.put(out)
        if debug[-1]:
            print("STDI stopped")

