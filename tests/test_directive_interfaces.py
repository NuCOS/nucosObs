import asyncio
import io

import pytest

from nucosObs.stdinInterface import StdinInterface
from nucosObs.twoWayInterface import TwoWayInterface


class RecordingObservable:
    def __init__(self):
        self.events = []

    async def put(self, event):
        self.events.append(event)


@pytest.mark.asyncio
async def test_stdin_interface_dispatches_commands_and_stops_cleanly():
    observable = RecordingObservable()
    interface = StdinInterface(
        observable,
        input_stream=io.StringIO("say\n"),
        loop=asyncio.get_running_loop(),
    )
    interface.got_input()
    await asyncio.sleep(0)
    task = asyncio.create_task(interface.get_ui())

    await interface.q.put("fact 42\n")
    await interface.q.put("x\n")
    await asyncio.wait_for(task, timeout=1)

    assert observable.events == [
        {"name": "say", "args": []},
        {"name": "fact", "args": ["42"]},
        {"name": "shutdown", "args": []},
    ]
    assert interface.stop


@pytest.mark.asyncio
async def test_stdin_interface_supports_multi_digit_leave_delay():
    observable = RecordingObservable()
    interface = StdinInterface(observable, loop=asyncio.get_running_loop())
    task = asyncio.create_task(interface.get_ui())

    await interface.q.put("leave_in 0.0\n")
    await asyncio.wait_for(task, timeout=1)

    assert observable.events == [{"name": "shutdown", "args": []}]
    assert interface.stop


@pytest.mark.asyncio
async def test_two_way_interface_routes_without_mutating_directive():
    target = RecordingObservable()
    interface = TwoWayInterface({"target": target})
    directive = {"obs": "target", "name": "work", "args": ["value"]}
    task = asyncio.create_task(interface.get_ui())

    await interface.put(directive)
    await interface.put({"action": "stop interface"})
    await asyncio.wait_for(task, timeout=1)

    assert directive == {"obs": "target", "name": "work", "args": ["value"]}
    assert target.events == [{"name": "work", "args": ["value"]}]
    assert interface.stop


@pytest.mark.asyncio
async def test_two_way_interface_sends_to_all_and_honors_wait_directive():
    first = RecordingObservable()
    second = RecordingObservable()
    interface = TwoWayInterface({"first": first, "second": second}, send_all=True)
    task = asyncio.create_task(interface.get_ui())

    await interface.put({"action": "waitTime 0.0"})
    await interface.put({"name": "broadcast", "args": ["value"]})
    await interface.put({"action": "leave_in 0.0"})
    await asyncio.wait_for(task, timeout=1)

    expected = {"name": "broadcast", "args": ["value"]}
    assert first.events == [expected]
    assert second.events == [expected]
    assert interface.stop