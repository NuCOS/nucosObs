import asyncio
import json

import pytest
import websockets

from nucosObs import websocketInterface
from nucosObs.websocketInterface import WebsocketInterface


class AcceptAuthenticator:
    async def startAuth(self, message, websocket, nonce):
        payload = json.loads(message)
        return payload["id"], "user"


@pytest.mark.asyncio
async def test_server_accepts_current_websockets_handler_contract():
    broker = asyncio.Queue()
    interface = WebsocketInterface(broker)
    await interface.serve("127.0.0.1", 0)
    port = interface.server.sockets[0].getsockname()[1]

    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws") as client:
            await client.send("hello")
            assert await asyncio.wait_for(broker.get(), timeout=1) == "hello"
    finally:
        interface.server.close()
        await interface.server.wait_closed()


@pytest.mark.asyncio
async def test_authenticated_client_routes_messages_and_is_removed_on_close(monkeypatch):
    monkeypatch.setattr(websocketInterface, "isCR", False)
    broker = asyncio.Queue()
    interface = WebsocketInterface(
        broker,
        doAuth=True,
        closeOnClientQuit=True,
        authenticator=AcceptAuthenticator(),
    )
    await interface.serve("127.0.0.1", 0)
    port = interface.server.sockets[0].getsockname()[1]

    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws") as client:
            challenge = json.loads(await client.recv())
            assert challenge["action"] == "authenticate"
            assert isinstance(challenge["args"]["nonce"], str)

            await client.send(json.dumps({"id": challenge["args"]["id"]}))
            await client.send("authenticated payload")
            assert await asyncio.wait_for(broker.get(), timeout=1) == "authenticated payload"

        assert await asyncio.wait_for(broker.get(), timeout=1) == "client exit"
        assert interface.ws == {}
        assert interface.isAuthenticated == {}
    finally:
        interface.server.close()
        await interface.server.wait_closed()