from bereshit import Core, Camera, GameObject
from bereshit.addons.essentials import FPS_cam, CamController
from bereshit.bereshitCore import Vector3, BoxCollider, Rigidbody

cam = GameObject(position=Vector3(0, 0, -8)).add_component(Camera(), CamController(), FPS_cam())

floor = GameObject(size=Vector3(10,1,10), position=Vector3(0,-1,0)).add_component(BoxCollider(), Rigidbody(isKinematic=True))

# obj = Object(position=Vector3(0,0,0)).add_component(BoxCollider(), Rigidbody())
#
obj2 = GameObject(position=Vector3(0,2,0)).add_component(BoxCollider(), Rigidbody())

Core.run([cam, floor, obj2])


