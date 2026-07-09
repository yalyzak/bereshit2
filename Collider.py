import numpy as np

from bereshit.Physics import RaycastHit
from bereshit.Vector3 import Vector3
from bereshit.Quaternion import Quaternion
from bereshit.bereshitCore import Component

class Collider(Component):
    Scale = 1

    def __init__(self, size=None, position=None, rotation=Vector3(), object_pointer=None, is_trigger=False):
        super().__init__()

        self.half_size = None
        self.__delta_size = Vector3() if not size else size
        self.__delta_position = Vector3() if not position else position
        self.__delta_quaternion = Quaternion.euler(rotation)

        self.obj = object_pointer
        self.is_trigger = is_trigger
        self.enter = False
        self.stay = False
        self.other = None
        self.__cached_min, self.__cached_max = None, None

    @property
    def size(self):
        return self.__delta_size + self.parent.size

    @property
    def position(self):
        return self.__delta_position + self.parent.position

    @property
    def quaternion(self):
        return self.__delta_quaternion * self.parent.quaternion

    def attach(self, parent):
        self.half_size = (self.__delta_size + parent.transform.size) * 0.5

    @staticmethod
    def check_collision(collider1, collider2, single_point=False):
        pass

    @staticmethod
    def aabb_collision(obj1, obj2):
        min1, max1 = obj1.get_aabb()
        min2, max2 = obj2.get_aabb()

        # Check overlap on all 3 axes
        return (
                (min1.x <= max2.x and max1.x >= min2.x) and
                (min1.y <= max2.y and max1.y >= min2.y) and
                (min1.z <= max2.z and max1.z >= min2.z)
        )

    def get_aabb(self):
        if not self.parent.Cache.aabb_dirty:
            return self.__cached_min, self.__cached_max

        # Half extents
        if self.parent.Cache.rotation_dirty:
            abs_rot = self.quaternion.to_matrix3_abs(self.parent.Cache)

            # Compute world extents
            world_half = self.half_size.MatrixMultiplication(abs_rot)
            self.__cached_min, self.__cached_max = self.position - world_half, self.position + world_half
            # AABB min/max
            self.parent.Cache.aabb_dirty = False
            return self.position - world_half, self.position + world_half

        self.__cached_min, self.__cached_max = self.position - self.half_size, self.position + self.half_size
        self.parent.Cache.aabb_dirty = False
        return self.position - self.half_size, self.position + self.half_size

    def OnCollisionEnter(self, collision):
        self.enter = True
        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionEnter') and component.OnCollisionEnter is not None and component != self:
                component.OnCollisionEnter(collision)

    def OnCollisionStay(self, collision):
        self.enter = False
        self.stay = True
        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionStay') and component.OnCollisionStay is not None and component != self:
                component.OnCollisionStay(collision)

    def OnCollisionExit(self, collision):
        self.enter = False
        self.stay = False
        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionExit') and component.OnCollisionExit is not None and component != self:
                component.OnCollisionExit(collision)

    def OnTriggerEnter(self, collision):
        """This method can be overwritten by subclasses to handle trigger events."""
        self.enter = True
        for component in self.parent.components.values():
            if hasattr(component, 'OnTriggerEnter') and component.OnTriggerEnter is not None and component != self:
                component.OnTriggerEnter(collision)

    def OnTriggerStay(self, collision):
        self.enter = False
        self.stay = True
        for component in self.parent.components.values():
            if hasattr(component, 'OnTriggerStay') and component.OnTriggerStay is not None and component != self:
                component.OnTriggerStay(collision)

    def OnTriggerExit(self, collision):
        self.stay = False
        self.enter = False
        """This method can be overwritten by subclasses to handle trigger events."""
        for component in self.parent.components.values():
            if hasattr(component, 'OnTriggerExit') and component.OnTriggerExit is not None and component != self:
                component.OnTriggerExit(collision)

    def handle_collision_exit(self):
        collision = Collision(self.other, None)
        if not self.is_trigger:
            if self.stay or self.enter:
                self.OnCollisionExit(collision)
        else:
            if self.stay or self.enter:
                self.OnTriggerExit(collision)


    def handle_collision_events(self, other_collider, result):
        same_collider = self.other == other_collider
        self.other = other_collider
        collision = Collision(other_collider, result)
        if not self.is_trigger:
            if (self.enter or self.stay) and same_collider:
                self.OnCollisionStay(collision)
            else:
                self.OnCollisionEnter(collision)
        else:
            if (self.enter or self.stay) and same_collider:
                self.OnTriggerStay(collision)
            else:
                self.OnTriggerEnter(collision)


    def Raycast(self, origin, direction, maxDistance=float('inf'), hit=None):
        print(f"Ray casting was not defined for {self.__class__.__name__}")
        return RaycastHit()


    @staticmethod
    def sweep_and_prune(colliders):
        """
        Broad-phase Sweep and Prune collision detection.

        Args:
            colliders: iterable of collider objects
                       each collider must implement:
                           get_aabb() -> (min_vec, max_vec)

                       where min_vec/max_vec have:
                           .x .y .z

        Returns:
            List of tuples:
                [(collider_a, collider_b), ...]
        """

        endpoints = []

        # Build X-axis endpoints
        for collider in colliders:
            min_v, max_v = collider.get_aabb()

            endpoints.append((min_v.x, True, collider))  # start
            endpoints.append((max_v.x, False, collider))  # end

        # Sort endpoints by position
        endpoints.sort(key=lambda e: e[0])

        active = set()
        candidate_pairs = []

        # Sweep along X
        for _, is_start, collider in endpoints:

            if is_start:
                # Compare against active colliders
                min_a, max_a = collider.get_aabb()

                for other in active:
                    min_b, max_b = other.get_aabb()

                    # Check Y overlap
                    overlap_y = (
                            min_a.y <= max_b.y and
                            max_a.y >= min_b.y
                    )

                    # Check Z overlap
                    overlap_z = (
                            min_a.z <= max_b.z and
                            max_a.z >= min_b.z
                    )

                    if overlap_y and overlap_z:
                        candidate_pairs.append((collider, other))

                active.add(collider)

            else:
                active.remove(collider)

        return candidate_pairs


class ContactPoints:
    def __init__(self, contact_points, normal, depth):
        self.contact_points = contact_points
        self.normal = normal
        self.depth = depth

    @staticmethod
    def average_point(contact_points):
        count = len(contact_points)
        if count:
            total_p = Vector3(0, 0, 0)

            for point in contact_points:
                total_p += point

            avg_p = total_p / count

            return avg_p
        return None


class Collision:
    def __init__(self, other, contactPoints):
        self.other = other
        self.contactPoints = contactPoints
