import socket
import threading
import json

class Client:
    def __init__(self, host="127.0.0.1", tcp_port=5000, udp_port=5001):
        self.server_host = host
        self.tcp_port = tcp_port
        self.server_udp_port = udp_port

        # --- Create UDP socket for receiving ---
        self.udp_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_listener.bind(("0.0.0.0", 0))  # random free port
        self.my_udp_port = self.udp_listener.getsockname()[1]

        threading.Thread(target=self._listen_udp, daemon=True).start()

    # ---------------- TCP -----------------

    def _send_tcp(self, obj):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.server_host, self.tcp_port))
            s.send(json.dumps(obj).encode())
            return json.loads(s.recv(4096).decode())

    def CreateRoom(self):
        reply = self._send_tcp({"action": "create_room"})
        return reply["room"]

    def FindRoom(self, RoomName):
        reply = self._send_tcp({"action": "find_room", "room": RoomName})
        return reply["exists"]

    def Connect(self, RoomName, UserName):
        reply = self._send_tcp({
            "action": "join_room",
            "room": RoomName,
            "username": UserName,
            "udp_port": self.my_udp_port
        })
        return reply["status"] == "ok"

    # ---------------- UDP -----------------

    def _listen_udp(self):
        while True:
            data, addr = self.udp_listener.recvfrom(4096)
            msg = json.loads(data.decode())
            print(f"[{msg['room']}] {msg['from']}: {msg['message']}")

    def Broadcast(self, RoomName, UserName, message):
        """Send message to server's UDP broadcast system."""
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.sendto(json.dumps({
            "action": "broadcast",
            "room": RoomName,
            "username": UserName,
            "message": message
        }).encode(), (self.server_host, self.server_udp_port))


# ---------------- Example usage ----------------
if __name__ == "__main__":
    c = Client()

    print("Creating room...")
    room = c.CreateRoom()
    # room = c.Connect(RoomName="WL5Q1K",UserName="asd")
    print("Created:", room)

    c.Connect(room, "Yaly")
    print("Connected!")

    while True:
        msg = "asd"
        c.Broadcast(room, "Yaly", msg)

