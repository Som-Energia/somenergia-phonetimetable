from websocket_server import WebsocketServer
from consolemsg import error, step, warn
from threading import Semaphore, Thread
from yamlns import namespace as ns


CONFIG = ns.load('config.yaml')

class WebSocketTomaticServer(object):

    def __init__(self):
        self.websockets = {}
        self.wserver = None
        self.wsthread = None

    def initialize_client(self, client, server, extension):
        self.client_left(client, server)
        step("Identifying client as {}", extension)
        if extension not in self.websockets:
            self.websockets[extension] = []
        self.websockets[extension].append(client)


    def say_new_user_logged(self, client, server, extension, iden):
        step("Saying to the page that now {} is there", iden)
        clients = self.websockets.get(extension, [])
        if not clients:
            error("Trying to send message to {} but has no client.", extension)
        for client in clients:
            self.wserver.send_message(client, "IDEN:" + iden)


    def say_logcalls_has_changed(self, extension):
        clients = self.websockets.get(extension, [])
        if not clients:
            error("Trying to send message to {} but has no client.", extension)
        for client in clients:
            self.wserver.send_message(client, "REFRESH:" + extension)


    def on_message_recieved(self, client, server, message):
        divided_message = message.split(":")
        type_of_message = divided_message[0]
        if type_of_message == "IDEN":
            extension = divided_message[1]
            iden = divided_message[2]
            self.initialize_client(client, server, extension)
            self.say_new_user_logged(client, server, extension, iden)
        else:
            error("Type of message not recognized.")


    def client_left(self, client, server):
        for extension in self.websockets:
            if client in self.websockets[extension]:
                step("Unidentifying client as {}", extension)
                self.websockets[extension].remove(client)
                break
        else:
            warn("New client")


    def startCallInfoWS(self, host):
        self.wserver = WebsocketServer(
            host=host,
            port=CONFIG.websocket_port,
        )
        self.wserver.set_fn_message_received(self.on_message_recieved)
        self.wserver.set_fn_client_left(self.client_left)

        self.wsthread = Thread(target=self.wserver.run_forever)
        self.wsthread.start()

    def stopCallInfoWS(self):
        self.wserver.shutdown()
        self.wserver.server_close()
        self.wsthread.join()
