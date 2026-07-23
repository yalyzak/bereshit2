
from bereshit import Core, GameObject, Camera
from bereshit.addons.essentials import FPS_cam, CamController
from bereshit.bereshitCore import Component, Vector3, Rigidbody, BoxCollider



class debug(Component):
    def Update(self, dt):
        print(self.parent.Rigidbody.velocity)

cam = GameObject(Vector3(0, 0, -8), Vector3(), Vector3()).add_component(Camera(shading="material preview"))
cam.add_component(FPS_cam())
cam.add_component(CamController())
rb = Rigidbody()

floor = GameObject(Vector3(0,-1,0), Vector3(), Vector3(100,1,100))
floor.add_component(Rigidbody())
floor.Rigidbody.isKinematic = True
floor.Rigidbody.Freeze_Rotation = Vector3(1,1,1)
floor.add_component(BoxCollider())

obj2 = GameObject(position=Vector3(0,2,0)).add_component(BoxCollider())
obj2.add_component(Rigidbody())
# obj2.add_component(debug())


Core.run([cam, floor, obj2], speed=1, Render=True, physics_epochs=0)
# time = 60 * 60 * 24
# Core.run_max_speed([floor, obj2], MaxTime=time, Render=False)
