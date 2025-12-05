import random

from bereshit import Object,Camera,Vector3, Rigidbody, BoxCollider, MeshRander, Quaternion, Render, Physics
import mouse  # pip install mouse
from bereshit.render import Text,Box

import copy
class Shoot:
    def __init__(self,target):
        self.cooldown = 0.01   # seconds between shots
        self.timer = 0.0      # time passed since last shot
        self.speed = 10
        self.target = target
        self.force = 50
        self.shots = 10
        self.shots_text = Text(str(self.shots), center=(120,850), scale=1)

        self.gimos = Object(position=Vector3(1000,1000,1000),size=Vector3(.1,.1,.1))

    def onClick(self):
        # print("g")
        if self.shots == 0:
            self.shots = 10
        self.shots -= 1
        self.shots_text.text = str(self.shots)
        # self.render.t = str(self.shots)
        forward = self.parent.quaternion.rotate(Vector3(0,0,1))
        hits = Physics.RaycastAll(self.parent.position.to_np(),forward.to_np())
        for hit in hits:
            if hit.point is not None and hit.collider.parent.get_component(self.target):
                hit.collider.parent.Rigidbody.AddForce(forward * self.force)#,Vector3.from_np(hit.point)
            # self.gimos.position = Vector3.from_np(hit)
    def Start(self):
        self.render = self.parent.Camera.render
        # self.target.add_child(self.gimos)
        self.render.add_text_rect(self.shots_text)
        # self.shoot = Box(size=(100,100),opacity=0.5)
        # self.render.add_ui_rect(self.shoot)

    def Update(self, dt):

        # advance the timer
        self.timer += dt
        # self.shoot.opacity = random.Random()
        if mouse.is_pressed("left") and self.timer >= 0.2:
            # self.shoot.opacity = 1

            self.onClick()
            self.timer = 0.0
            # self.cooldown = 1

