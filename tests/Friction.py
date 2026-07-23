from bereshit import Core, Camera, GameObject
from bereshit.addons.essentials import FPS_cam, CamController
from bereshit.bereshitCore import  Vector3, BoxCollider, Rigidbody

cam = GameObject(position=Vector3(0,-4,-3)).add_component(Camera(shading="material preview"), CamController(), FPS_cam())

obj1 = GameObject(position=Vector3(2,-4,0)).add_component(BoxCollider(), Rigidbody(velocity=Vector3(10,0,0), Freeze_Rotation=Vector3(1,1,1)))

obj2 = GameObject(position=Vector3(0,-4,0)).add_component(BoxCollider(), Rigidbody(angular_velocity=Vector3(0,10,0)))

obj3 = GameObject(position=Vector3(3,2,0)).add_component(BoxCollider(), Rigidbody(velocity=Vector3(1,0,0), angular_velocity=Vector3(0,1,0), restitution=0.1))

floor = GameObject(size=Vector3(100,1,100), position=Vector3(0,-5,0)).add_component(BoxCollider(), Rigidbody(isKinematic=True))

Core.run([cam,floor, obj1, obj2, obj3], tick=1/60, speed=100, Render=True)
