import websockets
import asyncio as aio

from nucosCR import hexdigest_n

from nucosObs import main_loop, loop, debug
from nucosObs.observer import Observer, inThread, broadcast
from nucosObs.observable import Observable
from nucosObs.websocketInterface import WebsocketInterface

debug.append(True)

messageBroker = Observable()
user = Observable()


class AuthObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(AuthObserver, self).__init__(name, observable, concurrent)
        # next line is for testing purpose and means test-user with pwd: test123
        # for real worl application use another source for user-credentials
        self.users = {'test-user': '40bcc00ae2166c62a53f8bf86a8bcc62dffe2cec552b66d846da02ebea309b18'}
        self.approved = False

    async def startAuth(self, *args):
        try:
            nonce, user, challenge = args
        except:
            await self.shutdown()
        print("start auth") 
        if self.authenticate(nonce, user, challenge):
            self.approved = True
            await wsi.ws.send("endAuth approved")
            print("Authenticated")
        else:
            await self.shutdown()

    def authenticate(self, nonce, user, challenge):
        digest = hexdigest_n(self.users[user] + nonce, 100)
        return digest == challenge 


    async def shutdown(self):
        print("Auth failed")
        await wsi.ws.send("Auth failed")
        await wsi.ws.close()



class SendObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(SendObserver, self).__init__(name, observable, concurrent)

    async def send(self, *msg):
        await wsi.ws.send(' '.join(msg))
        print("message send: %s"%' '.join(msg))

class ReceiveObserver(Observer):
    def __init__(self, name, observable, concurrent=[]):
        super(ReceiveObserver, self).__init__(name, observable, concurrent)

    async def print(self, *msg):
        print("message received: "," ".join(msg))

    def parse(self, item):
        method = self.print
        args = item.split(" ")
        return True, method, args
    

so = SendObserver("SO", messageBroker)
ro = ReceiveObserver("RO", messageBroker)
ao = AuthObserver("AO", messageBroker)

wsi = WebsocketInterface(messageBroker, ao)

#start the main loop with Interfaces
main_loop([wsi.serve('192.168.178.42',8765)])



