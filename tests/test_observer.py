import asyncio as aio

import nucosObs
from nucosObs.observable import Observable
from nucosObs.observer import Observer, broadcast


class DummyObserver(Observer):
    def __init__(self, name, obs):
        super().__init__(name, obs)
        self.called = False

    async def greet(self, msg):
        self.called = msg
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})


import unittest


class ObserverTests(unittest.TestCase):

    def setUp(self):
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()

    def tearDown(self):
        if not nucosObs.loop.is_closed():
            nucosObs.loop.close()

    def test_event_delivery(self):
        loop = aio.new_event_loop()
        aio.set_event_loop(loop)
        nucosObs.loop = loop

        obs = Observable()
        ob = DummyObserver("O", obs)
        aio.ensure_future(obs.put({"name": "greet", "args": ["hello"]}))
        aio.ensure_future(obs.put({"action": "stop_observer"}))
        nucosObs.main_loop([], test=True)
        self.assertEqual(ob.called, "hello")
        loop.close()

    def test_register_queue(self):
        obs = Observable()
        ob = DummyObserver("O", obs)
        self.assertIn(ob.name, obs.q)
        self.assertIs(ob._queue, obs.q[ob.name])


if __name__ == '__main__':
    unittest.main()
