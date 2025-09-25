import moderngl
import moderngl_window
from moderngl_window import geometry
from pyrr import Vector4, Vector3 as PyrrVector3, Quaternion as PyrrQuat, Matrix44
import numpy as np






class BereshitRenderer(moderngl_window.WindowConfig):
    gl_version = (3, 3)
    title = "Bereshit moderngl Renderer"
    window_size = (1920, 1080)
    aspect_ratio = None
    resizable = True
    resource_dir = '.'
    root_object = None  # 👈 class variable to inject data

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_object = BereshitRenderer.root_object  # 👈 assign it here
        self.camera_obj = self.root_object.search_by_component('Camera')
        if not self.camera_obj:
            raise Exception("No camera object found")

        self.cam = self.camera_obj.Camera
        self.fov = self.cam.FOV
        self.viewer_distance = self.cam.VIEWER_DISTANCE
        self.ortho_projection = Matrix44.orthogonal_projection(
            0, self.wnd.size[0], 0, self.wnd.size[1], -1.0, 1.0
        )
        self.ui_vbo = self.ctx.buffer(reserve=20 * 6 * 64)  # ~64 quads

        # Simple UI shader
        self.ui_prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_position;
                in vec3 in_color;
                uniform mat4 ortho;
                out vec3 v_color;
                void main() {
                    gl_Position = ortho * vec4(in_position, 0.0, 1.0);
                    v_color = in_color;
                }
            """,
            fragment_shader="""
                #version 330
                in vec3 v_color;
                out vec4 fragColor;
                void main() {
                    fragColor = vec4(v_color, 1.0);
                }
            """
        )
        self.ui_vao = self.ctx.vertex_array(
            self.ui_prog,
            [(self.ui_vbo, "2f 3f", "in_position", "in_color")]
        )


        # Store UI elements to draw
        self.ui_elements = []
        self.prog = self.ctx.program(
            vertex_shader='''
                      #version 330
                      uniform mat4 model;
                      uniform mat4 view;
                      uniform mat4 projection;
                      in vec3 in_position;
                      void main() {
                          gl_Position = projection * view * model * vec4(in_position, 1.0);
                      }
                      ''',
            fragment_shader='''
                      #version 330
                      out vec4 f_color;
                      uniform vec3 color;
                      void main() {
                          f_color = vec4(color, 1.0);
                      }
                      '''

        )

        self.view = Matrix44.identity()
        self.projection = Matrix44.perspective_projection(self.fov, self.wnd.aspect_ratio, 0.1, 1000.0)

        self.meshes = []
        self.prepare_meshes()

    def prepare_meshes(self):
        shading = self.cam.shading
        if shading == "wire":
            for obj in self.root_object.get_all_children():

                if obj.Mesh is None or obj.Mesh.vertices == []:
                    continue

                # Convert vertices to numpy
                # verts = [(v * obj.size * 0.5).to_np() for v in
                #          obj.Mesh.vertices]  # Ensure this returns list or np.array of floats
                verts = [v.to_np() for v in obj.Mesh.vertices]  # no size, no 0.5

                lines = []
                for i, j in obj.Mesh.edges:
                    lines.extend(verts[i])  # 👈 flatten the vector into x, y, z
                    lines.extend(verts[j])

                vbo = np.array(lines, dtype='f4')
                vao = self.ctx.buffer(vbo.tobytes())
                self.meshes.append({
                    'obj': obj,
                    'vbo': vao,
                    'vao': self.ctx.vertex_array(
                        self.prog,
                        [(vao, '3f', 'in_position')],
                    ),
                    'len': len(lines),
                })
        if shading == "solid":
            for obj in self.root_object.get_all_children():
                if obj.Mesh is None:
                    continue

                # Convert vertices to numpy (scaled and centered)
                verts = [(v * obj.size * 0.5).to_np() for v in obj.Mesh.vertices]

                # Build triangle vertex list
                triangles = []
                if obj.Mesh.triangles:
                    for tri in obj.Mesh.triangles:  # tri = (i, j, k)
                        for index in tri:
                            triangles.extend(verts[index])  # flatten x, y, z into list

                    vbo = np.array(triangles, dtype='f4')
                    vao_buffer = self.ctx.buffer(vbo.tobytes())
                    vao = self.ctx.vertex_array(
                        self.prog,
                        [(vao_buffer, "3f", "aPos")]  # only position
                    )

                    self.meshes.append({
                        'obj': obj,
                        'vbo': vao_buffer,
                        'vao': vao,
                        'len': len(triangles),
                    })

    def prepare_missing_meshes(self,missing):
        shading = self.cam.shading
        if shading == "wire":
            for obj in missing:
                if obj.Mesh is None or obj.Mesh.vertices == []:
                    continue

                # Convert vertices to numpy
                # verts = [(v * obj.size * 0.5).to_np() for v in
                #          obj.Mesh.vertices]  # Ensure this returns list or np.array of floats
                verts = [v.to_np() for v in obj.Mesh.vertices]  # no size, no 0.5

                lines = []
                for i, j in obj.Mesh.edges:
                    lines.extend(verts[i])  # 👈 flatten the vector into x, y, z
                    lines.extend(verts[j])

                vbo = np.array(lines, dtype='f4')
                vao = self.ctx.buffer(vbo.tobytes())
                self.meshes.append({
                    'obj': obj,
                    'vbo': vao,
                    'vao': self.ctx.vertex_array(
                        self.prog,
                        [(vao, '3f', 'in_position')],
                    ),
                    'len': len(lines),
                })
        if shading == "solid":
            for obj in missing:
                if obj.Mesh is None:
                    continue

                # Convert vertices to numpy (scaled and centered)
                verts = [(v * obj.size * 0.5).to_np() for v in obj.Mesh.vertices]

                # Build triangle vertex list
                triangles = []
                if obj.Mesh.triangles:
                    for tri in obj.Mesh.triangles:  # tri = (i, j, k)
                        for index in tri:
                            triangles.extend(verts[index])  # flatten x, y, z into list

                    vbo = np.array(triangles, dtype='f4')
                    vao_buffer = self.ctx.buffer(vbo.tobytes())
                    vao = self.ctx.vertex_array(
                        self.prog,
                        [(vao_buffer, "3f", "aPos")]  # only position
                    )

                    self.meshes.append({
                        'obj': obj,
                        'vbo': vao_buffer,
                        'vao': vao,
                        'len': len(triangles),
                    })

    def cleanup_removed_meshes(self, removed_objs):
        self.meshes = [m for m in self.meshes if m['obj'] not in removed_objs]

    def resize(self, width: int, height: int):
        self.projection = Matrix44.perspective_projection(self.fov, self.wnd.aspect_ratio, 0.1, 1000.0)
        self.ortho_projection = Matrix44.orthogonal_projection(0, width, 0, height, -1.0, 1.0)

    def render_ui(self):
        if not self.ui_elements:
            return
        self.ctx.disable(moderngl.DEPTH_TEST)
        # self.ctx.disable(moderngl.CULL_FACE)  # if you enabled it elsewhere
        self.ctx.enable(moderngl.BLEND)

        all_vertices = np.concatenate(self.ui_elements).astype('f4', copy=False)
        self.ui_vbo.orphan(all_vertices.nbytes)
        self.ui_vbo.write(all_vertices)

        self.ui_prog["ortho"].write(self.ortho_projection.astype("f4").tobytes())

        vertex_count = all_vertices.size // 5
        self.ui_vao.render(mode=moderngl.TRIANGLES, vertices=vertex_count)

        self.ui_elements.clear()
        self.ctx.enable(moderngl.DEPTH_TEST)

    def add_ui_rect(self, x, y, w, h, color=(1.0, 1.0, 1.0)):
        r, g, b = color
        # Triangle-based quad
        vertices = np.array([
            x, y, r, g, b,
            x + w, y, r, g, b,
            x + w, y + h, r, g, b,

            x, y, r, g, b,
            x + w, y + h, r, g, b,
            x, y + h, r, g, b,
        ], dtype="f4")
        self.ui_elements.append(vertices)

    def on_render(self, time: float, frametime: float):
        # collect all scene objects (root + children)
        scene_objs = self.root_object.get_all_children()

        # ignore the camera (and any other special objs)
        skip_objs = {self.camera_obj}
        scene_objs = [obj for obj in scene_objs if obj not in skip_objs]

        # objects we already have meshes for
        existing_objs = [m['obj'] for m in self.meshes]

        # objects missing a mesh
        missing = [obj for obj in scene_objs if obj not in existing_objs]

        # objects no longer in the scene
        removed = [obj for obj in existing_objs if obj not in scene_objs]

        # prepare meshes for new ones
        if missing:
            self.prepare_missing_meshes(missing)

        # cleanup old meshes
        if removed:
            self.cleanup_removed_meshes(removed)  # you'd implement this

        shading = self.cam.shading

        self.ctx.clear(0.0, 0.0, 0.0)



        cam_pos = self.camera_obj.position.to_np()
        cam_rot = self.camera_obj.quaternion
        # Rotate forward vector (0, 0, 1) using the rotation matrix
        pyrr_q = PyrrQuat([cam_rot.x, cam_rot.y, cam_rot.z, cam_rot.w])
        rot_matrix = Matrix44.from_quaternion(pyrr_q)

        forward_vec4 = np.array([0.0, 0.0, 1.0, 0.0])  # direction vector (w=0)
        rotated_forward = rot_matrix @ forward_vec4
        forward = rotated_forward[:3]

        target = cam_pos + forward

        up_vec4 = np.array([0.0, 1.0, 0.0, 0.0])
        rotated_up = rot_matrix @ up_vec4
        up = rotated_up[:3]

        self.view = Matrix44.look_at(
            PyrrVector3(cam_pos.tolist()),
            PyrrVector3(target.tolist()),
            PyrrVector3(up.tolist())  # or [0,1,0] if not rotated
        )

        for item in self.meshes:
            obj = item['obj']
            pos = obj.position.to_np()
            size = obj.size.to_np()
            rot = obj.quaternion

            # Use object's rotation
            pyrr_obj_q = PyrrQuat([rot.x, rot.y, rot.z, rot.w])
            # obj_rot_matrix = Matrix44.from_quaternion(pyrr_obj_q)

            model = (
                    Matrix44.from_scale(size*0.5)
                    @ Matrix44.from_quaternion(PyrrQuat([rot.x, rot.y, rot.z, rot.w]))
                    @ Matrix44.from_translation(pos)
            )
            # @ Matrix44.from_scale(size)
            self.prog['model'].write(model.astype('f4').tobytes())
            self.prog['view'].write(self.view.astype('f4').tobytes())
            self.prog['projection'].write(self.projection.astype('f4').tobytes())
            # self.prog['lightPos'].value = cam_pos  # your light source coordinates

            color = obj.material.color if hasattr(obj.material, 'color') else (1.0, 1.0, 1.0)
            self.prog['color'].value = color
            if shading == "wire":
                item['vao'].render(mode=moderngl.LINES, vertices=item['len'])
            elif shading == "solid":
                item['vao'].render(mode=moderngl.TRIANGLES, vertices=item['len'] // 3)
                # Big red box (covering most of the screen)
        # Desired rectangle size
        rect_width = 400
        rect_height = 300

        # Center position
        x = (self.window_size[0] - rect_width) / 2
        y = (self.window_size[1] - rect_height) / 2
        # self.add_ui_rect(x, y, rect_width, rect_height, color=(1.0, 0.0, 0.0))

        # --- Render UI on top ---
        self.render_ui()

def run_renderer(root_object):
    BereshitRenderer.root_object = root_object  # 👈 inject your object here
    moderngl_window.run_window_config(BereshitRenderer, args=['--window', 'glfw'])