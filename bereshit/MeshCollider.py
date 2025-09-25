import numpy as np
import copy

class MeshCollider:

    def __init__(self, vertices=None, object_pointer=None, is_trigger=False):
        self.vertices = copy.deepcopy(vertices) or []  # Local-space Vector3
        self.obj = object_pointer
        self.is_trigger = is_trigger
        self.enter = False

    def generate_convex_hull_and_simplify(self, target_triangles=500):
        """
        Simplify a convex hull built from the given vertices using Open3D.
        """
        points_np = np.array([v.to_tuple() for v in self.vertices])
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_np)

        hull, _ = pcd.compute_convex_hull()
        simplified = hull.simplify_quadric_decimation(target_number_of_triangles=target_triangles)
        self.vertices = [Vector3(*p) for p in np.asarray(simplified.vertices)]

    def get_world_vertices(self):
        return [
            rotate_vector_old(v, self.obj.position, self.obj.rotation) + self.obj.position
            for v in self.vertices
        ]

    def extract_triangle_edges(self, vertices):
        edges = set()
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                a, b, c = vertices[i:i + 3]
                edges.update([
                    (a, b),
                    (b, c),
                    (c, a),
                ])
        return edges

    def get_axes(self, verts_a_world, verts_b_world):
        axes = set()

        def extract_normals(vertices):
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    a, b, c = vertices[i:i + 3]
                    normal = (b - a).cross(c - a).normalized()
                    if normal.magnitude() > 1e-6:
                        axes.add(normal.to_tuple())

        # Face normals
        extract_normals(verts_a_world)
        extract_normals(verts_b_world)

        # Edge cross products
        edges_a = self.extract_triangle_edges(verts_a_world)
        edges_b = self.extract_triangle_edges(verts_b_world)

        for ea in edges_a:
            dir_a = (ea[1] - ea[0]).normalized()
            for eb in edges_b:
                dir_b = (eb[1] - eb[0]).normalized()
                cross = dir_a.cross(dir_b)
                if cross.magnitude() > 1e-6:
                    axes.add(cross.normalized().to_tuple())

        return list(axes)

    def project(self, vertices, axis):
        axis = Vector3(*axis) if isinstance(axis, tuple) else axis
        dots = [v.dot(axis) for v in vertices]
        return min(dots), max(dots)

    def check_collision(self, other):
        other_collider = getattr(other, 'collider', other)
        if other_collider is None:
            return None

        verts_a_world = self.get_world_vertices()
        verts_b_world = other_collider.get_world_vertices()

        axes = self.get_axes(verts_a_world, verts_b_world)

        smallest_overlap = float('inf')
        collision_axis = None

        for axis in axes:
            proj1 = self.project(verts_a_world, axis)
            proj2 = self.project(verts_b_world, axis)

            if proj1[1] < proj2[0] or proj2[1] < proj1[0]:
                return None  # Separating axis found

            overlap = min(proj1[1], proj2[1]) - max(proj1[0], proj2[0])
            if overlap < smallest_overlap:
                smallest_overlap = overlap
                collision_axis = axis

        # Compute collision normal and contact point
        normal = Vector3(*collision_axis)
        center_a = sum(verts_a_world, Vector3(0, 0, 0)) * (1 / len(verts_a_world))
        center_b = sum(verts_b_world, Vector3(0, 0, 0)) * (1 / len(verts_b_world))

        if (center_a - center_b).dot(normal) < 0:
            normal = normal * -1

        contact_point = (center_a + center_b) * 0.5
        return contact_point, normal, smallest_overlap

    def attach(self, owner_object):
        self.size = owner_object.size
        self.obj = owner_object
        self.vertices = owner_object.mesh.vertices
        self.generate_convex_hull_and_simplify()
        return "collider"
