"""Websocket interface implementation using ``aiohttp``."""

import asyncio as aio
import inspect
import secrets
from aiohttp import web
import aiohttp
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


def _token(length):
    if isCR:
        return random(length).decode()
    return secrets.token_urlsafe(length)


class AiohttpWebsocketInterface(object):
    """A websocket interface based on ``aiohttp``."""
    def __init__(self, app, broker, doAuth=False, closeOnClientQuit=False, 
                    authenticator=None,onCloseCallback=None, heartbeat=None,
                    closeSanely=None,
                    receive_timeout=None, sslClient=None, sslServer=None,
                    route="/ws", backend="default", on_error=None):
        """Create the interface and register a websocket route."""
        self.app = app
        self.onCloseCallback = onCloseCallback
        self.backend = backend
        self.ws = {}
        self.doAuth = doAuth
        self.closeSanely = closeSanely
        self.broker = broker
        self.server = None
        self.authenticator = authenticator
        self.nonce = {}
        self.isAuthenticated = {}
        self.connectedUser = {}
        self.isRefused = []
        self.closeOnClientQuit = closeOnClientQuit
        self.sslClient = sslClient
        self.sslServer = sslServer
        self.client_session = None
        self.approved = []
        self.receive_timeout = receive_timeout
        self.heartbeat = heartbeat
        self.ids = []
        self.id_0 = None
        self.on_error = on_error
        app.router.add_route('GET', route, self.handler)

    async def _report_error(self, context, error):
        if self.on_error is not None:
            result = self.on_error(context, error)
            if inspect.isawaitable(result):
                await result

    async def send(self, msg, user):
        """Send ``msg`` to the websocket connection belonging to ``user``."""
        id_ = self.connectedUser.get(user)
        if id_ is None:
            return
        else:
            try:
                await self.ws[id_].send_str(msg)
            except Exception as error:
                await self._report_error("send", error)

    async def send_by_id(self, msg, id_):
        """
        """
        if id_ in self.ws:
            await self.ws[id_].send_str(msg)

    async def send_by_client(self, msg, client):
        """
        client is the numbering
        wait until connected
        """
        while True:
            try:
                id_ = self.ids[client]
                break
            except:
                # print("SEND failed", self.ids, client, msg)
                await aio.sleep(0.2)
        await self.ws[id_].send_str(msg)
    async def broadcast(self, msg):
        """Send ``msg`` to all connected websocket clients."""
        for id_, ws in self.ws.items():
            try:
                await ws.send_str(msg)
            except Exception as error:
                await self._report_error("broadcast", error)

    async def connect(self, host, port):
        """Connect to a remote websocket server."""
        if debug[-1]:
            print("try to start client")
        # self.server = await websockets.connect(self.handler, ip, port)
        if self.sslClient:
            protocol = "wss"
        else:
            protocol = "ws"
        self.client_session = aiohttp.ClientSession()
        options = {}
        if self.sslClient is not None:
            options["ssl"] = self.sslClient
        websocket = await self.client_session.ws_connect(
            '%s://%s:%s' % (protocol, host, str(port)), **options
        )
        self.ws['client'] = websocket
        await self.listener(websocket, 'client')


    async def handler(self, request):
        """Handle incoming websocket upgrade requests."""
        ws = web.WebSocketResponse(heartbeat=self.heartbeat)
        await ws.prepare(request)
        id_ =  ws.headers.get("Sec-Websocket-Accept")
        self.ws.update({id_: ws})
        self.id_0 = id_
        self.ids.append(id_)  # store the first connection for easier reference
        if debug[-1]:
            print("Partner connected")     
            print(self.ws)   
        if self.doAuth:
            self.nonce[id_] = _token(24)
            context = {"name": "doAuth",
                       "args": {"nonce": self.nonce[id_], "id": id_},
                       "action": "authenticate",
                       "backend": self.backend}
            await ws.send_str(json.dumps(context)) #or send_bytes ??
        try:
            await self.listener(ws, id_)
        except aio.TimeoutError:
            if debug[-1]:
                print("timeout....")
            self.remove_connection(id_)
            await ws.close()
        # NOTE next line is mandatory for preventing a closed websocket to raise exception
        return ws

    async def shutdown(self):
        """Close all websocket connections and notify observers."""
        if debug[-1]:
            print("in shutdown process ...")
        await broadcast.put({"name": "broadcast", "args": [{"action": "stop_observer"}]})
        for websocket in list(self.ws.values()):
            await websocket.close()
        if self.client_session is not None and not self.client_session.closed:
            await self.client_session.close()
                
    async def _closeSanely_(self, id_old, user):
        """
        protects the hard shutdown if the same user is connected once again
        """
        if self.closeSanely:
            try:
                await self.closeSanely(user, id_old)
            except Exception as error:
                await self._report_error("close_sanely", error)
                if debug[-1]:
                    print("closeSanely callback failed:", error)
            await aio.sleep(3.0)
        if id_old in self.ws:
            await self.ws[id_old].close()
        self.remove_connection(id_old)

    async def listener(self, ws, id_):
        """Listen for messages on ``ws`` and forward them to the broker."""
        user = "unknown"
        while True:
            # async for msg in ws: ---> replaced by ...
            # if no message arrives after lately 20 secs the connection is closed
            msg = await ws.receive(timeout=self.receive_timeout)  
            if msg.type == aiohttp.WSMsgType.text:
                data = msg.data
                if id_ not in self.isAuthenticated and self.doAuth:
                    id_out, user = await self.authenticator.startAuth(data, ws, self.nonce[id_])
                    if id_out is not None and id_out == id_:
                        self.isAuthenticated.update({id_: user})
                        if user in self.connectedUser:
                            id_old = self.connectedUser.pop(user)
                            self.isAuthenticated.pop(id_old)
                            try:
                                aio.ensure_future(self._closeSanely_(id_old, user))
                            except:
                                pass
                            finally:
                                if debug[-1]:
                                    print("closed one pending connection of user %s" % user)
                            self.connectedUser.update({user: id_})
                        else:
                            self.connectedUser.update({user: id_})
                        # print(self.connectedUser, self.ws)
                    else:
                        await self._report_error(
                            "authentication", PermissionError("authentication rejected")
                        )
                        await self.ws[id_].close()
                        break
                else:
                    await self.broker.put(data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                print(f"closed by client {user}")
                await self.ws[id_].close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f"error by client {user}")
                await self.ws[id_].close()
                break
            else:
                if debug[-1]:
                    print(f"an unknown text message arrived {msg.type} by {user}")
                await self.ws[id_].close()
                break
        # print("out of order.........")
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
                    if self.onCloseCallback:
                        try:
                            await self.onCloseCallback(user)
                        except Exception as error:
                            await self._report_error("on_close", error)
                            if debug[-1]:
                                print("close callback failed:", error)
        if debug[-1]:
            print("--- connection of %s stopped " % user)
        #if self.onCloseCallback:
        #    await self.onCloseCallback(user)

    def remove_connection(self, id_):
        """Remove a connection from the internal registry."""
        self.ws.pop(id_, None)
        if id_ in self.ids:
            self.ids.remove(id_)
        if id_ in self.isAuthenticated:
            user = self.isAuthenticated.pop(id_)
            if self.connectedUser.get(user) == id_:
                self.connectedUser.pop(user)
        if debug[-1]:
            print("after client left:")
            print("user...",self.connectedUser)
            print("ws.....",self.ws)

