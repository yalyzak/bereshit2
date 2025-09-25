import math
import copy
import trimesh
import moderngl

from bereshit.Vector3 import Vector3


class MeshRander:
    def __deepcopy__(self, memo):
        obj_copy = type(self)(
            triangles=copy.deepcopy(self.triangles, memo),
            vertices=copy.deepcopy(self.vertices, memo),
            edges=copy.deepcopy(self.edges, memo),
            shape=copy.deepcopy(self.shape, memo),
            # ctx= moderngl.create_standalone_context()
        )
        memo[id(self)] = obj_copy

        return obj_copy

    def attach(self, owner_object):
        return "Mesh"

    def __init__(self, vertices=None, edges=None, shape=None, triangles=None, obj_path=None):
        self.shape = shape
        self.colors = None
        self.ctx = moderngl.create_standalone_context()
        if obj_path:
            self.vertices, self.triangles, self.edges, self.colors, self.vertex_shader, self.fragment_shader = self.load_model(
                obj_path)

            # Compile program
            self.prog = self.ctx.program(
                vertex_shader=self.vertex_shader,
                fragment_shader=self.fragment_shader,
            )

        elif shape and vertices is None and edges is None:
            generator = self.get_generator_function(shape)
            if generator:
                result = generator()
                if len(result) == 2:  # Only vertices and edges
                    self.vertices, self.edges = result
                    self.triangles = None  # No triangle data available
                elif len(result) == 3:  # Vertices, edges, triangles
                    self.vertices, self.edges, self.triangles = result
                else:
                    raise ValueError("Shape generator must return (vertices, edges) or (vertices, edges, triangles)")
            else:
                raise ValueError(f"No generator found for shape: {shape}")

        elif vertices is not None and edges is not None and triangles is not None:
            self.vertices = vertices
            self.edges = edges
            self.triangles = triangles

        else:
            raise ValueError("Must provide either a shape, .obj path, or both vertices and edges")

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

    @staticmethod
    def load_model(path):
        mesh = trimesh.load(path, force='mesh')

        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError("Loaded file is not a mesh")

        # Convert vertices
        # vertices = [Vector3(*v) for v in mesh.vertices]
        # Convert and center vertices
        vertices = [Vector3(*v) for v in mesh.vertices]
        centroid = sum(vertices, Vector3()) * (1.0 / len(vertices))
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
            diffuse = mesh.visual.material.diffuse
            if diffuse is not None:
                colors = [tuple(diffuse)] * len(vertices)
            else:
                colors = [(1.0, 1.0, 1.0)] * len(vertices)  # default white
        else:
            colors = [(1.0, 1.0, 1.0)] * len(vertices)  # default white

        # Vertex Shader
        vertex_shader = """
      #version 330

      in vec3 in_position;
      in vec3 in_color;

      uniform mat4 model;
      uniform mat4 view;
      uniform mat4 projection;

      out vec3 v_color;

      void main() {
          gl_Position = projection * view * model * vec4(in_position, 1.0);
          v_color = in_color;
      }
      """

        # Fragment Shader
        fragment_shader = """
      #version 330

      in vec3 v_color;
      out vec4 fragColor;

      void main() {
          fragColor = vec4(v_color, 1.0);
      }
      """

        return vertices, triangles, edges, colors, vertex_shader, fragment_shader

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
        # centroid = sum(cube_vertices, Vector3()) * (1.0 / len(cube_vertices))
        # cube_vertices = [v - centroid for v in cube_vertices]
        return cube_vertices, cube_edges, cube_triangles

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
