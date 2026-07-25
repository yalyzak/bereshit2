import math
import copy

import numpy as np
import trimesh
from PIL import Image

from bereshit.bereshitCore import Vector3
from bereshit import Component


class MeshRander(Component):
    def __deepcopy__(self, memo):

        cls = type(self)

        # 1. Create empty object
        obj_copy = cls.__new__(cls)

        # 2. Register immediately (CRITICAL)
        memo[id(self)] = obj_copy

        # 3. Now it's safe to deepcopy
        obj_copy._triangles = copy.deepcopy(self._triangles, memo)
        obj_copy._vertices = copy.deepcopy(self._vertices, memo)
        obj_copy._edges = copy.deepcopy(self._edges, memo)
        obj_copy._uv = copy.deepcopy(self._uv, memo)
        obj_copy._TextureImage = copy.deepcopy(self._TextureImage, memo)


        # obj_copy.shape = copy.deepcopy(self.shape, memo)

        return obj_copy
    def vertices(self):
        return self._vertices

    def triangles(self):
        return self._triangles

    def edges(self):
        return self._edges

    def uvs(self):
        return self._uv

    def texture(self):
        return self._TextureImage

    def attach(self, owner_object):
        mesh = owner_object.get_component("Mesh")  # will remove duplicate renders by default
        if mesh:
            owner_object.remove_component("Mesh")

        if self._obj_path:
            self._vertices, self._triangles, self._edges, self._colors = self.load_model()

        elif self._shape and self._vertices is None and self._edges is None:
            generator = self.get_generator_function(self._shape)
            if generator:
                result = generator()
                if len(result) == 2:  # Only vertices and edges
                    self._vertices, self._edges = result
                    self._triangles = None  # No triangle data available
                elif len(result) == 3:  # Vertices, edges, triangles
                    self._vertices, self._edges, self._triangles = result
                elif len(result) == 4:  # Vertices, edges, triangles
                    self._vertices, self._edges, self._triangles, self._faces = result
                else:
                    raise ValueError("Shape generator must return (vertices, edges) or (vertices, edges, triangles)")
            else:
                raise ValueError(f"No generator found for shape: {self._shape}")

        elif self._vertices is not None and self._edges is not None and self._triangles is not None:
            self._vertices = self._vertices
            self._edges = self._edges
            self._triangles = self._triangles

        else:
            raise ValueError("Must provide either a shape, .obj path, or both vertices and edges")
        if self._repeat_texture:
            if self._shape == "box":
                self.build_uv_cube()

    def __init__(self, vertices=None, edges=None, shape=None, triangles=None, faces=None, obj_path=None, size=None, texture=None, repeat_texture=False):
        super().__init__()
        self.name = "Mesh"
        self._shape = shape
        self.colors = None
        if texture:
            self._TextureImage = Image.open(texture)
        else:
            self._TextureImage = None
        self._repeat_texture = repeat_texture
        self._uv = []
        if size:
            self._size = size.to_np()
        else:
            self._size = np.ones(3)
        self._vertices = vertices
        self._edges = edges
        self._triangles = triangles
        self._faces = faces
        self._obj_path = obj_path

    def get_generator_function(self, shape_name):
        generators = {
            "box": self.generate_cube,
            "ellipsoid": self.generate_ellipsoid,
            "cone": self.generate_cone,
            "cylinder": self.generate_cylinder,
            "pyramid": self.generate_pyramid,
            "triangular_prism": self.generate_triangular_prism,
            "empty": self.generate_empty

        }
        return generators.get(shape_name)

    # @staticmethod
    def load_model(self):
        mesh = trimesh.load(self._obj_path, force='mesh')

        # mesh_size = mesh.scale
        if mesh.visual.defined:
            TextureImage = mesh.visual.material.baseColorTexture
            self._TextureImage = TextureImage
            self._uv = mesh.visual.uv
        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError("Loaded file is not a mesh")

        # Convert vertices
        # vertices = [Vector3(*v) for v in mesh.vertices]
        # Convert and center vertices
        vertices = [Vector3(*v) for v in mesh.vertices * self._size ]
        centroid = Vector3(0,0,0)
        vertices = [v - centroid for v in vertices]

        # Convert faces to triangles (used for solid rendering)
        triangles = [tuple(face) for face in mesh.faces]

        # Convert faces to edges (used for wireframe rendering)
        edge_set = set()
        for face in mesh.faces:
            for i in range(3):
                a = face[i]
                b = face[(i + 1) % 3]
                edge_set.add(tuple(sorted((a, b))))
        edges = list(edge_set)

        # Load vertex colors if available
        if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
            raw_colors = mesh.visual.vertex_colors[:, :3]
            colors = [tuple(c / 255.0) for c in raw_colors]
        elif hasattr(mesh.visual, 'material') and mesh.visual.material is not None:
            try:
                diffuse = mesh.visual.material.diffuse
                if diffuse is not None:
                    colors = [tuple(diffuse)] * len(vertices)
                else:
                    colors = [(1.0, 1.0, 1.0)] * len(vertices)  # default white
            except:
                colors = [(1.0, 1.0, 1.0)] * len(vertices)  # default white
        else:
            colors = [(1.0, 1.0, 1.0)] * len(vertices)  # default white



        return vertices, triangles, edges, colors

    def build_uv_cube(self):
        old_vertices = self._vertices[:]  # original 8 vertices

        self._vertices = []
        self._uv = []
        self._triangles = []

        # full texture per face
        uv_face = [
            (0.0, 0.0),  # bottom-left
            (1.0, 0.0),  # bottom-right
            (1.0, 1.0),  # top-right
            (0.0, 1.0),  # top-left
        ]

        for face in self._faces:
            i0, i1, i2, i3 = face

            # duplicate vertices for this face
            v0 = old_vertices[i0]
            v1 = old_vertices[i1]
            v2 = old_vertices[i2]
            v3 = old_vertices[i3]

            start = len(self._vertices)

            self._vertices += [v0, v1, v2, v3]
            self._uv += uv_face

            # build 2 triangles
            self._triangles += [
                (start + 0, start + 1, start + 2),
                (start + 0, start + 2, start + 3),
            ]

    @staticmethod
    def generate_cube():
        cube_vertices = [
            Vector3(-1, -1, -1), Vector3(1, -1, -1),
            Vector3(1, 1, -1), Vector3(-1, 1, -1),
            Vector3(-1, -1, 1), Vector3(1, -1, 1),
            Vector3(1, 1, 1), Vector3(-1, 1, 1),
        ]

        cube_edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        # triangles (for rendering)
        cube_triangles = [
            # back (-Z)
            (0, 1, 2), (0, 2, 3),
            # front (+Z)
            (4, 6, 5), (4, 7, 6),
            # left (-X)
            (0, 3, 7), (0, 7, 4),
            # right (+X)
            (1, 5, 6), (1, 6, 2),
            # bottom (-Y)
            (0, 4, 5), (0, 5, 1),
            # top (+Y)
            (3, 2, 6), (3, 6, 7),
        ]

        # NEW: faces (quads, perfect for UV mapping)
        cube_faces = [
            (0, 1, 2, 3),  # back
            (4, 5, 6, 7),  # front
            (0, 3, 7, 4),  # left
            (1, 5, 6, 2),  # right
            (0, 4, 5, 1),  # bottom
            (3, 2, 6, 7),  # top
        ]

        return cube_vertices, cube_edges, cube_triangles, cube_faces

    @staticmethod
    def generate_ellipsoid(rx=1, ry=1, rz=1, segments=12, rings=6):
        vertices = []
        edges = []

        for i in range(rings + 1):
            phi = math.pi * i / rings
            for j in range(segments):
                theta = 2 * math.pi * j / segments
                x = rx * math.sin(phi) * math.cos(theta)
                y = ry * math.cos(phi)
                z = rz * math.sin(phi) * math.sin(theta)
                vertices.append(Vector3(x, y, z))

        for i in range(rings):
            for j in range(segments):
                current = i * segments + j
                next_seg = current + 1 if (j + 1) < segments else i * segments
                next_ring = current + segments
                edges.append((current, next_seg))
                if i < rings:
                    edges.append((current, next_ring))
        return vertices, edges

    @staticmethod
    def generate_cone(radius=1, height=2, segments=12):
        vertices = [Vector3(0, height / 2, 0)]  # Tip of cone
        base_center = Vector3(0, -height / 2, 0)
        base_indices = []

        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            vertices.append(Vector3(x, -height / 2, z))
            base_indices.append(i + 1)

        edges = [(0, i) for i in base_indices]  # Sides to tip
        for i in range(segments):
            edges.append((base_indices[i], base_indices[(i + 1) % segments]))  # Base circle
        return vertices, edges

    @staticmethod
    def generate_pyramid(base_size=2, height=2):
        half = base_size / 2
        vertices = [
            Vector3(-half, 0, -half),  # 0 base
            Vector3(half, 0, -half),  # 1
            Vector3(half, 0, half),  # 2
            Vector3(-half, 0, half),  # 3
            Vector3(0, height, 0)  # 4 tip
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # base
            (0, 4), (1, 4), (2, 4), (3, 4)  # sides
        ]
        return vertices, edges

    @staticmethod
    def generate_cylinder(radius=1, height=2, segments=16):
        vertices = []
        edges = []

        # Generate bottom and top circle vertices
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            vertices.append(Vector3(x, -height / 2, z))  # Bottom circle
            vertices.append(Vector3(x, height / 2, z))  # Top circle

        for i in range(segments):
            bottom = i * 2
            top = bottom + 1
            next_bottom = (bottom + 2) % (2 * segments)
            next_top = (top + 2) % (2 * segments)

            # Vertical edge
            edges.append((bottom, top))

            # Bottom circle edge
            edges.append((bottom, next_bottom))

            # Top circle edge
            edges.append((top, next_top))

        return vertices, edges

    @staticmethod
    def generate_triangular_prism(base=1, height=1, depth=2):
        h = math.sqrt(3) * base / 2
        vertices = [
            Vector3(-base / 2, -h / 3, -depth / 2),  # bottom front triangle
            Vector3(base / 2, -h / 3, -depth / 2),
            Vector3(0, 2 * h / 3, -depth / 2),
            Vector3(-base / 2, -h / 3, depth / 2),  # back triangle
            Vector3(base / 2, -h / 3, depth / 2),
            Vector3(0, 2 * h / 3, depth / 2)
        ]
        edges = [
            (0, 1), (1, 2), (2, 0),  # front
            (3, 4), (4, 5), (5, 3),  # back
            (0, 3), (1, 4), (2, 5)  # connecting edges
        ]
        return vertices, edges

    @staticmethod
    def generate_empty():
        cube_vertices = []
        cube_edges = []
        return cube_vertices, cube_edges

