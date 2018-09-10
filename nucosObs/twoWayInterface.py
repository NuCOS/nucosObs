import sys
import asyncio as aio

from nucosObs import loop, debug
from nucosObs.observer import broadcast

class TwoWayInterface(object):
    def __init__(self, observables_dict, send_all=False):
        self.loop = loop
        self.q = aio.Queue(loop=self.loop)
        self.observables_dict = observables_dict
        self.stop = False
        self.send_all = send_all

    async def put(self, txt):
        await self.q.put(txt)

    async def get_ui(self):
        self.stop = False
        while not self.stop:
            out = (await self.q.get()).strip()
            if debug[-1]:
                print("interface received", out)
            if "waitTime" in out:
                # just wait
                t = float(out[-1])
                await aio.sleep(t)
                continue
            if out.endswith('stop interface'):
                # broadcast here the stop event
                await broadcast.put("broadcast stop")
                break
            elements = out.split(" ")
            if elements[0] in self.observables_dict:
                msg = " ".join(elements[1:])
                await self.observables_dict[elements[0]].put(msg)
            elif self.send_all:
                for k,v in self.observables_dict.items():
                    await v.put(out)
            if "leave_in" in out:
                # wait async and leave
                self.stop = True
                t = float(out[-1])
                await aio.sleep(t)

        if debug[-1]:
            print("Interface stopped")
