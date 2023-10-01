import socket
import threading
from datetime import datetime


HEADER = 64
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


class SocketChat:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind((self.host, self.port))

        self._clients = {}

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
        broadcast_message = self._format_message(message, username)
        if not broadcast_message:
            return

        for client in self._clients.copy():
            try:
                client.send(broadcast_message)
            except BrokenPipeError:
                self._remove_client(client)

    def _direct(self, message, client):
        client = self._clients[client]

        message = self._format_message(message, client["username"])
        if not message:
            return

        try:
            client.send(message)
        except BrokenPipeError:
            self._remove_client(client)

    @staticmethod
    def _format_message(message, username="Server"):
        time = datetime.now().strftime("%H:%M:%S")

        message.replace(";;", "")
        message = message.strip()
        if not message:
            return None

        broadcast_message = f"{username};;{message};;{time}".encode()
        return broadcast_message

    def _client(self, client, address):
        username = client.recv(HEADER).decode()
        self._clients[client] = {
            "username": username,
            "address": address,
        }

        while True:
            message = client.recv(HEADER).decode()
            try:
                key, message, time = message.strip().split(";;")
            except ValueError:
                self._direct("Malformed Information", client)
                continue

            if key not in ("C", "M"):
                self._direct("Malformed Information", client)
                continue

            if key == "C":
                if message == "quit":
                    self._remove_client(client)
                else:
                    client.send("Unknown command!".encode())
            if key == "M":
                self._broadcast(message, username)

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
