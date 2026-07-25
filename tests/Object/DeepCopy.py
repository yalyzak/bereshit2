import copy

from bereshit import GameObject, Vector3, Core, Camera, BoxCollider, Rigidbody, Component
from bereshit.addons.essentials import FPS_cam, CamController

obj = GameObject()
obj2 = GameObject(children=[obj])

obj3 = copy.deepcopy(obj2)