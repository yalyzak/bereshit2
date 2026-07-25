from bereshit import GameObject, Vector3, Core, Camera, BoxCollider, Rigidbody, Component
from bereshit.addons.essentials import FPS_cam, CamController

cam = GameObject(position=Vector3(0, 5, 0), rotation=Vector3(90,0,0)).add_component(Camera(), CamController(), FPS_cam())

obj = GameObject().add_component(Rigidbody(), BoxCollider())
obj2 = GameObject(children=[obj])

Core.run(scene=[obj2, cam])