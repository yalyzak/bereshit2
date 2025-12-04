from bereshit import  Vector3
class code:
    def Start(self):

        self.parent.Rigidbody.AddForce(Vector3(0, -7000, 0), Vector3(0, 5.25,-2.5))
        self.parent.Rigidbody.AddForce(Vector3(0, 7000, 0), Vector3(0, 4.75,-1.5))
        # self.parent.Rigidbody.AddForce(Vector3(0, 100, 0), Vector3(0, -0.5, -0.5))
