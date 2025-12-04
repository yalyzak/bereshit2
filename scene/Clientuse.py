import socket
import struct
from collections import deque
from bereshit import World, Object, Rigidbody, BoxCollider, Vector3, Quaternion, MeshRander


FORMAT = "fff ffff fff"      # pos(3), quat(4), vel(3)
SIZE = struct.calcsize(FORMAT)

players = {}  # { "username": Object() }

class Clientuse:
    def __init__(self, data_objects=[]):
        self.data_objects = data_objects
        self.UserName = None

        self.incoming = deque()  # stores raw bytes
        self.outgoing = deque()  # stores raw bytes
    def Start(self):
        self.Broadcast = self.parent.Client.Broadcast
        self.ReceiveMassages = self.parent.Client.ReceiveMassages

        self.player = Object()
        self.player.add_component(BoxCollider())
        self.player.add_component(Rigidbody(useGravity=True))
        ServerContiner = Object()
        ServerContiner.add_component(MeshRander(shape="empty"))
        self.parent.add_child(ServerContiner)
        self.Continer = ServerContiner

    def Send(self):
        for obj in self.data_objects:
            msg = struct.pack(
                "fff fff ffff",
                obj.position.x, obj.position.y, obj.position.z,
                obj.quaternion.x, obj.quaternion.y, obj.quaternion.z, obj.quaternion.w,

                obj.Rigidbody.velocity.x, obj.Rigidbody.velocity.y, obj.Rigidbody.velocity.z,

            )
            self.Broadcast(self.UserName,msg)

    def Update(self, dt):
        if self.UserName is not None:
            self.Send()

        msg = self.ReceiveMassages()
        if not msg:
            return

        username = msg["from"]
        data = msg["message"]

        # --- Ensure correct data size ---
        if len(data) != 10:
            print("Bad message size from", username, len(data))
            return

            # Extract values
        px, py, pz = data[0:3]
        qx, qy, qz, qw = data[3:7]
        vx, vy, vz = data[7:10]

        # --- Create new player if not in dictionary ---
        if username not in players:
            new_player = Object()
            new_player.add_component(BoxCollider())
            new_player.add_component(Rigidbody(useGravity=False))  # server controls vel

            # Optional: add a renderer so you can see the player
            new_player.add_component(MeshRander(shape="box"))

            # Add to world
            self.Continer.add_child(new_player)

            players[username] = new_player
            print("Created new player:", username)

        # --- Update the player ---
        player = players[username]

        player.position.x = px
        player.position.y = py
        player.position.z = pz

        player.quaternion = Quaternion(qx, qy, qz, qw)

        rb = player.get_component(Rigidbody)
        rb.velocity = Vector3(vx, vy, vz)


