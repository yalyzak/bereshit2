from bereshit import Object, Camera, Vector3, Rigidbody, BoxCollider, MeshRander, Material, Core
from bereshit.addons.essentials import CamController, PlayerController, FPS_cam
from bereshit.addons.essentials.Shoot import Shoot
from bereshit.addons.online_addon import Client

obj = Object(size=Vector3(1,1,1),rotation=Vector3(10,0,0)).add_component([BoxCollider(),Rigidbody(useGravity=False)])

floor = Object(position=Vector3(0,-10,0),size=(10,1,10)).add_component([BoxCollider(),Rigidbody(isKinematic=True)])

camera = Object().add_component([Camera(),Shoot(obj),CamController(),FPS_cam(),Rigidbody()])
camera.add_component(Client("172.31.16.1", 5000, data_objects=[camera]))
# camera.add_component(Server(data_objects=[camera]))

scene = [floor]

Core.run(scene+[camera],Render=False)