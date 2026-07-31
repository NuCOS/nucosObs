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


class RejectAuthenticator:
    async def startAuth(self, message, websocket, nonce):
        return None, "user"


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


@pytest.mark.asyncio
async def test_rejected_client_is_closed_and_all_state_is_removed(monkeypatch):
    monkeypatch.setattr(websocketInterface, "isCR", False)
    interface = WebsocketInterface(
        asyncio.Queue(), doAuth=True, authenticator=RejectAuthenticator()
    )
    await interface.serve("127.0.0.1", 0)
    port = interface.server.sockets[0].getsockname()[1]

    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws") as client:
            challenge = json.loads(await client.recv())
            connection_id = challenge["args"]["id"]
            await client.send(json.dumps({"id": connection_id}))
            with pytest.raises(websockets.ConnectionClosed):
                await asyncio.wait_for(client.recv(), timeout=1)

        for _ in range(100):
            if not interface.ws:
                break
            await asyncio.sleep(0.01)

        assert interface.ws == {}
        assert interface.isAuthenticated == {}
        assert interface.nonce == {}
    finally:
        interface.server.close()
        await interface.server.wait_closed()