import websockets
import asyncio as aio
import ssl 
try:
    import simplejson as json
except:
    import json
from nucosCR import hexdigest_n

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread, broadcast
from nucosObs.observable import Observable
from nucosObs.websocketInterface import WebsocketInterface
from logger import Logger
logger = Logger("Logger")
logger.level("INFO")



debug.append(True)

messageBroker = Observable()
user = Observable()
server_cert = 'server.crt'
server_key = 'server.key'
client_certs = 'client.crt'

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) # ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)
# for testing puprose ...
users = {'test-user': '7d0bff4edd541774e07692b71c8f1af082682d6f1b158e1c29e156d1838c624b'}

def authenticate(id_, user, nonce, challenge):
    # pre = hexdigest_n('test123', 100)
    # print("PRE local", pre)
    digest = hexdigest_n(users[user] + nonce, 100)
    # print(digest, challenge, pre)
    return digest == challenge

def check_session_key(key, user):
    return True

class Authenticator():
    def __init__(self):
        self.approved = False

    async def startAuth(self, msg, wsi, nonce):
        inp = json.loads(msg)
        args = inp["args"]
        try:
            user, challenge, id_ = args["user"], args["challenge"], args["id"]
        except:
            return None, user
        if debug[-1]:
            print("start auth", msg)
        if authenticate(id_, user, nonce, challenge):
            context = {"name": "finalizeAuth",
                       "args": {"authenticated": True, "id": id_},
                       "action": "authenticated"}
            await wsi.send(json.dumps(context))
            if debug[-1]:
                print("Authenticate accepted of user %s" % user)
            return id_, user
        else:
            context = {"name": "finalizeAuth",
                       "args": {"authenticated": False, "id": id_},
                       "action": "authenticated"}
            await wsi.send(json.dumps(context))
            if debug[-1]:
                print("Authenticate refused")
            return None, user


class WebsocketObserver(Observer):
    def __init__(self, name, observable, wsi, concurrent=[]):
        super(WebsocketObserver, self).__init__(name, observable, concurrent)
        self.wsi = wsi

    async def send(self, user, session_key, msg):
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        if check_session_key(session_key, user):
            await self.wsi.ws[session_key].send(msg)
            logger.log(lvl="INFO", msg="message send: %s %s" % (user, msg))

    def parse(self, item):
        logger.log(lvl="INFO", msg="message received: %s" % item)
        try:
            item = json.loads(item)
        except:
            logger.log("WARNING", msg="no json found ... do nothing")
            return False, None, None
        return super(WebsocketObserver, self).parse(item)

    async def addUser(self, user, session_key, new_user, secret):
        logger.log(lvl="INFO", msg="addUser called %s %s" % (user, new_user))
        if user == "admin":
            logger.log(lvl="INFO", msg="new user added %s" % new_user)
            cache.set(new_user, secret)
        msg = {
               "name": "logger",
               "args": {"log": "addUser called"}
              }
        await self.send(user, session_key, msg)
    



wsi = WebsocketInterface(messageBroker, 
                         doAuth=True, 
                         closeOnClientQuit=False, 
                         authenticator=Authenticator(), 
                         sslServer=context)
obs = WebsocketObserver("WSO", messageBroker, wsi)

#start the main loop with Interfaces
main_loop([wsi.serve('127.0.0.1', 5000)])



