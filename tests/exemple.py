
from bereshit import Object, Vector3, Core, BoxCollider, GameObject
from bereshit.addons.essentials import FPS_cam, CamController
from bereshit.bereshitCore import Component, Vector3, Rigidbody, BoxCollider

class Camera(Component):
    def __init__(self, width=1920, hight=1080, FOV=120, VIEWER_DISTANCE=0, shading="wire"):
        super().__init__()
        self.width = width
        self.hight = hight
        self.FOV = FOV
        self.VIEWER_DISTANCE = VIEWER_DISTANCE
        self.shading = shading  # wire, solid, material preview
        self.render = None
        self.name = "Camera"

cam = GameObject(Vector3(0, 0, -8), Vector3(), Vector3()).add_component(Camera())
cam.add_component(FPS_cam())
cam.add_component(CamController())
rb = Rigidbody()

floor = GameObject(Vector3(0,-1,0), Vector3(), Vector3(100,1,100))
floor.add_component(Rigidbody())
floor.Rigidbody.isKinematic = True
floor.Rigidbody.Freeze_Rotation = Vector3(1,1,1)
floor.add_component(BoxCollider())

obj2 = GameObject(Vector3(0,2,0), Vector3(0,0,10), Vector3(1,1,1)).add_component(BoxCollider())
obj2.add_component(Rigidbody())


# Core.run([cam, floor, obj2], speed=1, Render=True, physics_epochs=20)
time = 60 * 60 * 24
Core.run_max_speed([floor, obj2], MaxTime=time, Render=False)
