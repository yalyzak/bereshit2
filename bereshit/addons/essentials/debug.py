import time

import numpy as np

import bereshit
from bereshit import Quaternion,Vector3, MeshRander
import  mouse

CENTER_X = 960
CENTER_Y = 540
class debug:
    def __init__(self,other):
        self.total_pitch = 0.0
        self.total_yaw = 0.0
        self.state = 0
        self.start_time = 0
        self.max = 0
        self.dt = 0
        self.other = other
    def change(self):
        current_time = time.perf_counter()

        if self.state == 0:
            self.parent.add_component(MeshRander(shape="empty"))

            self.start_time = current_time
            self.state = 1

        # elif self.state == 1:
        #     if current_time - self.start_time >= 5.0:
        #         self.parent.add_component(Mesh_rander(shape="box"))
        #
        #         self.state = 0  # Done
    # def s(self):
    #     relative = self.parent.position - pivot
    #
    #     # 2. Rotate that vector
    #     rotation = Quaternion.euler(Vector3(0, 0, 0.01))  # Rotate around Z axis
    #     rotated_relative = rotate_vector_quaternion(relative, rotation)
    #
    #     # 3. Set new position to maintain orbit
    #     self.parent.position = pivot + rotated_relative
    #
    #     # 4. Optionally rotate the object itself (e.g., to face same direction)
    #     self.parent.quaternion = rotation * self.parent.quaternion  # Global rotation
    def des(self):
        # self.parent = bereshit.Object()
        self.parent.world.add_child(bereshit.Object(size=(10,10,10),name="äsd"))
        # self.parent.world.children.append(bereshit.Object(size=(10,10,10)))
        print(self.parent.world.children)


    def Update(self,dt):
        # e_total = total_energy(self.parent)# + total_energy(self.other)
        # print(e_total)
        # print((self.parent.position-self.other.position).normalized().to_np())
        print(self.parent.position)

        # if self.other.position.y <= 0 or self.parent.position.y <= 0:
        #     exit()
    # def Start(self):
    #     self.parent.Rigidbody.AddForce(Vector3(100,0,0),self.parent.position - Vector3(0,10,0))
    #     self.parent.Rigidbody.AddForce(Vector3(100,0,0),self.parent.position - Vector3(0,-10,0))

    #     self.max = self.parent.position.y
    #     # self.parent.Rigidbody.angular_velocity += Vector3(3,1,10)
    #     self.des()
    #
    # #     self.parent.quaternion *= Quaternion.euler(Vector3(0,0,30))
    #     # print(self.parent.rotation)
    #     self.parent.Rigidbody.velocity += Vector3(0,0,2)

# def total_energy(obj):
#     rb = obj.Rigidbody
#     m = rb.mass
#     v = rb.velocity.magnitude()
#     h = abs(obj.position.y)
#
#     # Linear kinetic energy + potential energy
#     e = 0.5 * m * v ** 2 + m * 9.8 * h
#
#     # Angular kinetic energy: 0.5 * ω^T I ω
#     if rb.angular_velocity.magnitude() > 0:
#         # Make sure I_world is the inertia tensor in world space
#         I_world = rb.parent.quaternion.to_matrix3() @ rb.inertia.to_np() @ rb.parent.quaternion.conjugate().to_matrix3()
#         # w = rb.angular_velocity.to_np()
#
#         e += 0.5 * (w.T @ (I_world @ w))

    # return e/