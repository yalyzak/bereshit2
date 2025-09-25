import socket
import struct
from collections import deque
from bereshit import Object, Rigidbody, BoxCollider, Vector3, MeshRander

class Client:
    def __init__(self, host, port, data_objects=None):
        # --- core UDP socket setup ---
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = (host, port)

        # "connect" the UDP socket so recv() only accepts from server
        self.sock.connect(self.server_addr)

        # set non-blocking mode
        self.sock.setblocking(False)

        # objects this client syncs
        self.data_objects = data_objects or []

        # message buffers
        self.incoming = deque()
        self.outgoing = deque()

        self.Continer = None
        self.id = None  # assigned by server

    def Start(self):
        cube = Object()
        cube.add_component(BoxCollider())
        cube.add_component(Rigidbody(useGravity=True))
        ServerContiner = Object(children=[cube])
        ServerContiner.add_component(MeshRander(shape="empty"))
        self.parent.world.add_child(ServerContiner)
        self.Continer = ServerContiner

    def Update(self, dt=None):
        # --- receive incoming data ---
        try:
            while True:  # drain all available packets this frame
                data = self.sock.recv(1024)
                if not data:
                    break

                if self.id is None and len(data) == 4:
                    # First message = assigned ID
                    self.id = struct.unpack("!I", data)[0]
                    print(f"Assigned client ID {self.id}")
                else:
                    self.incoming.append(data)

        except BlockingIOError:
            pass  # nothing left to read
        except OSError as e:
            print("Socket error:", e)

        # --- parse messages ---
        for m in self.get_messages():
            child = self.Continer.children[0]
            child.position = Vector3(*m["position"])
            child.size = Vector3(*m["size"])
            child.Rigidbody.velocity = Vector3(*m["velocity"])
            child.Rigidbody.angular_velocity = Vector3(*m["angular_velocity"])
            # TODO: set quaternion properly in your engine

        # --- prepare and queue outgoing data ---
        if self.id is not None:
            for obj in self.data_objects:
                name_bytes = obj.name.encode()
                msg = struct.pack(
                    f"!I{len(name_bytes)}sI fff fff ffff fff fff",
                    len(name_bytes), name_bytes,
                    self.id,
                    obj.position.x, obj.position.y, obj.position.z,
                    obj.size.x, obj.size.y, obj.size.z,
                    obj.quaternion.x, obj.quaternion.y, obj.quaternion.z, obj.quaternion.w,
                    obj.Rigidbody.velocity.x, obj.Rigidbody.velocity.y, obj.Rigidbody.velocity.z,
                    obj.Rigidbody.angular_velocity.x, obj.Rigidbody.angular_velocity.y, obj.Rigidbody.angular_velocity.z,
                )
                self.outgoing.append(msg)

        # --- send outgoing ---
        try:
            while self.outgoing:
                msg = self.outgoing.popleft()
                self.sock.send(msg)
        except BlockingIOError:
            self.outgoing.appendleft(msg)
        except OSError as e:
            print("Send error:", e)

    def get_messages(self):
        decoded = []
        while self.incoming:
            m = self.incoming.popleft()
            try:
                name_len = struct.unpack("!I", m[:4])[0]
                fmt = f"!I{name_len}sI fff fff ffff fff fff"
                unpacked = struct.unpack(fmt, m)

                _, name, obj_id, px, py, pz, sx, sy, sz, qx, qy, qz, qw, vx, vy, vz, ax, ay, az = unpacked
                decoded.append({
                    "name": name.decode(),
                    "id": obj_id,
                    "position": (px, py, pz),
                    "size": (sx, sy, sz),
                    "quaternion": (qx, qy, qz, qw),
                    "velocity": (vx, vy, vz),
                    "angular_velocity": (ax, ay, az),
                })
            except struct.error:
                print("Warning: malformed packet ignored")
        return decoded
