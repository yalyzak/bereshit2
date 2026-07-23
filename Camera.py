from bereshit.bereshitCore import Component

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
