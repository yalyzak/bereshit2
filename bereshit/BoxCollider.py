import numpy as np

from bereshit.Vector3 import Vector3
from bereshit.Quaternion import Quaternion


class BoxCollider:
    def __init__(self, size=Vector3(1, 1, 1), object_pointer=None, is_trigger=False):
        self.size = size
        self.obj = object_pointer
        self.is_trigger = is_trigger
        self.enter = False

    def OnCollisionEnter(self, other_collider):
        self.enter = True

        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionEnter') and component.OnCollisionEnter is not None and component != self:
                component.OnCollisionEnter(other_collider)

    def OnCollisionStay(self, other_collider):
        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionStay') and component.OnCollisionStay is not None and component != self:
                component.OnCollisionStay(other_collider)

    def OnCollisionExit(self, other_collider):
        self.enter = False
        for component in self.parent.components.values():
            if hasattr(component, 'OnCollisionExit') and component.OnCollisionExit is not None and component != self:
                component.OnCollisionExit(other_collider)

    def OnTriggerEnter(self, other_collider):
        """This method can be overwritten by subclasses to handle trigger events."""
        for component in self.parent.components.values():
            if hasattr(component, 'OnTriggerEnter') and component.OnTriggerEnter is not None and component != self:
                component.OnTriggerEnter(other_collider)

    def get_bounds(self):
        # Get 8 corners in local space
        half = self.size * 0.5
        local_corners = [
            Vector3(x, y, z)
            for x in (-half.x, half.x)
            for y in (-half.y, half.y)
            for z in (-half.z, half.z)
        ]

        # Rotate and translate to world space
        world_corners = [rotate_vector_old(corner, self.obj.position, self.obj.rotation) + self.obj.position for corner
                         in
                         local_corners]

        # Find min/max of all corners
        min_bound = Vector3(
            min(c.x for c in world_corners),
            min(c.y for c in world_corners),
            min(c.z for c in world_corners)
        )
        max_bound = Vector3(
            max(c.x for c in world_corners),
            max(c.y for c in world_corners),
            max(c.z for c in world_corners)
        )
        bounds = []
        for child in self.obj.get_children_bereshit():
            bounds = child.collider.get_bounds()
        bounds.append([min_bound, max_bound])
        return bounds

    def check_collision(self, other, single_point=False):

        other_collider = getattr(other, 'collider', other)
        if other_collider is None:
            return None

        # --- Internal Functions ---
        def generate_face_to_face_contact(ref_center, ref_axes, ref_half,
                                          inc_center, inc_axes, inc_half,
                                          normal_axis, collision_normal, penetration_depth, ref):
            def get_face_corners(center, axes, half_sizes, normal_axis):
                u, v = [i for i in range(3) if i != normal_axis]
                corners = []
                for i in [-1, 1]:
                    for j in [-1, 1]:
                        corner = center + axes[u] * half_sizes[u] * i + axes[v] * half_sizes[v] * j
                        corners.append(corner)
                return corners

            def line_plane_intersection(p1, p2, pA, pB, pC):
                """
                Find intersection of line (p1->p2) with plane (defined by pA, pB, pC).
                Returns intersection point or None if parallel.
                """
                # Direction vector of line
                d = p2 - p1
                # Normal to plane
                n = np.cross(pB - pA, pC - pA)
                denom = np.dot(n, d)
                if abs(denom) < 1e-9:
                    return None  # Line parallel to plane
                t = np.dot(n, pA - p1) / denom
                return p1 + t * d

            def point_in_triangle(pt, a, b, c):
                """
                Check if point pt lies inside triangle (a, b, c) using barycentric coordinates.
                """
                v0, v1, v2 = c - a, b - a, pt - a
                dot00 = np.dot(v0, v0)
                dot01 = np.dot(v0, v1)
                dot02 = np.dot(v0, v2)
                dot11 = np.dot(v1, v1)
                dot12 = np.dot(v1, v2)

                invDenom = 1 / (dot00 * dot11 - dot01 * dot01 + 1e-12)
                u = (dot11 * dot02 - dot01 * dot12) * invDenom
                v = (dot00 * dot12 - dot01 * dot02) * invDenom

                return (u >= 0) and (v >= 0) and (u + v <= 1)

            def coplanar(p1, p2, p3, p4, tol=1e-9):
                """
                Check if 4 points are coplanar.
                """
                v1, v2, v3 = p2 - p1, p3 - p1, p4 - p1
                return abs(np.dot(np.cross(v1, v2), v3)) < tol

            def line_shape_intersections(line_pts, shape_pts):
                """
                Compute intersections between a line (2 pts) and a shape (4 pts).
                Returns list of intersection points.
                """
                p1, p2 = map(np.array, line_pts)
                shape = [np.array(p) for p in shape_pts]

                intersections = []

                if coplanar(*shape):
                    # Treat as quadrilateral: split into 2 triangles
                    tris = [(shape[0], shape[1], shape[2]),
                            (shape[0], shape[2], shape[3])]
                else:
                    # Treat as tetrahedron: 4 triangular faces
                    tris = [(shape[0], shape[1], shape[2]),
                            (shape[0], shape[1], shape[3]),
                            (shape[0], shape[2], shape[3]),
                            (shape[1], shape[2], shape[3])]

                for A, B, C in tris:
                    ipt = line_plane_intersection(p1, p2, A, B, C)
                    if ipt is not None and point_in_triangle(ipt, A, B, C):
                        # Check duplicates
                        if not any(np.allclose(ipt, q, atol=1e-9) for q in intersections):
                            intersections.append(ipt)

                return intersections

            def point_in_quad(pt, quad, tol=1e-9):
                """
                Check if a point lies inside a quadrilateral (assumed coplanar).
                """
                A, B, C, D = quad
                # Ensure pt is in the same plane as the quad
                n = np.cross(B - A, C - A)
                if abs(np.dot(n, pt - A)) > tol:
                    return False  # not in plane

                # Then check triangle membership
                return point_in_triangle(pt, A, B, C) or point_in_triangle(pt, A, C, D)

            def point_plane_signed_distance(pt, A, B, C):
                """Signed distance from point to plane defined by triangle ABC."""
                n = np.cross(B - A, C - A)
                n = n / np.linalg.norm(n)
                return np.dot(pt - A, n)

            def point_distance_to_shape_signed(pt, shape_pts):
                """
                Return (inside?, signed_depth) for point relative to shape.
                - For quadrilateral: signed distance to plane (0 if inside polygon).
                - For tetrahedron: max signed face distance (<=0 inside).
                """
                shape = [np.array(p) for p in shape_pts]
                pt = np.array(pt)

                if coplanar(*shape):  # quadrilateral
                    A, B, C, D = shape
                    d = point_plane_signed_distance(pt, A, B, C)
                    if point_in_quad(pt, shape):
                        return True, d  # inside → signed depth relative to plane
                    else:
                        return False, d  # outside but still signed
                else:  # tetrahedron
                    faces = [(shape[0], shape[1], shape[2]),
                             (shape[0], shape[1], shape[3]),
                             (shape[0], shape[2], shape[3]),
                             (shape[1], shape[2], shape[3])]
                    dists = [point_plane_signed_distance(pt, *f) for f in faces]
                    inside = all(d <= 0 for d in dists) or all(d >= 0 for d in dists)
                    return inside, max(dists, key=abs)  # use the most "limiting" face

            # Example usage:
            def point_in_quad(pt, quad):
                """
                Check if a point lies inside a quadrilateral (assumed coplanar).
                """
                A, B, C, D = quad
                return point_in_triangle(pt, A, B, C) or point_in_triangle(pt, A, C, D)

            def point_in_tetrahedron(pt, tet):
                """
                Check if a point lies inside a tetrahedron.
                """
                A, B, C, D = tet

                def same_side(p, q, a, b, c):
                    # normal of triangle
                    n = np.cross(b - a, c - a)
                    return np.dot(n, p - a) * np.dot(n, q - a) >= 0

                # pick one reference vertex as "inside" point (D)
                return (same_side(pt, D, A, B, C) and
                        same_side(pt, C, A, B, D) and
                        same_side(pt, B, A, C, D) and
                        same_side(pt, A, B, C, D))

            def point_in_shape(pt, shape_pts):
                """
                General check: point inside quadrilateral or tetrahedron.
                """
                shape = [np.array(p) for p in shape_pts]
                pt = np.array(pt)

                if coplanar(*shape):
                    return point_in_quad(pt, shape)
                else:
                    return point_in_tetrahedron(pt, shape)

            def sdf(x, ref):
                result = []
                result2 = []

                plane_face, incident_face = x
                for i in range(4):
                    shape_points = [1, 2, 3, 4]
                    A = plane_face[i].to_tuple()
                    B = plane_face[(i + 1) % 4].to_tuple()
                    for i in range(len(incident_face)):
                        shape_points[i] = incident_face[i].to_tuple()
                    line_points = [A, B]
                    for lp in line_points:
                        inside, depth = point_distance_to_shape_signed(lp, shape_points)
                        if point_in_shape(lp, shape_points):
                            result2.append(lp)
                    p = line_shape_intersections(line_points, shape_points)
                    if len(p) > 0:
                        result.append(p[0])
                        # result.append(p[1])
                if len(result) == 0:
                    result = result2

                for i in range(4):
                    shape_points = [1, 2, 3, 4]
                    A = incident_face[i].to_tuple()
                    B = incident_face[(i + 1) % 4].to_tuple()
                    for i in range(len(plane_face)):
                        shape_points[i] = plane_face[i].to_tuple()
                    line_points = [A, B]
                    p = line_shape_intersections(line_points, shape_points)
                    # if len(p)>0:
                    #     result.append(p[0])
                    # result.append(p[1])
                    for lp in line_points:
                        inside, depth = point_distance_to_shape_signed(lp, shape_points)
                        if depth <= -0.1 and point_in_shape(lp, shape_points):
                            result.append(lp)
                return result

            def clip_polygon_against_plane(polygon, plane_point, plane_normal):
                clipped = []
                for i in range(len(polygon)):
                    A = polygon[i]
                    B = polygon[(i + 1) % len(polygon)]
                    dA = (A - plane_point).dot(plane_normal)
                    dB = (B - plane_point).dot(plane_normal)

                    if dA >= 0:
                        if dB >= 0:  # both inside
                            clipped.append(B)
                        else:  # A in, B out → clip
                            t = dA / (dA - dB)
                            clipped.append(A + (B - A) * t)
                    elif dB >= 0:  # A out, B in
                        t = dA / (dA - dB)
                        clipped.append(A + (B - A) * t)
                        clipped.append(B)
                return clipped

            # --- Reference face setup ---
            n_ref = ref_axes[normal_axis]
            my_normal = (inc_center - ref_center).normalized().dot(collision_normal) * collision_normal
            sign_inc = 1.0 if (inc_center - ref_center).normalized().dot(collision_normal) < 0.0 else -1.0

            ref_face_center = ref_center + n_ref * ref_half[normal_axis] * -sign_inc

            # --- Incident face setup ---
            incident_axis = max(range(3), key=lambda i: inc_axes[i].dot(collision_normal))
            n_inc = inc_axes[incident_axis]

            # sign_inc = 1.0 if n_inc.dot(collision_normal) < 0.0 else -1.0
            incident_face_center = inc_center + n_inc * inc_half[incident_axis] * sign_inc

            incident_face = get_face_corners(incident_face_center, inc_axes, inc_half, incident_axis)
            plane_face = get_face_corners(ref_face_center, ref_axes, ref_half, normal_axis)

            gizmos = (plane_face, incident_face)

            points = sdf(gizmos, ref)
            final_points = []

            for p in points:
                if len(p) > 0:
                    final_points.append((Vector3.from_np(p), collision_normal * sign_inc, 0))
            return final_points, gizmos

            side_axes = [i for i in range(3) if i != normal_axis]
            planes = []
            for i in side_axes:
                edge_dir = ref_axes[i]
                plane_point = ref_face_center + edge_dir * ref_half[i]
                planes.append((plane_point, -edge_dir))
                plane_point = ref_face_center - edge_dir * ref_half[i]
                planes.append((plane_point, edge_dir))
            gizmos = (planes, incident_face)
            clipped = incident_face
            for point, normal in planes:
                clipped = clip_polygon_against_plane(clipped, point, normal)
                if not clipped:  # back
                    return [], gizmos

            # Filter points below the face
            final_points = []
            for p in clipped:
                depth_offset = -(p - ref_face_center).dot(ref_axes[normal_axis])
                depth = min(penetration_depth, depth_offset)
                # depth = penetration_depth
                if depth >= 0:
                    final_points.append((p, my_normal, depth))

            return final_points, gizmos

        # def generate_edge_to_edge_contact(a_center, a_axes, a_half, b_center, b_axes, b_half, i, j, collision_axis,
        #                                   penetration):
        #     p1 = a_center + a_axes[i] * a_half[i]
        #     p2 = a_center - a_axes[i] * a_half[i]
        #     q1 = b_center + b_axes[j] * b_half[j]
        #     q2 = b_center - b_axes[j] * b_half[j]
        #
        #     # Closest point between two line segments
        #     def closest_point_between_segments(p1, p2, q1, q2):
        #         d1 = p2 - p1
        #         d2 = q2 - q1
        #         r = p1 - q1
        #         a = d1.dot(d1)
        #         e = d2.dot(d2)
        #         f = d2.dot(r)
        #         b = d1.dot(d2)
        #         c = d1.dot(r)
        #
        #         denom = a * e - b * b
        #         if denom == 0:
        #             return (p1 + p2 + q1 + q2) * 0.25  # Fallback: midpoint of both edges
        #
        #         s = (b * f - c * e) / denom
        #         t = (a * f - b * c) / denom
        #
        #         s = max(0, min(1, s))
        #         t = max(0, min(1, t))
        #
        #         closest_a = p1 + d1 * s
        #         closest_b = q1 + d2 * t
        #         return (closest_a + closest_b) * 0.5
        #
        #     pt = closest_point_between_segments(p1, p2, q1, q2)
        #     return [(pt, collision_axis, penetration)]

        def generate_edge_to_edge_contact(
                a_center, a_axes, a_half,
                b_center, b_axes, b_half,
                edge_indices, collision_normal, penetration_depth
        ):
            """
            Edge-edge contact between OBB A (edge along a_axes[i]) and OBB B (edge along b_axes[j]).
            Returns: (contact_points, gizmos)
              contact_points: [(point, normal, penetration_depth)]
              gizmos: list of debug prims (("line", p0, p1), ("arrow", p, n)) etc.
            """
            eps = 1e-9

            def sign(x):
                return 1.0 if x >= 0.0 else -1.0

            def closest_points_on_segments(p1, d1, L1, p2, d2, L2):
                """
                p1,p2: segment centers
                d1,d2: unit directions
                L1,L2: half-lengths  (segment = center +/- d*L)
                Returns: (c1, c2) closest points on the finite segments
                """
                # Line parameters s in [-L1, L1], t in [-L2, L2]
                r = p1 - p2
                a = 1.0  # d1·d1 (unit)
                e = 1.0  # d2·d2 (unit)
                b = d1.dot(d2)  # d1·d2
                c = d1.dot(r)  # d1·(p1-p2)
                f = d2.dot(r)  # d2·(p1-p2)

                denom = a * e - b * b  # = 1 - b^2
                if denom > eps:
                    s = (b * f - c * e) / denom
                else:
                    # Nearly parallel -> pick s = 0 (center) as baseline
                    s = 0.0
                # Clamp s to segment
                s = max(-L1, min(L1, s))

                # Compute t that best matches this s (one-step)
                t = (b * s + f) / e
                t = max(-L2, min(L2, t))

                # Recompute s with clamped t, then clamp again (handles corner cases)
                if denom > eps:
                    s = (b * t - c) / a
                else:
                    # Parallel: choose s by projecting r onto d1
                    s = -c
                s = max(-L1, min(L1, s))

                # Final closest points
                c1 = p1 + d1 * s
                c2 = p2 + d2 * t
                return c1, c2

            i, j = edge_indices
            # Edge directions (unit)
            ai = a_axes[i]
            bj = b_axes[j]
            # Pick the two fixed-signs (±) for each edge so the chosen edges face each other.
            # Use the vector from A to B to decide which "side" of the box we select.
            AtoB = (b_center - a_center)

            # For A: edge along axis i, fix the other two axes to the signs that face B.
            uA, vA = [k for k in range(3) if k != i]
            suA = sign(AtoB.dot(a_axes[uA]))
            svA = sign(AtoB.dot(a_axes[vA]))

            # For B: edge along axis j, fix the other two axes to the signs facing *toward A* (opposite of A->B).
            uB, vB = [k for k in range(3) if k != j]
            suB = -sign(AtoB.dot(b_axes[uB]))
            svB = -sign(AtoB.dot(b_axes[vB]))

            # Edge centers (each is the midpoint of its segment)
            edgeA_center = (
                    a_center
                    + a_axes[uA] * (a_half[uA] * suA)
                    + a_axes[vA] * (a_half[vA] * svA)
            )
            edgeB_center = (
                    b_center
                    + b_axes[uB] * (b_half[uB] * suB)
                    + b_axes[vB] * (b_half[vB] * svB)
            )

            # Half lengths along the edge directions
            LA = a_half[i]
            LB = b_half[j]

            # Closest points between the two finite edges
            cA, cB = closest_points_on_segments(edgeA_center, ai, LA, edgeB_center, bj, LB)

            # Contact point: midpoint of closest points
            contact_p = (cA + cB) * 0.5

            # Contact normal: orient to point from A to B
            n = collision_normal.normalized()
            if (b_center - a_center).dot(n) < 0.0:
                n = -n

            # Build outputs
            contact_points = [(contact_p, n, penetration_depth)]
            gizmos = [
                ("line", edgeA_center - ai * LA, edgeA_center + ai * LA),  # A edge
                ("line", edgeB_center - bj * LB, edgeB_center + bj * LB),  # B edge
                ("line", cA, cB),  # connector
                ("arrow", contact_p, contact_p + n * max(LA, LB) * 0.25),  # normal
            ]
            return contact_points, gizmos

        def get_axes(rotation: Quaternion):
            R = rotation.to_matrix3()  # 3x3 numpy array

            right = Vector3(*R[:, 0]).normalized()
            up = Vector3(*R[:, 1]).normalized()
            forward = Vector3(*R[:, 2]).normalized()

            return [right, up, forward]

        def project_box(center, axes, half_sizes, axis):
            projection_center = center.dot(axis)
            radius = sum(abs(axis.dot(a)) * h for a, h in zip(axes, half_sizes))
            return projection_center - radius, projection_center + radius

        def overlap_on_axis(proj1, proj2):
            return not (proj1[1] < proj2[0] or proj2[1] < proj1[0])

        # --- SAT Collision Detection ---

        a_center = self.obj.position
        b_center = other_collider.obj.position

        a_axes = get_axes(self.obj.quaternion.conjugate())
        b_axes = get_axes(other_collider.obj.quaternion.conjugate())

        a_half = self.obj.size * 0.5
        b_half = other_collider.obj.size * 0.5

        a_half_sizes = [a_half.x, a_half.y, a_half.z]
        b_half_sizes = [b_half.x, b_half.y, b_half.z]

        axes_to_test = []

        # Add 3 axes of A
        for i in range(3):
            axes_to_test.append(("a", i, a_axes[i]))

        # Add 3 axes of B
        for i in range(3):
            axes_to_test.append(("b", i, b_axes[i]))
        #
        # # Add 9 cross-product axes
        # # Add 9 cross-product axes
        # for i in range(3):
        #     for j in range(3):
        #         cross = a_axes[i].cross(b_axes[j])
        #         if cross.magnitude() > 1e-6:
        #             axis = cross.normalized()
        #
        #             # Check if this axis is nearly parallel to an existing axis
        #             is_unique = True
        #             for _, _, existing in axes_to_test:
        #                 if abs(existing.dot(axis)) > 1 - 1e-6:  # almost parallel
        #                     is_unique = False
        #                     break
        #
        #             if is_unique:
        #                 axes_to_test.append(("edge", (i, j), axis))

        smallest_overlap = float('inf')
        collision_axis = None
        for axis_info in axes_to_test:
            source, indices, axis = axis_info
            proj_a = project_box(a_center, a_axes, a_half_sizes, axis)
            proj_b = project_box(b_center, b_axes, b_half_sizes, axis)

            if not overlap_on_axis(proj_a, proj_b):
                return None  # Separating axis found

            overlap = min(proj_a[1], proj_b[1]) - max(proj_a[0], proj_b[0])
            if overlap < smallest_overlap:  # or (overlap == smallest_overlap and source != 'edge')
                smallest_overlap = overlap
                collision_axis = axis
                collision_type = source
                collision_axis_indices = indices
            # elif abs(overlap - smallest_overlap) < 1e-6 and source != 'edge':
            #     smallest_overlap = overlap
            #     collision_axis = axis
            #     collision_type = source
            #     collision_axis_indices = indices
        # print(source)
        if collision_type in ("a", "b"):
            if collision_type == "a":
                ref_center, ref_axes, ref_half = a_center, a_axes, a_half_sizes
                inc_center, inc_axes, inc_half = b_center, b_axes, b_half_sizes
                normal_axis = collision_axis_indices
                ref = (self.parent.Rigidbody, other_collider.parent.Rigidbody)

            else:
                print("G")
                ref = (other_collider.parent.Rigidbody, self.parent.Rigidbody)

                normal_axis = collision_axis_indices
                ref_center, ref_axes, ref_half = b_center, b_axes, b_half_sizes
                inc_center, inc_axes, inc_half = a_center, a_axes, a_half_sizes

            contact_points, gizmos = generate_face_to_face_contact(
                ref_center, ref_axes, ref_half,
                inc_center, inc_axes, inc_half,
                normal_axis, collision_axis, smallest_overlap, ref[0]
            )
        elif collision_type == "edge":
            # i, j = collision_axis_indices  # from your SAT loop
            # contact_points, gizmos = generate_edge_to_edge_contact(
            #     a_center, a_axes, a_half_sizes,
            #     b_center, b_axes, b_half_sizes,
            #     (i, j), collision_axis, smallest_overlap
            # )
            print("gg")
            return None
            # exit()

        def average_contact_data(contact_points):
            if not contact_points:
                return None  # or raise Exception

            total_p = Vector3(0, 0, 0)
            total_n = Vector3(0, 0, 0)
            total_d = 0.0

            for p, n, d in contact_points:
                total_p += p
                total_n += n
                total_d += d

            count = len(contact_points)
            avg_p = total_p / count
            avg_n = total_n.normalized()  # normalize the summed normal vector
            avg_d = total_d / count

            return avg_p, avg_n, avg_d
        if single_point:
            contact_points = average_contact_data(contact_points)
        if contact_points is None or contact_points == []:
            return None

        if self.is_trigger:
            self.OnTriggerEnter(other_collider)
        if other_collider.is_trigger:
            other_collider.OnTriggerEnter(self)

        if self.enter == False:
            self.OnCollisionEnter(other_collider)
        else:
            self.OnCollisionStay(other_collider)

        if other_collider.enter == False:
            other_collider.OnCollisionEnter(self)
        else:
            other_collider.OnCollisionStay(self)

        return contact_points, gizmos, ref

    def attach(self, owner_object):
        self.size = owner_object.size
        self.obj = owner_object
        return "collider"
