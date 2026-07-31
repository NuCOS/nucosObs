import asyncio
from types import SimpleNamespace

import aiohttp
from aiohttp import web
import pytest

from nucosObs.aiohttpWebsocketInterface import AiohttpWebsocketInterface


class ClosedWebSocket:
    def __init__(self):
        self.closed = False

    async def receive(self, timeout=None):
        return SimpleNamespace(type=aiohttp.WSMsgType.CLOSED)

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_listener_removes_closed_connection_by_default():
    interface = AiohttpWebsocketInterface(web.Application(), asyncio.Queue())
    websocket = ClosedWebSocket()
    connection_id = "connection"
    interface.ws[connection_id] = websocket
    interface.ids.append(connection_id)

    await interface.listener(websocket, connection_id)

    assert connection_id not in interface.ws
    assert connection_id not in interface.ids


@pytest.mark.asyncio
async def test_listener_allows_missing_close_callback():
    broker = asyncio.Queue()
    interface = AiohttpWebsocketInterface(
        web.Application(), broker, closeOnClientQuit=True
    )
    websocket = ClosedWebSocket()
    interface.ws["connection"] = websocket
    interface.ids.append("connection")

    await interface.listener(websocket, "connection")

    assert await broker.get() == "client exit"


@pytest.mark.asyncio
async def test_connect_uses_an_aiohttp_websocket_client():
    async def server_handler(request):
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        await websocket.send_str("hello")
        await websocket.receive()
        return websocket

    server_app = web.Application()
    server_app.router.add_get("/", server_handler)
    runner = web.AppRunner(server_app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    interface = AiohttpWebsocketInterface(web.Application(), asyncio.Queue())
    connect_task = asyncio.create_task(interface.connect("127.0.0.1", port))

    try:
        assert await asyncio.wait_for(interface.broker.get(), timeout=1) == "hello"
        await interface.shutdown()
        await asyncio.wait_for(connect_task, timeout=1)
    finally:
        if not connect_task.done():
            connect_task.cancel()
            await asyncio.gather(connect_task, return_exceptions=True)
        await runner.cleanup()