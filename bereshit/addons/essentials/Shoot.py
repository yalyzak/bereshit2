from bereshit import Object,Camera,Vector3, Rigidbody, BoxCollider, MeshRander, Quaternion, Render, Physics
import mouse  # pip install mouse
import copy
class Shoot:
    def __init__(self,target):
        self.cooldown = 0.01   # seconds between shots
        self.timer = 0.0      # time passed since last shot
        self.speed = 10
        self.target = target
        self.force = 10


    def onClick(self):
        # print("g")
        forward = self.parent.quaternion.rotate(Vector3(0,0,1))
        hit = Physics.Raycast(self.parent.position.to_np(),forward.to_np(),self.target.get_component("collider"))
        if hit is not None:
            self.target.Rigidbody.AddForce(forward * self.force,ContactPoint=Vector3.from_np(hit))
            print(forward * self.force)
    def Start(self):
        self.render = self.parent.Camera.render
    def Update(self, dt):

        # advance the timer
        self.timer += dt

        if mouse.is_pressed("left") and self.timer >= 0.2:
            self.render.add_ui_rect(self.render.window_size[0]/2,self.render.window_size[1]/2,100,100)
            self.onClick()
            self.timer = 0.0
            # self.cooldown = 1

