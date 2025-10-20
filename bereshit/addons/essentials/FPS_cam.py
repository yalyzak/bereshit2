import math

import mouse

import bereshit
from bereshit import Quaternion,Vector3,MeshRander

CENTER_X = 960
CENTER_Y = 540
sensitivity = 0.1  # adjust to your liking
class FPS_cam:
    def __init__(self):
        self.total_pitch = 0.0
        self.total_yaw = 0.0

    def s(self,dt):
        x, y = mouse.get_position()

        dx = x - CENTER_X
        dy = y - CENTER_Y

        sensitivity = 0.001
        self.total_yaw -= dx * sensitivity
        self.total_pitch += dy * sensitivity
        max_yaw = math.radians(90)
        min_yaw = math.radians(-90)

        max_pitch = math.radians(135)
        min_pitch = math.radians(0)
        # self.total_yaw = max(min_yaw, min(max_yaw, self.total_yaw))
        # self.total_pitch = max(min_pitch, min(max_pitch, self.total_pitch))

        # Apply pitch and yaw in fixed world space
        pitch_q = Quaternion.axis_angle(Vector3(1, 0, 0), self.total_pitch)
        yaw_q = Quaternion.axis_angle(Vector3(0, 1, 0), self.total_yaw)

        # self.parent.quaternion = pitch_q * yaw_q   # Rotate identity, not previous rotation
        self.parent.quaternion = yaw_q * pitch_q
        # self.parent.quaternion *= Quaternion.euler(Vector3(0.001,0,0))
        mouse.move(CENTER_X, CENTER_Y)

    def Update(self,dt):
        # self.parent.quaternion *= Quaternion.euler(Vector3(0.001,0,0))
        # Get current rotation
        self.s(dt)

        # Save
        # self.parent.quaternion = self.parent.quaternion.normalized()

        # self.parent.mesh = Mesh_rander(obj_path="models/Cup.obj")

        # self.parent.mesh = Mesh_rander(shape="box")

        # print(self.parent.rotation)

    def Start(self):
        mouse.move(CENTER_X, CENTER_Y)
        self.total_pitch = self.parent.rotation.x
        self.total_yaw= self.parent.rotation.y