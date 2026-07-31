import asyncio

import pytest
import websockets

from nucosObs.websocketInterface import WebsocketInterface


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