import copy

from bereshit import GameObject, Vector3, Core, Camera, BoxCollider, Rigidbody, FixedJoint, HingeJoint
from bereshit.addons.essentials import FPS_cam, CamController
from bereshit.addons.PPO.examples.WalkToGoal.Servo import Servo

cam = GameObject(position=Vector3(0, 0, -8)).add_component(Camera(shading="material preview"))

floor = GameObject(size=Vector3(100, 1, 100), position=Vector3(0, -3, 0)).add_component(BoxCollider(),
                                                                                    Rigidbody(isKinematic=True))


feet = GameObject(size=Vector3(1, 1, 1), position=Vector3(0,0,0), name="feet").add_component(BoxCollider(), Rigidbody(angular_velocity=Vector3(0,10,0), useGravity=False))

mount = GameObject(position=Vector3(2,0,0), size=Vector3(1, 1, 1), name="mount").add_component(BoxCollider(), Rigidbody( useGravity=False), FixedJoint(feet, beta=1))


Core.run([cam, mount, feet, floor], Render=True, tick=1/120)
