class Raycast:
    class RaycastHit:
        def __init__(self, point=None, normal=None, distance=None, collider=None, transform=None, rigidbody=None):
            self.point = point
            self.normal = normal
            self.distance = distance
            self.collider = collider
            self.transform = transform
            self.rigidbody = rigidbody

    def __init__(self, origin, direction, maxDistance=float('inf'), hit=None):
        self.origin = origin
        self.direction = direction
        self.maxDistance = maxDistance
        self.hit = hit if hit is not None else Raycast.RaycastHit()