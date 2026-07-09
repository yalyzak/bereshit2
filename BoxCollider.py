import numpy as np

from bereshit.Vector3 import Vector3
from bereshit.Quaternion import Quaternion
from bereshit.Physics import RaycastHit
from bereshit.Collider import Collider, ContactPoints, Collision
from bereshit.Cache import Cache

class BoxCollider(Collider):

    @staticmethod
    def check_collision(collider1, collider2, single_point=False):
        aabb_hit = BoxCollider.aabb_collision(collider1, collider2)

        if not aabb_hit:
            collider1.handle_collision_exit()
            collider2.handle_collision_exit()
            return None

        sat_result = collider1.__SAT(collider2)
        if sat_result is None:
            collider1.handle_collision_exit()
            collider2.handle_collision_exit()
            return None

        contacts = BoxCollider.__generate_contacts(sat_result)

        collider1.handle_collision_events(collider2, contacts)
        collider2.handle_collision_events(collider1, contacts)

        if collider1.is_trigger or collider2.is_trigger:
            return None

        return contacts

    def Raycast(self, origin, direction, maxDistance=float('inf'), hit=None):  # needs fixing
        return self.__ray_obb_intersection(origin, direction, self.parent.position.to_np(),
                                           self.parent.quaternion.to_matrix3(self.parent.Cache), self.parent.size.to_np() * 0.5)

    @staticmethod
    def __generate_contacts(sat_result):
        normal = sat_result["normal"]
        penetration = sat_result["penetration"]
        collision_type = sat_result["type"]
        axis_index = sat_result["axis_index"]

        A = sat_result["A"]
        B = sat_result["B"]

        # World data
        a_center = A.position
        b_center = B.position

        a_axes = A.__get_axes(A.quaternion, A.parent.Cache)
        b_axes = B.__get_axes(B.quaternion, B.parent.Cache)

        a_half = A.size * 0.5
        b_half = B.size * 0.5

        # ---------------------------
        # EDGE–EDGE CASE
        # ---------------------------
        if collision_type == "edge":
            i, j = axis_index

            p1, q1 = BoxCollider.__get_edge_segment(a_center, a_axes, a_half.to_np(), i, normal)
            p2, q2 = BoxCollider.__get_edge_segment(b_center, b_axes, b_half.to_np(), j, -normal)

            c1, c2 = BoxCollider.__closest_points_between_segments(p1, q1, p2, q2)

            contact_point = [(c1 + c2) * 0.5]
            return ContactPoints(contact_point, normal, penetration)

        # ---------------------------
        # FACE–FACE CASE
        # ---------------------------
        if collision_type == "a":
            ref = A
            inc = B
            ref_axis_index = axis_index
            flip = False
        else:
            ref = B
            inc = A
            ref_axis_index = axis_index
            flip = True
            normal = -normal  # ensure normal points A → B

        ref_center = ref.position
        ref_axes = ref.__get_axes(ref.quaternion.conjugate())
        ref_half = ref.size * 0.5

        inc_center = inc.position
        inc_axes = inc.__get_axes(inc.quaternion.conjugate())
        inc_half = inc.size * 0.5

        # Reference face
        ref_normal = ref_axes[ref_axis_index]
        if ref_normal.dot(normal) < 0:
            ref_normal = -ref_normal

        ref_face = BoxCollider.__get_face_vertices(ref_center, ref_axes, ref_half.to_np(), ref_axis_index,
                                                   ref_normal)  # this is ok

        # Incident face (most opposite)
        inc_face = BoxCollider.__get_incident_face(inc_center, inc_axes, inc_half.to_np(), normal)
        # Clip incident face against reference side planes
        clipped = inc_face
        for i in range(4):
            p1 = ref_face[i]
            p2 = ref_face[(i + 1) % 4]

            edge = p2 - p1
            plane_normal = edge.cross(ref_normal).normalized()
            # Ensure it points inward
            to_center = ref_center - p1
            if plane_normal.dot(to_center) < 0:
                plane_normal.NegativeSelf()

            clipped = BoxCollider.__clip_polygon(clipped, p1, -plane_normal)

            if not clipped:
                break

        # Keep only points behind reference face
        contacts = []
        ref_plane_d = ref_normal.dot(ref_face[0])

        for p in clipped:
            depth = ref_plane_d - ref_normal.dot(p)
            if depth >= 0:
                projected_p = p + ref_normal * depth
                contacts.append(projected_p)
        average = ContactPoints.average_point(contacts)
        if average:
            contacts.insert(0, average)
        return ContactPoints(contacts, sat_result["normal"], penetration)

    def __SAT(self, other_collider):
        a_center = self.position
        b_center = other_collider.position

        a_axes = self.__get_axes(self.quaternion, self.parent.Cache)
        b_axes = self.__get_axes(other_collider.quaternion.conjugate(), other_collider.parent.Cache)

        a_half = self.size * 0.5
        b_half = other_collider.size * 0.5

        a_half_sizes = [a_half.x, a_half.y, a_half.z]
        b_half_sizes = [b_half.x, b_half.y, b_half.z]

        axes_to_test = []

        for i in range(3):
            axes_to_test.append(("a", i, a_axes[i]))
            axes_to_test.append(("b", i, b_axes[i]))

        for i in range(3):
            for j in range(3):
                cross = a_axes[i].cross(b_axes[j])
                if cross.magnitude() > 1e-6:
                    axes_to_test.append(("edge", (i, j), cross.normalized()))

        smallest_overlap = float("inf")
        collision_axis = None
        collision_type = None
        collision_axis_indices = None

        for source, indices, axis in axes_to_test:
            proj_a = BoxCollider.__project_box(a_center, a_axes, a_half_sizes, axis)
            proj_b = BoxCollider.__project_box(b_center, b_axes, b_half_sizes, axis)

            if not BoxCollider.__overlap_on_axis(proj_a, proj_b):
                return None

            overlap = min(proj_a[1], proj_b[1]) - max(proj_a[0], proj_b[0])
            if overlap < smallest_overlap:
                smallest_overlap = overlap
                collision_axis = axis
                collision_type = source
                collision_axis_indices = indices

        if (b_center - a_center).dot(collision_axis) < 0:
            collision_axis = -collision_axis
            # if collision_type == "a":
            #     collision_type = 'b'
            # elif collision_type == "b":
            #     collision_type = 'a'

        return {
            "normal": collision_axis,
            "penetration": smallest_overlap,
            "type": collision_type,  # "a", "b", "edge"
            "axis_index": collision_axis_indices,
            "A": self,
            "B": other_collider
        }


    def __get_axes(self, rotation, cache=None):
        R = rotation.to_matrix3(cache)
        return [
            Vector3(*R[:, 0]).normalized(),
            Vector3(*R[:, 1]).normalized(),
            Vector3(*R[:, 2]).normalized(),
        ]

    @staticmethod
    def __project_box(center, axes, half_sizes, axis):
        c = center.x * axis.x + center.y * axis.y + center.z * axis.z

        a0 = axes[0]
        a1 = axes[1]
        a2 = axes[2]

        d0 = axis.x * a0.x + axis.y * a0.y + axis.z * a0.z
        d1 = axis.x * a1.x + axis.y * a1.y + axis.z * a1.z
        d2 = axis.x * a2.x + axis.y * a2.y + axis.z * a2.z

        r = (
                abs(d0) * half_sizes[0] +
                abs(d1) * half_sizes[1] +
                abs(d2) * half_sizes[2]
        )

        return c - r, c + r

    @staticmethod
    def __overlap_on_axis(p1, p2):
        return not (p1[1] < p2[0] or p2[1] < p1[0])

    @staticmethod
    def __get_incident_face(center, axes, half_sizes, collision_normal):
        # Find box axis most aligned with collision normal
        best_index = 0
        best_dot = axes[0].dot(collision_normal)

        for i in range(1, 3):
            d = axes[i].dot(collision_normal)
            if abs(d) > abs(best_dot):
                best_dot = d
                best_index = i

        # Incident face normal should point opposite collision normal
        face_normal = axes[best_index]
        if face_normal.dot(collision_normal) > 0:
            face_normal.NegativeSelf()

        return BoxCollider.__get_face_vertices(
            center,
            axes,
            half_sizes,
            best_index,
            face_normal
        )

    @staticmethod
    def __get_face_vertices(center, axes, half, axis_index, normal):
        u = axes[(axis_index + 1) % 3]
        v = axes[(axis_index + 2) % 3]

        hu = float(half[(axis_index + 1) % 3])
        hv = float(half[(axis_index + 2) % 3])
        hn = float(half[axis_index])

        face_center = center + normal * hn

        return [
            face_center + u * hu + v * hv,
            face_center - u * hu + v * hv,
            face_center - u * hu - v * hv,
            face_center + u * hu - v * hv,
        ]

    @staticmethod
    def __clip_polygon(poly, plane_point, plane_normal):
        result = []

        for i in range(len(poly)):
            a = poly[i]
            b = poly[(i + 1) % len(poly)]

            da = (a - plane_point).dot(plane_normal)
            db = (b - plane_point).dot(plane_normal)

            if da <= 0:
                result.append(a)

            if da * db < 0:
                t = da / (da - db)
                result.append(a + (b - a) * t)

        return result

    @staticmethod
    def __get_edge_segment(center, axes, half, axis_index, normal):
        axis = axes[axis_index]

        # pick edge direction
        dir1 = axes[(axis_index + 1) % 3]
        dir2 = axes[(axis_index + 2) % 3]

        offset = (
                axis * float(half[axis_index]) +
                dir1 * float(half[(axis_index + 1) % 3]) * (1 if dir1.dot(normal) > 0 else -1) +
                dir2 * float(half[(axis_index + 2) % 3]) * (1 if dir2.dot(normal) > 0 else -1)
        )

        p = center + offset - axis * float(half[axis_index])
        q = center + offset + axis * float(half[axis_index])

        return p, q

    @staticmethod
    def __closest_points_between_segments(p1, q1, p2, q2):
        d1 = q1 - p1
        d2 = q2 - p2
        r = p1 - p2

        a = d1.dot(d1)
        e = d2.dot(d2)
        f = d2.dot(r)

        if a <= 1e-6 and e <= 1e-6:
            return p1, p2

        if a <= 1e-6:
            t = f / e
            t = max(0, min(1, t))
            return p1, p2 + d2 * t

        c = d1.dot(r)

        if e <= 1e-6:
            s = max(0, min(1, -c / a))
            return p1 + d1 * s, p2

        b = d1.dot(d2)
        denom = a * e - b * b

        if denom != 0:
            s = max(0, min(1, (b * f - c * e) / denom))
        else:
            s = 0

        t = (b * s + f) / e

        if t < 0:
            t = 0
            s = max(0, min(1, -c / a))
        elif t > 1:
            t = 1
            s = max(0, min(1, (b - c) / a))

        return p1 + d1 * s, p2 + d2 * t

    @staticmethod
    def __ray_box_intersection(self, ray_origin, ray_dir, box_min, box_max):
        tmin = float('-inf')
        tmax = float('inf')

        for i in range(3):
            origin = ray_origin[i]
            direction = ray_dir[i]
            bmin = box_min[i]
            bmax = box_max[i]

            if abs(direction) < 1e-8:
                # Ray parallel to slab
                if origin < bmin or origin > bmax:
                    return RaycastHit()
            else:
                t1 = (bmin - origin) / direction
                t2 = (bmax - origin) / direction

                t_near = min(t1, t2)
                t_far = max(t1, t2)

                tmin = max(tmin, t_near)
                tmax = min(tmax, t_far)

                if tmin > tmax:
                    return RaycastHit()

        # 🚨 Critical fix: reject hits behind the ray
        if tmax < 0:
            return RaycastHit()

        # If inside the box, use exit point
        t_hit = tmin if tmin >= 0 else tmax

        hit_point = (
            ray_origin[0] + ray_dir[0] * t_hit,
            ray_origin[1] + ray_dir[1] * t_hit,
            ray_origin[2] + ray_dir[2] * t_hit,
        )

        return RaycastHit(point=Vector3.from_np(hit_point) + self.parent.position, collider=self)

    def __ray_obb_intersection(self, ray_origin, ray_dir, box_center, rotation_matrix, half_size):
        """
        ray_origin, ray_dir: np.array shape (3,)
        box_center: np.array (3,)
        rotation_matrix: 3x3 matrix (columns = box axes)
        half_size: np.array (hx, hy, hz)

        Returns:
            (hit: bool, tmin: float, tmax: float)
        """

        # Step 1: move ray into box local space
        # inverse rotation = transpose (for orthonormal matrix)
        inv_rot = rotation_matrix.T

        local_origin = inv_rot @ (ray_origin - box_center)
        local_dir = inv_rot @ ray_dir

        # Step 2: now it's just an AABB centered at (0,0,0)
        box_min = -half_size
        box_max = half_size

        return BoxCollider.__ray_box_intersection(self, local_origin, local_dir, box_min, box_max)

    def attach(self, owner_object):
        super().attach(owner_object)
        # box = owner_object.get_component(BoxCollider)  # will remove duplicate renders by default
        # if box:
        #     owner_object.remove_component("Collider")

        self.obj = owner_object
        return "Collider"  # need to be change to "Collider" but fucks up the whole update loop
