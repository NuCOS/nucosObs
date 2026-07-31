import asyncio
from types import SimpleNamespace

import aiohttp
from aiohttp import web
import pytest

from nucosObs import aiohttpWebsocketInterface
from nucosObs.aiohttpWebsocketInterface import AiohttpWebsocketInterface


class ClosedWebSocket:
    def __init__(self):
        self.closed = False

    async def receive(self, timeout=None):
        return SimpleNamespace(type=aiohttp.WSMsgType.CLOSED)

    async def close(self):
        self.closed = True


class AcceptAuthenticator:
    async def startAuth(self, message, websocket, nonce):
        return message, "user"


class RejectAuthenticator:
    async def startAuth(self, message, websocket, nonce):
        return None, "user"


async def start_interface_server(interface):
    runner = web.AppRunner(interface.app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, f"ws://127.0.0.1:{port}/ws"


async def authenticate(client):
    challenge = await client.receive_json()
    assert challenge["action"] == "authenticate"
    assert isinstance(challenge["args"]["nonce"], str)
    await client.send_str(challenge["args"]["id"])
    return challenge["args"]["id"]


async def wait_for(predicate):
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("server state did not reach the expected condition")


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


@pytest.mark.asyncio
async def test_authenticated_client_routes_messages_and_replaces_previous_connection(monkeypatch):
    monkeypatch.setattr(aiohttpWebsocketInterface, "isCR", False)
    broker = asyncio.Queue()
    interface = AiohttpWebsocketInterface(
        web.Application(), broker, doAuth=True, authenticator=AcceptAuthenticator()
    )
    runner, url = await start_interface_server(interface)
    session = aiohttp.ClientSession()

    try:
        first_client = await session.ws_connect(url)
        first_id = await authenticate(first_client)
        await wait_for(lambda: interface.connectedUser == {"user": first_id})
        assert interface.connectedUser == {"user": first_id}

        second_client = await session.ws_connect(url)
        second_id = await authenticate(second_client)
        await asyncio.wait_for(first_client.receive(), timeout=1)
        await wait_for(lambda: interface.connectedUser == {"user": second_id})
        await wait_for(lambda: first_id not in interface.ws)

        assert interface.connectedUser == {"user": second_id}
        assert first_id not in interface.ws
        assert interface.isAuthenticated == {second_id: "user"}

        await second_client.send_str("authenticated payload")
        assert await asyncio.wait_for(broker.get(), timeout=1) == "authenticated payload"
        await first_client.close()
        await second_client.close()
    finally:
        await session.close()
        await runner.cleanup()


@pytest.mark.asyncio
async def test_rejected_authentication_closes_and_removes_connection(monkeypatch):
    monkeypatch.setattr(aiohttpWebsocketInterface, "isCR", False)
    interface = AiohttpWebsocketInterface(
        web.Application(),
        asyncio.Queue(),
        doAuth=True,
        authenticator=RejectAuthenticator(),
    )
    runner, url = await start_interface_server(interface)
    session = aiohttp.ClientSession()

    try:
        client = await session.ws_connect(url)
        connection_id = await authenticate(client)
        closed_message = await asyncio.wait_for(client.receive(), timeout=1)
        await wait_for(lambda: connection_id not in interface.ws)

        assert closed_message.type in {aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED}
        assert connection_id not in interface.ws
        assert interface.isAuthenticated == {}
        await client.close()
    finally:
        await session.close()
        await runner.cleanup()


@pytest.mark.asyncio
async def test_receive_timeout_removes_idle_connection():
    interface = AiohttpWebsocketInterface(
        web.Application(), asyncio.Queue(), receive_timeout=0.01
    )
    runner, url = await start_interface_server(interface)
    session = aiohttp.ClientSession()

    try:
        client = await session.ws_connect(url)
        closed_message = await asyncio.wait_for(client.receive(), timeout=1)

        assert closed_message.type in {aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED}
        assert interface.ws == {}
        assert interface.ids == []
        await client.close()
    finally:
        await session.close()
        await runner.cleanup()


@pytest.mark.asyncio
async def test_close_callback_failure_does_not_undo_cleanup():
    async def failing_callback(user):
        raise RuntimeError("callback failure")

    interface = AiohttpWebsocketInterface(
        web.Application(),
        asyncio.Queue(),
        closeOnClientQuit=True,
        onCloseCallback=failing_callback,
    )
    websocket = ClosedWebSocket()
    interface.ws["connection"] = websocket
    interface.ids.append("connection")

    await interface.listener(websocket, "connection")

    assert interface.ws == {}
    assert interface.ids == []