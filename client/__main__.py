import os
import socket
import threading
import json
from datetime import datetime
import time


HEADER = 512
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.messages = []
        self.username = "User"

        self._client = socket.socket()
        self._online = False

    def run(self):
        self.username = input("Username: ").strip()

        join_data = {
            "username": self.username,
            "version": "0.0.1",
        }
        join_data = json.dumps(join_data).encode()

        while not self._online:
            try:
                self._client.connect((self.host, self.port))
                self._client.send(join_data)
            except ConnectionRefusedError:
                print("Server is not available. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                self._online = True

        thread = threading.Thread(target=self._receive_message)
        thread.start()

        try:
            self.refresh()

            while True:
                message = input().strip()
                if not message:
                    continue

                message = {
                    "content": message,
                    "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "username": self.username,
                    "version": "0.0.1",
                }
                message = json.dumps(message).encode()

                try:
                    self._client.send(message)
                except BrokenPipeError:
                    print("Gone offline")
                    break
        except KeyboardInterrupt:
            print("Client shutting down...")
        finally:
            thread.join()
            self._client.close()

    def _receive_message(self):
        system_message = {
            "content": "Connected to server!",
            "time": datetime.now().strftime("%H:%M:%S"),
            "username": "System",
            "version": "0.0.1",
        }
        self.messages.append(system_message)

        while True:
            content = self._client.recv(HEADER).decode()
            content = json.loads(content.strip())

            try:
                message = {
                    "content": content["content"],
                    "time": content["time"],
                    "username": content["username"],
                    "version": content["version"],
                }
            except KeyError:
                print("Invalid data received!")
                continue

            self.messages.append(message)
            self.refresh()

    def refresh(self):
        os.system("clear")
        for message in self.messages:
            print(f"{message['username']} ({message['time']}): {message['content']}")
        print(end="")


if __name__ == "__main__":
    client = Client(HOST, PORT)
    client.run()
