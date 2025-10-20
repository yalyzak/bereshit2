from bereshit import Object, Camera, Vector3, Rigidbody, BoxCollider, MeshRander, Material, Core
from bereshit.addons.essentials import CamController, PlayerController, FPS_cam
from bereshit.addons.essentials.Shoot import Shoot
from bereshit.addons.online_addon import Server

obj = Object(size=Vector3(1,1,1),rotation=Vector3(10,0,0)).add_component([BoxCollider(),Rigidbody(useGravity=False)])

floor = Object(position=Vector3(0,-10,0),size=(10,1,10)).add_component([BoxCollider(),Rigidbody(isKinematic=True)])

camera = Object().add_component([Camera(),CamController()])
camera.add_component(Server())

scene = [floor]

Core.run(scene+[camera],Render=False)