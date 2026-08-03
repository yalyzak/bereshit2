from bereshit import GameObject, Vector3, Camera, BoxCollider, Rigidbody, Core
from bereshit.addons.essentials import CamController, FPS_cam, Servo

cam = GameObject(position=Vector3(8, 0, 0), rotation=Vector3(0,-90,0)).add_component(Camera(shading="material preview"),CamController(), FPS_cam())

mount = GameObject(position=Vector3(0,0,0)).add_component(BoxCollider(), Rigidbody(isKinematic=True, mass=99))

servo = GameObject(position=Vector3(0,0,3)).add_component(BoxCollider(), Rigidbody(), Servo(mount, Vector3(1,0,0), torque=50, max_speed=9999))

Core.run([servo, mount, cam], Render=True, tick=1/120, physics_epochs=100)
