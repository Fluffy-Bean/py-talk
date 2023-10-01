import socket
import threading
import json
from datetime import datetime


HEADER = 512
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


"""
example message contents looks as follows:
{
    "content": "Hello World!",  This is the actual message content
    "time": "2021-01-01 00:00:00",  This is the time the message was sent in UTC
    "username": "user",  This is the username of the user who sent the message, only temporary
    "version": "0.0.1"  This is the version of the client that sent the message, can be used for compatibility in the future
}
"""


class SocketChat:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind((self.host, self.port))

        self._clients = {}
        self._messages = []

    def run(self):
        self._server.listen()
        print("Server is listening on %s:%d" % (self.host, self.port))

        while True:
            client, address = self._server.accept()

            thread = threading.Thread(target=self._client, args=(client, address))
            thread.start()

            print("Active connections:", str(threading.active_count() - 1))

            self._broadcast("New user joined the chat!")

        self._server.close()

    def _broadcast(self, message, username="Server"):
        message = {
            "content": message,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "version": "0.0.1",
        }
        message = json.dumps(message).encode()

        for client in self._clients.copy():
            try:
                client.send(message)
            except BrokenPipeError:
                self._remove_client(client)

    def _direct(self, message, client):
        client = self._clients[client]

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
            self._remove_client(client)

    def _client(self, client, address):
        initial_data = client.recv(HEADER).decode()

        print(initial_data)

        initial_data = json.loads(initial_data.strip())

        client_data = None
        try:
            client_data = {
                "username": initial_data["username"],
                "address": address,
                "version": initial_data["version"],
            }
            self._clients[client] = client_data
        except KeyError:
            client.send("Invalid data!".encode())
            client.close()
            return
        finally:
            print("New connection from %s:%d" % (address[0], address[1]))

        while True:
            message = client.recv(HEADER).decode()

            print(message)

            message = json.loads(message.strip())

            if not message or not message["content"]:
                continue

            self._messages.append(message)
            self._broadcast(message["content"], client_data["username"])

    def _remove_client(self, client):
        try:
            self._broadcast(str(self._clients[client]["username"]) + " left the chat!")
            self._clients.pop(client)
            client.close()
        except Exception as e:
            print(e)
            # There is a problem with the code here, but I don't know what it is so trying to sus it out


if __name__ == "__main__":
    server = SocketChat(HOST, PORT)
    server.run()
