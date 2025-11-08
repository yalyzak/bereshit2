# --- Preload moderngl_window submodules (fix for Nuitka onefile) ---
import importlib
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
for name in [
    "moderngl_window.resources",
    "moderngl_window.resources.programs",
    "moderngl_window.resources.textures",
    "moderngl_window.resources.scenes",
]:
    try:
        if name not in sys.modules:
            importlib.import_module(name)
    except Exception as e:
        print(f"Warning preloading {name}:", e)


# --- Disable automatic resource registration if no "scene" folder exists ---
import os
from pathlib import Path

scene_path = Path(__file__).parent / "scene"
if not scene_path.exists():
    # Override the register_dir function to a harmless dummy
    import moderngl_window.resources
    moderngl_window.resources.register_dir = lambda *a, **k: None
    print("[Info] Disabled moderngl_window resource registration (no scene folder).")
# -------------------------------------------------------------------
import moderngl_window
import moderngl
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
        self.wnd.exit_key = None
        self.root_object = BereshitRenderer.root_object  # 👈 assign it here
        self.camera_obj = self.root_object.search_by_component('Camera')

        if not self.camera_obj:
            raise Exception("No camera object found")
        self.cam = self.camera_obj.Camera
        self.cam.render = self
        self.Initialize[0] = True
        self.fov = self.cam.FOV
        self.viewer_distance = self.cam.VIEWER_DISTANCE
        self.ortho_projection = Matrix44.orthogonal_projection(
            0, self.wnd.size[0], 0, self.wnd.size[1], -1.0, 1.0
        )
        self.ui_vbo = self.ctx.buffer(reserve=20 * 6 * 64)  # ~64 quads
        self.bullshit = ""
        self.text_elements = []
        self.text_prog = self.ctx.program(
            vertex_shader=open("bereshit/shaders/text_vertex_shader.vert").read(),
            fragment_shader=open("bereshit/shaders/text_fragment_shader.vert").read())
        # === 4. Quad for drawing ===
        vertices = np.array([
            -1.0, -1.0, 0.0, 1.0,  # bottom-left
            1.0, -1.0, 1.0, 1.0,  # bottom-right
            -1.0, 1.0, 0.0, 0.0,  # top-left
            1.0, 1.0, 1.0, 0.0,  # top-right
        ], dtype='f4')

        self.text_vbo = self.ctx.buffer(vertices.tobytes())
        self.text_vbo = self.ctx.vertex_array(
            self.text_prog,
            [(self.text_vbo, '2f 2f', 'in_vert', 'in_tex')]
        )
        # Simple UI shader
        self.ui_prog = self.ctx.program(
            vertex_shader=open("bereshit/shaders/ui_prog.vert").read(),
            fragment_shader=open("bereshit/shaders/ui_fragment_shader.vert").read())
        self.ui_vao = self.ctx.vertex_array(
            self.ui_prog,
            [(self.ui_vbo, "2f 3f", "in_position", "in_color")]
        )

        # Store UI elements to draw
        self.ui_elements = []
        self.wire_prog = self.ctx.program(
            vertex_shader=open("bereshit/shaders/wire_vertex_shader.vert").read(),
            fragment_shader=open("bereshit/shaders/wire_fragment_shader.vert").read())
        self.solid_prog = self.ctx.program(
            vertex_shader=open("bereshit/shaders/solid_vertex_shader.vert").read(),
            fragment_shader=open("bereshit/shaders/solid_fragment_shader.vert").read())
        self.view = Matrix44.identity()
        self.projection = Matrix44.perspective_projection(self.fov, self.wnd.aspect_ratio, 0.1, 1000.0)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (
            moderngl.SRC_ALPHA,
            moderngl.ONE_MINUS_SRC_ALPHA,
        )
        self.keys_down = set()
        self.keys_up = set()
        self.keys = list()


        self.meshes = []
        self.prepare_meshes()

    def GetKeyDown(self):
        keys = self.wnd.keys
        string = ""
        for key in self.keys_down:

            key_name = None
            for name, value in vars(keys).items():
                if value == key:
                    key_name = name
                    break

            # Fallback to printing the raw key code
            if key_name is None:
                key_name = f"Unknown({key})"

            string += key_name
        self.keys_down = set()
        return string

    def GetKey(self):
        keys = self.wnd.keys
        string = ""
        for key in self.keys:
            key_name = None
            for name, value in vars(keys).items():
                if value == key:
                    key_name = name
                    break

            # Fallback to printing the raw key code
            if key_name is None:
                key_name = f"Unknown({key})"

            string += key_name
        self.keys = list()
        return string
    def on_key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        self.keys.append(key)

        # Key pressed (only trigger once)
        if action == keys.ACTION_PRESS and key not in self.keys_down:
            self.keys_down.add(key)
        # Key released (remove from pressed set)
        elif action == keys.ACTION_RELEASE and key in self.keys_down:
            self.keys_down.remove(key)

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
                        self.wire_prog,
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
                        self.solid_prog,
                        [(vao_buffer, "3f", "in_position")]  # only position
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
                        self.wire_prog,
                        [(vao, '3f', 'in_position')],
                    ),
                    'len': len(lines),
                })
        if shading == "solid":
            for obj in missing:
                if obj.Mesh is None:
                    continue

                # Convert vertices to numpy (scaled and centered)
                verts = [(v * obj.size * 0.25).to_np() for v in obj.Mesh.vertices]

                # Build triangle vertex list
                triangles = []
                if obj.Mesh.triangles:
                    for tri in obj.Mesh.triangles:  # tri = (i, j, k)
                        for index in tri:
                            triangles.extend(verts[index])  # flatten x, y, z into list

                    vbo = np.array(triangles, dtype='f4')
                    vao_buffer = self.ctx.buffer(vbo.tobytes())
                    vao = self.ctx.vertex_array(
                        self.solid_prog,
                        [(vao_buffer, "3f", "in_position")]  # only position
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

    def render_text(self):
        if not self.text_elements:
            return
        self.texture.use()
        self.text_vbo.render(moderngl.TRIANGLE_STRIP)
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


    def render_text(self):

        # === 1. Create text image using Pillow ===
        img = Image.new("RGBA", self.window_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for text in self.text_elements:
            font_size = int(64 * text.scale)
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            draw.text((text.center), text.text, font=font, fill=(255, 255, 255, 255))

        text_data = np.array(img).astype('u1')

        # === 2. Upload to OpenGL as a texture ===
        self.texture = self.ctx.texture(self.window_size, 4, text_data.tobytes())
        self.texture.use()




    def add_text_rect(self,text):
        self.text_elements.append(text)
    def add_ui_rect(self, x, y, w, h, color=(1.0, 1.0, 1.0)):
        r, g, b = color
        hw, hh = w / 2, h / 2
        vertices = np.array([
            x - hw, y - hh, r, g, b,
            x + hw, y - hh, r, g, b,
            x + hw, y + hh, r, g, b,

            x - hw, y - hh, r, g, b,
            x + hw, y + hh, r, g, b,
            x - hw, y + hh, r, g, b,
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
            if shading == "wire":
                item['vao'].render(mode=moderngl.LINES, vertices=item['len'])
                self.wire_prog['model'].write(model.astype('f4').tobytes())
                self.wire_prog['view'].write(self.view.astype('f4').tobytes())
                self.wire_prog['projection'].write(self.projection.astype('f4').tobytes())
                # self.prog['lightPos'].value = cam_pos  # your light source coordinates

                color = obj.material.color if hasattr(obj.material, 'color') else (1.0, 1.0, 1.0)
                self.wire_prog['color'].value = color
            elif shading == "solid":
                # Enable depth test
                self.ctx.enable(moderngl.DEPTH_TEST)

                # Set uniforms before drawing
                self.solid_prog['model'].write(model.astype('f4').tobytes())
                self.solid_prog['view'].write(self.view.astype('f4').tobytes())
                self.solid_prog['projection'].write(self.projection.astype('f4').tobytes())

                self.solid_prog['light_pos'].value = cam_pos

                self.solid_prog['light_color'].value = (1.0, 1.0, 1.0)
                color = obj.material.color if hasattr(obj.material, 'color') else (1.0, 1.0, 1.0)
                self.solid_prog['object_color'].value = color
                self.solid_prog['view_pos'].value = tuple(cam_pos)

                # Render as filled triangles
                item['vao'].render(mode=moderngl.TRIANGLES, vertices=item['len'])
        # Desired rectangle size
        rect_width = 400
        rect_height = 300

        # Center position
        x = (self.window_size[0] - rect_width) / 2
        y = (self.window_size[1] - rect_height) / 2
        # self.add_ui_rect(x, y, rect_width, rect_height, color=(1.0, 0.0, 0.0))

        # --- Render UI on top ---
        self.render_text()
        self.render_ui()
        self.text_vbo.render(moderngl.TRIANGLE_STRIP)


def run_renderer(root_object, Initialize):
    BereshitRenderer.Initialize = Initialize
    BereshitRenderer.root_object = root_object  # 👈 inject your object here
    moderngl_window.run_window_config(BereshitRenderer, args=['--window', 'glfw'])




class Text:
    def __init__(self, text="", center =(0.0, 0.0), size=(512, 128), scale=1.0):
        self.text = text
        self.center = center
        self.size = size
        self.scale = scale


