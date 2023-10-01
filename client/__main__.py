import os
import socket
import threading
from datetime import datetime
import time


HEADER = 64
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


class Message:
    content = None
    username = None
    time = None


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.messages = []
        self.username = "User"

        self._client = socket.socket()
        self._connected = False

    def run(self):
        self.username = input("Username: ")

        while not self._connected:
            try:
                self._client.connect((self.host, self.port))
                self._client.send(self.username.encode())
            except ConnectionRefusedError:
                print("Server is not available. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                self._connected = True

        thread = threading.Thread(target=self._receive_message)
        thread.start()

        try:
            self.refresh()

            while True:
                message = input().strip().replace(";;", "")

                if not message:
                    continue
                if message == "!quit":
                    self._client.send("C;;quit".encode())
                    break

                try:
                    self._client.send(f"M;;{message}".encode())
                except BrokenPipeError:
                    print("Gone offline")
                    break
        except KeyboardInterrupt:
            print("Client shutting down...")
        finally:
            thread.join()
            self._client.close()

    def _receive_message(self):
        system_message = Message()
        system_message.content = "Connected to server! Type !quit to exit."
        system_message.username = "System"
        system_message.time = datetime.now().strftime("%H:%M:%S")
        self.messages.append(system_message)

        while True:
            content = self._client.recv(HEADER).decode()
            content = content.strip().split(";;")

            if len(content) != 3:
                print(content)
                continue

            message = Message()
            message.content = content[1]
            message.username = content[0]
            message.time = datetime.now().strftime("%H:%M:%S")

            self.messages.append(message)
            self.refresh()

    def refresh(self):
        os.system("clear")
        for message in self.messages:
            print(f"{message.username} ({message.time}): {message.content}")
        print(end="")


if __name__ == "__main__":
    client = Client(HOST, PORT)
    client.run()
