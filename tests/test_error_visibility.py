import asyncio

import pytest
from aiohttp import web

from nucosObs import Runtime
from nucosObs.aiohttpWebsocketInterface import AiohttpWebsocketInterface
from nucosObs.observable import Observable
from nucosObs.observer import Observer


class FailingSocket:
    async def send_str(self, message):
        raise RuntimeError("send failed")


class FailingObserver(Observer):
    async def fail(self):
        raise RuntimeError("handler failed")


@pytest.mark.asyncio
async def test_observer_reports_handler_error_before_preserving_exception():
    errors = []
    runtime = Runtime(loop=asyncio.get_running_loop())
    observable = Observable(runtime=runtime)
    observer = FailingObserver(
        "failing", observable, on_error=lambda context, error: errors.append((context, error))
    )

    try:
        task = asyncio.create_task(observer.observe())
        await observable.put({"name": "fail", "args": []})

        with pytest.raises(RuntimeError, match="handler failed"):
            await task

        assert [(context, type(error), str(error)) for context, error in errors] == [
            ("handler", RuntimeError, "handler failed")
        ]
    finally:
        runtime.pool.shutdown()


@pytest.mark.asyncio
async def test_aiohttp_interface_reports_failed_send_without_raising():
    errors = []
    interface = AiohttpWebsocketInterface(
        web.Application(),
        asyncio.Queue(),
        on_error=lambda context, error: errors.append((context, error)),
    )
    interface.connectedUser["user"] = "connection"
    interface.ws["connection"] = FailingSocket()

    await interface.send("message", "user")

    assert [(context, type(error), str(error)) for context, error in errors] == [
        ("send", RuntimeError, "send failed")
    ]