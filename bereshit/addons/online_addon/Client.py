import socket
import struct
from collections import deque
from bereshit import World, Object, Rigidbody, BoxCollider, Vector3, MeshRander

class Client:
    def __init__(self, host, port, data_objects=None):
        # --- core UDP socket setup ---
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.server_addr = (host, port)

        # objects this client syncs
        self.data_objects = data_objects or []

        # message buffers
        self.incoming = deque()   # stores raw bytes
        self.outgoing = deque()   # stores raw bytes

        self.Continer = None

    def Start(self):
        cube = Object()
        cube.add_component(BoxCollider())
        cube.add_component(Rigidbody(useGravity=True))
        ServerContiner = Object(children=[cube])
        ServerContiner.add_component(MeshRander(shape="empty"))
        self.parent.world.add_child(ServerContiner)
        self.Continer = ServerContiner

    def send_data(self, msg: bytes):
        """Queue a raw binary message to send."""
        self.outgoing.append(msg)

    def Update(self, dt=None):
        # --- parse any received messages ---
        msgs = self.get_messages()
        for m in msgs:
            # Update container position
            self.Continer.children[0].position = Vector3(*m["position"])
            self.Continer.children[0].quaternion = Vector3(*m["quaternion"])

            self.Continer.children[0].Rigidbody.velocity = Vector3(*m["velocity"])


        # --- prepare and queue outgoing data ---
        for obj in self.data_objects:
            name_bytes = obj.name.encode()
            msg = struct.pack(
                f"!I{len(name_bytes)}s fff ffff fff",
                len(name_bytes), name_bytes,
                obj.position.x, obj.position.y, obj.position.z,
                obj.quaternion.x, obj.quaternion.y, obj.quaternion.z, obj.quaternion.w,

                obj.Rigidbody.velocity.x, obj.Rigidbody.velocity.y, obj.Rigidbody.velocity.z,

            )
            self.outgoing.append(msg)

        # --- send outgoing ---
        try:
            while self.outgoing:
                msg = self.outgoing.popleft()
                self.sock.sendto(msg, self.server_addr)
        except BlockingIOError:
            # socket buffer full, keep message
            self.outgoing.appendleft(msg)

        # --- receive incoming ---
        try:
            data, _ = self.sock.recvfrom(1024)
            if data:
                # store raw binary
                self.incoming.append(data)
        except BlockingIOError:
            pass  # nothing to read

    def get_messages(self):
        """Retrieve and decode all received messages this frame."""
        decoded = []
        while self.incoming:
            m = self.incoming.popleft()

            # first 4 bytes = name length
            name_len = struct.unpack("!I", m[:4])[0]

            # rebuild format string
            fmt = f"!I{name_len}s fff ffff fff"
            unpacked = struct.unpack(fmt, m)

            _, name, x, y, z, xq, yq, zq, wq, vx, vy, vz = unpacked
            decoded.append({
                "name": name.decode(),
                "position": (x, y, z),
                "quaternion": (xq, yq, zq, wq),
                "velocity": (vx, vy, vz),

            })
        return decoded