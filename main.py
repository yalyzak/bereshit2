from bereshit import Object, Core, Camera, Vector3, BoxCollider, Rigidbody
from bereshit.addons.essentials import CamController, PlayerController, FPS_cam

from scene.ui import ui, ui2
from scene.Clientuse import Clientuse
from scene.Goal import Goal

from bereshit.addons.online_addon import Client
from bereshit.addons.essentials.Shoot import Shoot

obj = Object(position=Vector3(0,2,2)).add_component([Goal(),BoxCollider(),Rigidbody(useGravity=True)])

floor = Object(position=Vector3(0,0,0),size=(10,1,10),rotation=Vector3(0,0,0)).add_component([BoxCollider(),Rigidbody(isKinematic=True)])

# camera.add_component(Clientuse(camera))
scene = [floor,obj]
camera = Object(position=Vector3(0,5,0)).add_component([Camera(), ui(),ui2(), Client(host="192.168.1.45"),PlayerController(),BoxCollider(), FPS_cam(),Rigidbody(useGravity=True),Shoot(Goal)])

camera.add_component(Clientuse(data_objects=[camera]))

Core.run(scene+[camera],gizmos=False,tick=1/60)
