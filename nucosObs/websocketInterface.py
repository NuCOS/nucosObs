"""Basic ``websockets`` based interface for observers."""

import websockets
import asyncio as aio
import inspect
import secrets
try:
    import simplejson as json
except:
    import json

try:
    from nucosCR import random, hexdigest_n
    isCR = True
except:
    import random
    isCR = False

from nucosObs import loop, debug
from nucosObs.observer import broadcast
# debug.append(True)


def _token(length):
    if isCR:
        return random(length).decode()
    return secrets.token_urlsafe(length)


class WebsocketInterface(object):
    """Simple websocket server/client using the ``websockets`` package."""

    def __init__(self,
                 broker,
                 doAuth=False,
                 closeOnClientQuit=False,
                 authenticator=None,
                 sslClient=None,
                 sslServer=None,
                 on_error=None):
        """Initialize the interface and optionally enable authentication."""
        self.ws = {}
        self.doAuth = doAuth
        self.broker = broker
        self.server = None
        self.authenticator = authenticator
        self.nonce = {}
        self.isAuthenticated = {}
        self.isRefused = []
        self.closeOnClientQuit = closeOnClientQuit
        self.sslClient = sslClient
        self.sslServer = sslServer
        self.approved = []
        self.on_error = on_error

    async def _report_error(self, context, error):
        if self.on_error is not None:
            result = self.on_error(context, error)
            if inspect.isawaitable(result):
                await result

    async def broadcast(self, msg, client=None):
        """Broadcast ``msg`` to all clients or to ``client`` if given."""
        for i, antenna in enumerate(self.ws.values()):
            if client is None or i == client:
                try:
                    await antenna.send(msg)
                except Exception as error:
                    await self._report_error("broadcast", error)

    async def connect(self, host, port):
        """Connect as a client to ``host`` and ``port``."""
        if debug[-1]:
            print("try to start client")
        # self.server = await websockets.connect(self.handler, ip, port)
        if self.sslClient:
            protocol = "wss"
        else:
            protocol = "ws"
        websocket = await websockets.connect('%s://%s:%s/ws' % (protocol, host, str(port)), ssl=self.sslClient)
        self.ws['client'] = websocket
        await self.listener(websocket, 'client')

    async def serve(self, ip, port):
        """Start a websocket server bound to ``ip``/``port``."""
        if debug[-1]:
            print("try to start server")
        self.server = await websockets.serve(self.handler, ip, port, ssl=self.sslServer)
        print("started server", self.server)

    async def handler(self, websocket):
        """Handle a single websocket connection."""
        id_ = _token(12)
        self.ws[id_] = websocket
        if debug[-1]:
            print("Partner connected")        
        if self.doAuth:
            self.nonce[id_] = _token(24)
            context = {"name": "doAuth",
                       "args": {"nonce": self.nonce[id_], "id": id_},
                       "action": "authenticate"}
            await self.ws[id_].send(json.dumps(context))
        await self.listener(self.ws[id_], id_)

    async def shutdown(self):
        """Close all open connections and inform observers."""
        if debug[-1]:
            print("in shutdown process ...")
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
        if self.server is not None:
            for k in [x for x in self.ws.keys()]:
                await self.ws[k].close()

    def remove_connection(self, id_):
        """Remove all state associated with a websocket connection."""
        self.ws.pop(id_, None)
        self.nonce.pop(id_, None)
        self.isAuthenticated.pop(id_, None)

    async def listener(self, ws, id_):
        """Read messages from ``ws`` and route them to the broker."""
        user = "unknown"
        while True:
            try:
                msg = await ws.recv()
            except websockets.ConnectionClosed:
                if id_ == "client":
                    await self.shutdown()
                else:
                    self.remove_connection(id_)
                    if self.closeOnClientQuit:
                        if debug[-1]:
                            print("client died ...")
                        if len(self.ws) == 0:
                            await self.broker.put("client exit")
                            await self.shutdown()
                break

            if id_ not in self.isAuthenticated and self.doAuth:
                id_out, user = await self.authenticator.startAuth(msg, ws, self.nonce[id_])
                if id_out is not None and id_out == id_:
                    self.isAuthenticated.update({id_: user})
                else:
                    await self._report_error(
                        "authentication", PermissionError("authentication rejected")
                    )
                    self.remove_connection(id_)
                    await ws.close()
                    break
            else:
                await self.broker.put(msg)

        if debug[-1]:
            print("--- connection of %s stopped " % user)
