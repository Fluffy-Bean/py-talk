import socket
import threading
import json
from datetime import datetime


HEADER = 512
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


class SocketChat:
    def __init__(self, host="localhost", port=8080):
        self.host, self.port = host, port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))

        self.clients = {}
        self.messages = []

    def run(self):
        self.server.listen()
        print("Server is listening on %s:%d" % (self.host, self.port))

        while True:
            client, address = self.server.accept()
            client.send("pong".encode())

            initial_data = client.recv(HEADER).decode()
            initial_data = json.loads(initial_data.strip())
            self.clients[client] = {
                "username": initial_data["username"],
                "address": address,
                "version": initial_data["version"],
            }

            self.broadcast("New user joined the chat!")

            thread = threading.Thread(target=self.handle, args=(client, address))
            thread.start()

            print("Active connections:", str(threading.active_count() - 1))

    def broadcast(self, message, username="Server"):
        message = {
            "content": message,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "version": "0.0.1",
        }
        message = json.dumps(message).encode()

        for client in self.clients.copy():
            try:
                client.send(message)
            except BrokenPipeError:
                self.remove_client(client)

    def direct(self, message, client):
        client = self.clients[client]

        message = {
            "content": message,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "username": client["username"],
            "version": "0.0.1",
        }
        message = json.dumps(message).encode()

        try:
            client.send(message)
        except BrokenPipeError:
            self.remove_client(client)

    def handle(self, client, address):
        client_data = self.clients[client]
        connected = True

        while connected:
            message = client.recv(HEADER).decode()
            if not message:
                break
            message = json.loads(message.strip())
            if not message["content"]:
                client.send(
                    json.dumps(
                        {
                            "content": "Malformed message!",
                            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                            "username": "Server",
                            "version": "0.0.1",
                        }
                    ).encode()
                )
                continue

            self.messages.append(message)
            self.broadcast(message["content"], client_data["username"])

        self.remove_client(client)
        client.close()

    def remove_client(self, client):
        self.broadcast(str(self.clients[client]["username"]) + " left the chat!")
        self.clients.pop(client)
        client.close()


if __name__ == "__main__":
    server = SocketChat(HOST, PORT)
    server.run()
