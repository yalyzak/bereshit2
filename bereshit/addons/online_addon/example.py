from bereshit import Object, Camera, Vector3, Rigidbody, BoxCollider, MeshRander, Material, Core
from bereshit.addons.online_addon import Client
from bereshit.addons.essentials.FPS_cam import rotate
from bereshit.addons.essentials.CamController import CamController
from bereshit.addons.essentials.debug import debug
from bereshit.addons.essentials.Shoot import Shoot

import copy
# base object template
base_obj = Object(
    position=(0, 100, 0),
    size=(5, 1, 5),
    rotation=(0,0, 0),
    name="obj"
)
r=1
base_obj.add_component(Rigidbody(useGravity=True, velocity=Vector3(0, 0, 0), restitution=r))
base_obj.add_component(BoxCollider())
base_obj.add_component(Material(color="blue"))

# stack of 10 objects
stack = []
for i in range(1):
    obj_copy = copy.deepcopy(base_obj)
    obj_copy.position = Vector3(0, 0, 0)  # space slightly so no initial overlap
    obj_copy.name = f"obj_{i}"
    stack.append(obj_copy)

# floor
floor = Object(position=(0,-10,0), size=(50,5,50), rotation=(0,0,0), name="floor")
floor.add_component(Rigidbody(isKinematic=True, restitution=r,mass=9999))
floor.add_component(BoxCollider())

# camera
camera = Object(size=(1,1,1), position=(5,0,-5), name='camera')
camera.add_component(Camera(shading="wire"))
camera.add_component(MeshRander(shape="empty"))
camera.add_component(CamController())
camera.add_component(Rigidbody(useGravity=False))
camera.add_component(BoxCollider())
camera.add_component(rotate())
camera.add_component(Shoot())
stack[0].add_component(debug(floor))
camera.add_component(Client("192.168.1.17", 5000, data_objects=[camera]))

# scene with stacked objects
scene = Object(
    position=Vector3(0,0,0),
    size=(0,0,0),
    children=[floor, camera],
    name="scene"
)

Core.run(scene, gizmos=False, speed=1, tick=1/60, scriptRefreshRate=1)