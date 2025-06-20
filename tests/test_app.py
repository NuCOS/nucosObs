import asyncio as aio
import unittest

import nucosObs
from nucosObs.observable import Observable, NoConcurrentObserver
from nucosObs.observer import Observer


class DummyObserver(Observer):
    def __init__(self, name, obs, concurrent=None):
        if concurrent is None:
            concurrent = []
        super().__init__(name, obs, concurrent)
        self.received = []

    async def greet(self, msg):
        self.received.append(msg)


class DebugTests(unittest.TestCase):
    def setUp(self):
        nucosObs.debug.clear()

    def tearDown(self):
        nucosObs.debug.clear()

    def test_debug_append(self):
        nucosObs.debug.append(False)
        self.assertIn(False, nucosObs.debug)
        self.assertEqual(len(nucosObs.debug), 1)

    def test_debug_multiple(self):
        nucosObs.debug.append(False)
        nucosObs.debug.append(True)
        nucosObs.debug.append("msg")
        self.assertEqual(len(nucosObs.debug), 3)
        self.assertIn(True, nucosObs.debug)
        self.assertIn("msg", nucosObs.debug)

    def test_debug_clear(self):
        nucosObs.debug.extend([1, 2, 3])
        nucosObs.debug.clear()
        self.assertEqual(nucosObs.debug, [])

    def test_debug_contains(self):
        nucosObs.debug.append("value")
        self.assertTrue("value" in nucosObs.debug)
        self.assertFalse("other" in nucosObs.debug)


class ObservableTests(unittest.TestCase):
    def setUp(self):
        self.loop = aio.new_event_loop()
        aio.set_event_loop(self.loop)
        nucosObs.loop = self.loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()
        nucosObs.debug[:] = [False]

    def tearDown(self):
        if not self.loop.is_closed():
            self.loop.close()
        nucosObs.debug[:] = [False]
        nucosObs.debug[:] = [False]

    def test_multiple_observers_receive_events(self):
        obs = Observable()
        ob1 = DummyObserver("A", obs)
        ob2 = DummyObserver("B", obs)
        aio.ensure_future(obs.put({"name": "greet", "args": ["hi"]}))
        aio.ensure_future(obs.put({"action": "stop_observer"}))
        nucosObs.main_loop([], test=True)
        self.assertEqual(ob1.received, ["hi"])
        self.assertEqual(ob2.received, ["hi"])

    def test_concurrent_registration(self):
        obs = Observable()
        ob1 = DummyObserver("A", obs)
        ob2 = DummyObserver("B", obs, concurrent=["A"])
        self.assertIs(ob1._queue, ob2._queue)

    def test_unknown_concurrent_raises(self):
        obs = Observable()
        DummyObserver("A", obs)
        with self.assertRaises(NoConcurrentObserver):
            DummyObserver("B", obs, concurrent=["X"])


class ObserverParseTests(unittest.TestCase):
    def setUp(self):
        self.loop = aio.new_event_loop()
        aio.set_event_loop(self.loop)
        nucosObs.loop = self.loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()
        nucosObs.debug[:] = [False]

    def tearDown(self):
        if not self.loop.is_closed():
            self.loop.close()
        nucosObs.debug[:] = [False]

    def test_parse_dict_and_string(self):
        obs = Observable()

        class PObserver(Observer):
            async def hello(self, *args):
                pass

        ob = PObserver("P", obs)
        ok, method, args = ob.parse({"name": "hello", "args": [1, 2]})
        self.assertTrue(ok)
        self.assertEqual(method.__name__, "hello")
        self.assertIs(method.__self__, ob)
        self.assertEqual(args, [1, 2])

        ok, method, args = ob.parse("hello 3 4")
        self.assertTrue(ok)
        self.assertEqual(method.__name__, "hello")
        self.assertIs(method.__self__, ob)
        self.assertEqual(args, ["3", "4"])

    def test_parse_invalid(self):
        obs = Observable()
        ob = DummyObserver("D", obs)
        ok, method, args = ob.parse({"name": "does_not_exist"})
        self.assertFalse(ok)
        self.assertIsNone(method)


class BridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.loop = aio.get_running_loop()
        nucosObs.loop = self.loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()
        nucosObs.debug[:] = [False]

    async def test_bridge_call(self):
        obs = Observable()
        ob = DummyObserver("B", obs)
        called = []

        async def hook(val):
            called.append(val)

        ob.set_bridge_method("send", hook)
        await ob.bridge("send", 5)
        self.assertEqual(called, [5])


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.loop = aio.new_event_loop()
        aio.set_event_loop(self.loop)
        nucosObs.loop = self.loop
        nucosObs.allObs.clear()
        nucosObs.allObservables.clear()
        nucosObs.debug[:] = [False]

    def tearDown(self):
        if not self.loop.is_closed():
            self.loop.close()

    def test_schedule_regular(self):
        obs = Observable()

        class SObserver(DummyObserver):
            async def tick(self):
                self.flag = True
                self.stop = True

        ob = SObserver("S", obs)
        ob.flag = False
        ob.scheduleRegular(ob.tick, 0.01)
        aio.ensure_future(obs.put({"action": "stop_observer"}))
        nucosObs.main_loop([], test=True)
        self.assertTrue(ob.flag)

