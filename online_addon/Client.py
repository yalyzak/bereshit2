import socket
from collections import deque

class Client:
    def __init__(self, host, port, data_objects=None):
        # core socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.setblocking(False)

        # objects this client syncs
        self.data_objects = data_objects or []

        # message buffers
        self.incoming = deque()
        self.outgoing = deque()

    def send_data(self, msg: str):
        """Queue a raw message to send."""
        self.outgoing.append(msg)

    def Update(self, dt=None):
        msgs = self.get_messages()
        print(msgs)
        """Called automatically each physics tick."""

        # --- prepare data from objects ---
        for obj in self.data_objects:
            # Example: send object name + position
            msg = f"{obj.name}:{obj.position.x},{obj.position.y},{obj.position.z}"
            self.outgoing.append(msg)

        # --- send outgoing ---
        try:
            while self.outgoing:
                msg = self.outgoing.popleft()
                self.sock.send(msg.encode())
        except BlockingIOError:
            # socket buffer full, keep message
            self.outgoing.appendleft(msg)

        # --- receive incoming ---
        try:
            data = self.sock.recv(1024)
            if data:
                self.incoming.append(data.decode())
        except BlockingIOError:
            pass  # nothing to read

    def get_messages(self):
        """Retrieve and clear all received messages this frame."""
        msgs = list(self.incoming)
        self.incoming.clear()
        return msgs