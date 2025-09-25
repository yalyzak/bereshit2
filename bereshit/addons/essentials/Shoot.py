from bereshit import Object,Camera,Vector3, Rigidbody, BoxCollider, MeshRander ,Quaternion
import mouse  # pip install mouse
import copy
class Shoot:
    def __init__(self):
        self.cooldown = 0.1   # seconds between shots
        self.timer = 0.0      # time passed since last shot
        self.speed = 10

    def onClick(self):
        # print("g")
        boolet = Object(position=copy.deepcopy(self.parent.position),name="boolet")
        forward = self.parent.quaternion.rotate(Vector3(0,0,1))
        boolet.add_component(BoxCollider())
        boolet.add_component(Rigidbody(
            velocity=(forward * self.speed),
            useGravity=False,
            mass=100
        ))
        self.parent.world.add_child(boolet)

    def Update(self, dt):
        # advance the timer
        self.timer += dt

        if mouse.is_pressed("left") and self.timer >= self.cooldown:
            self.onClick()
            self.timer = 0.0
            # self.cooldown = 1

