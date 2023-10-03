import socket
import threading
import json
from datetime import datetime
import time
import tkinter as tk


HEADER_SIZE = 512
PORT = 8080
HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"
VERSION = "0.0.2"
STYLING = {
    "bg": "#17202A",
    "fg": "#EAECEE",
    "font": "Helvetica 13 bold",
    "padding": 5,
}


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.messages = []
        self.username = "User"

        self._client = socket.socket()

        # Create Window
        self.window = tk.Tk()
        self.window.withdraw()

        # Login root
        self._login = tk.Toplevel()
        self._login.title("Login")
        self._login.resizable(width=False, height=False)
        self._login.configure(width=400, height=300)

        # Label for login
        self._title_text = tk.Label(
            self._login,
            text="Please login to continue",
            justify=tk.CENTER,
            font=STYLING["font"],
        )
        self._title_text.place(relheight=0.15, relx=0.2, rely=0.07)

        # Label and entry for username
        self._login_label = tk.Label(self._login, text="Name: ", font=STYLING["font"])
        self._login_label.place(relheight=0.2, relx=0.1, rely=0.2)
        self._login_entry = tk.Entry(self._login, font=STYLING["font"])
        self._login_entry.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.2)
        self._login_entry.focus()

        # Button to continue
        login_continue = tk.Button(
            self._login,
            text="CONTINUE",
            font=STYLING["font"],
            command=lambda: self._main_loop(self._login_entry.get()),
        )
        login_continue.place(relx=0.4, rely=0.55)

        self.window.mainloop()

    def _main_loop(self, name):
        self.username = name.strip()

        online = False
        while not online:
            try:
                self._client.connect((self.host, self.port))
                self._client.recv(HEADER_SIZE).decode()
            except ConnectionRefusedError:
                print("Server is not available. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                online = True

        self._client.send(
            json.dumps(
                {
                    "username": self.username,
                    "version": VERSION,
                }
            ).encode()
        )
        self._login.destroy()
        self._layout()

        thread = threading.Thread(target=self._receive_message)
        thread.start()

    def _receive_message(self):
        system_message = {
            "content": "Connected to server!",
            "time": datetime.now().strftime("%H:%M:%S"),
            "username": "System",
            "version": VERSION,
        }
        self.messages.append(system_message)
        self._append_message(system_message)

        while True:
            content = self._client.recv(HEADER_SIZE).decode()
            content = json.loads(content.strip())
            self.messages.append(
                {
                    "content": content["content"],
                    "time": content["time"],
                    "username": content["username"],
                    "version": content["version"],
                }
            )
            self._append_message(content)

    def _append_message(self, message):
        message = f"{message['username']} [{message['time']}]: {message['content']} (version {message['version']})"
        self.textCons.config(state=tk.NORMAL)
        self.textCons.insert(tk.END, message + "\n\n")
        self.textCons.config(state=tk.DISABLED)
        self.textCons.see(tk.END)

    def _layout(self):
        self.window.deiconify()
        self.window.title("PyChat v" + VERSION + " - Logged in as: " + self.username)
        self.window.resizable(width=False, height=False)
        self.window.configure(width=470, height=550, bg="#17202A")

        self.label_heading = tk.Label(
            self.window,
            bg="#17202A",
            fg="#EAECEE",
            text="PyChat v" + VERSION,
            font=STYLING["font"],
            pady=5,
        )
        self.label_heading.place(relwidth=1)

        self.line = tk.Label(self.window, width=450, bg="#ABB2B9")
        self.line.place(relwidth=1, rely=0.07, relheight=0.012)

        self.textCons = tk.Text(
            self.window,
            width=20,
            height=2,
            bg="#17202A",
            fg="#EAECEE",
            font=STYLING["font"],
            padx=5,
            pady=5,
        )
        self.textCons.place(relheight=0.745, relwidth=1, rely=0.08)

        self.labelBottom = tk.Label(self.window, bg="#ABB2B9", height=80)
        self.labelBottom.place(relwidth=1, rely=0.825)

        self.entryMsg = tk.Entry(
            self.labelBottom,
            bg="#2C3E50",
            fg="#EAECEE",
            font=STYLING["font"],
        )
        self.entryMsg.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        self.entryMsg.focus()

        self.buttonMsg = tk.Button(
            self.labelBottom,
            text="Send",
            font=STYLING["font"],
            width=20,
            bg="#ABB2B9",
            command=lambda: self._send_button(self.entryMsg.get()),
        )
        self.buttonMsg.place(relx=0.77, rely=0.008, relheight=0.06, relwidth=0.22)

        self.textCons.config(cursor="arrow")

        scrollbar = tk.Scrollbar(self.textCons)
        scrollbar.place(relheight=1, relx=0.974)
        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=tk.DISABLED)

    def _send_button(self, msg):
        self.textCons.config(state=tk.DISABLED)
        self.msg = msg
        self.entryMsg.delete(0, tk.END)
        snd = threading.Thread(target=self._send_message)
        snd.start()

    # function to send messages
    def _send_message(self):
        self.textCons.config(state=tk.DISABLED)

        while True:
            message = self.msg.strip()
            print(message)

            if not message:
                continue

            message = {
                "content": message,
                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "username": self.username,
                "version": VERSION,
            }
            message = json.dumps(message).encode()

            try:
                self._client.send(message)
            except BrokenPipeError:
                print("Gone offline")

            break


if __name__ == "__main__":
    client = Client(HOST, PORT)
