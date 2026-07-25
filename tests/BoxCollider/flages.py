from bereshit import GameObject, Vector3, Core, Camera, BoxCollider, Rigidbody, Component
from bereshit.addons.essentials import FPS_cam, CamController
class debug(Component):
    def OnCollisionEnter(self, Collision):
        print("entered", Collision.other.parent.name)

    def OnCollisionStay(self, Collision):
        print("stay", Collision.other.parent.name)

    def OnCollisionExit(self, Collision):
        print("exited", Collision.other.parent.name)



cam = GameObject(position=Vector3(0, 0, -8)).add_component(Camera(), CamController(), FPS_cam())

floor = GameObject(size=Vector3(10, 1, 10), position=Vector3(0, -1, 0), name="floor").add_component(BoxCollider(),
                                                                                  Rigidbody(isKinematic=True))

obj = GameObject(position=Vector3(0, 2, 0), name="obj").add_component(BoxCollider(), Rigidbody(), debug())

obj2 = GameObject(position=Vector3(0, 2, 1), name="obj2").add_component(BoxCollider(), Rigidbody())

Core.run([cam, floor, obj, obj2])
