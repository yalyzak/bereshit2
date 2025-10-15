import numpy as np


class Physics:
    # class RaycastHit:
    #     def __init__(self, point=None, normal=None, distance=None, collider=None, transform=None, rigidbody=None):
    #         self.point = point
    #         self.normal = normal
    #         self.distance = distance
    #         self.collider = collider
    #         self.transform = transform
    #         self.rigidbody = rigidbody

    def __init__(self, origin, direction, maxDistance=float('inf'), hit=None):
        self.origin = origin
        self.direction = direction
        self.maxDistance = maxDistance
        # self.hit = hit if hit is not None else Raycast.RaycastHit()
    @staticmethod
    def Raycast(origin, direction, layerMask, maxDistance=float('inf')):
        def ray_triangle_intersect(orig, dir, triangle, eps=1e-90):
            v0, v1, v2 = triangle
            # Compute edges
            edge1 = v1 - v0
            edge2 = v2 - v0

            # Begin calculating determinant
            h = np.cross(dir, edge2)
            a = np.dot(edge1, h)

            if -eps < a < eps:
                return None  # Ray is parallel to the triangle

            f = 1.0 / a
            s = orig - v0
            u = f * np.dot(s, h)

            if u < 0.0 or u > 1.0:
                return None

            q = np.cross(s, edge1)
            v = f * np.dot(dir, q)

            if v < 0.0 or u + v > 1.0:
                return None

            # Compute t to find intersection point
            t = f * np.dot(edge2, q)
            if t > eps:
                hit_point = orig + dir * t
                return hit_point  # intersection point
            else:
                return None  # Line intersects but not a ray
        triangles = layerMask.triangles()
        for triangle in triangles:
            hit = ray_triangle_intersect(origin, direction, triangle)
            if hit:
                return hit


