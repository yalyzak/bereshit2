# --- Preload moderngl_window submodules (fix for Nuitka onefile) ---
import importlib
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque
from importlib.resources import files

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
import moderngl_window.context.glfw
import bereshit.shaders


class BereshitRenderer(moderngl_window.WindowConfig):
    gl_version = (3, 3)
    title = "Bereshit moderngl Renderer"
    window_size = (1920, 1080)
    aspect_ratio = None
    resizable = True
    resource_dir = '.'
    root_object = None  # 👈 class variable to inject data

    def load_texture(self, path):
        folder = Path(sys.argv[0]).resolve().parent
        img = Image.open(folder / path).convert("RGBA")
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        texture = self.ctx.texture(img.size, 4, img.tobytes())
        texture.build_mipmaps()

        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.repeat_x = True
        texture.repeat_y = True

        return texture

    def image_to_texture(self, image):
        img = image.convert("RGBA")
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        texture = self.ctx.texture(img.size, 4, img.tobytes())
        texture.build_mipmaps()

        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.repeat_x = True
        texture.repeat_y = True

        return texture

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wnd.exit_key = None
        self.width, self.height = self.wnd.size
        self.root_object = BereshitRenderer.root_object
        cameras = self.root_object.search_by_component('Camera')
        if len(cameras) > 0:
            self.camera_obj = cameras[0]

        if not self.camera_obj:
            raise Exception("No camera object found")
        self.cam = self.camera_obj.Camera
        self.cam.render = self

        self.text_input = -1
        self._mouse_input = 0

        self.mouse_pos = (0,0)

        self.typing = False

        self.fov = self.cam.FOV
        self.viewer_distance = self.cam.VIEWER_DISTANCE
        self.ortho_projection = Matrix44.orthogonal_projection(
            0, self.wnd.size[0], 0, self.wnd.size[1], -1.0, 1.0
        )
        self.ui_vbo = self.ctx.buffer(reserve=20 * 6 * 64)  # ~64 quads
        self.bullshit = ""
        self.text_elements = []
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.text_prog = self.ctx.program(
            vertex_shader=(
                    files("bereshit")
                    / "shaders"
                    / "text_vertex_shader.vert"
            ).read_text(),
            fragment_shader=(
                    files("bereshit")
                    / "shaders"
                    / "text_fragment_shader.vert"
            ).read_text(),
            )
        # === 4. Quad for drawing ===
        vertices = np.array([
            -1.0, -1.0, 0.0, 1.0,  # bottom-left
            1.0, -1.0, 1.0, 1.0,  # bottom-right
            -1.0, 1.0, 0.0, 0.0,  # top-left
            1.0, 1.0, 1.0, 0.0,  # top-right
        ], dtype='f4')

        self.text_vbo = self.ctx.buffer(vertices.tobytes())

        self.text_vao = self.ctx.vertex_array(
            self.text_prog,
            [(self.text_vbo, '2f 2f', 'in_vert', 'in_tex')]
        )
        # Simple UI shader
        self.ui_prog = self.ctx.program(
            vertex_shader=(
                    files("bereshit")
                    / "shaders"
                    / "ui_vertex_shader.vert"
            ).read_text(),
            fragment_shader=(
                    files("bereshit")
                    / "shaders"
                    / "ui_fragment_shader.vert"
            ).read_text(),)
        self.ui_vao = self.ctx.vertex_array(
            self.ui_prog,
            [
                (self.ui_vbo, "2f 2f 4f", "in_pos", "in_uv", "in_color"),
            ],
        )

        # Store UI elements to draw
        self.ui_elements = []
        self.wire_prog = self.ctx.program(
            vertex_shader=(
                    files("bereshit")
                    / "shaders"
                    / "wire_vertex_shader.vert"
            ).read_text(),
            fragment_shader=(
                    files("bereshit")
                    / "shaders"
                    / "wire_fragment_shader.vert"
            ).read_text(),
        )
        self.solid_prog = self.ctx.program(
            vertex_shader=(
                    files("bereshit")
                    / "shaders"
                    / "solid_vertex_shader.vert"
            ).read_text(),
            fragment_shader=(
                    files("bereshit")
                    / "shaders"
                    / "solid_fragment_shader.vert"
            ).read_text(),)

        self.material_prog = self.ctx.program(
            vertex_shader=(
                    files("bereshit")
                    / "shaders"
                    / "material_preview_vertex_shader.vert"
            ).read_text(),
            fragment_shader=(
                    files("bereshit")
                    / "shaders"
                    / "material_preview_fragment_shader.vert"
            ).read_text(), )
        # self.material_prog["texture1"] = 0
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

        self.texture = self.ctx.texture(self.window_size, 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.default_texture = self.load_texture((str(files("bereshit")) + "\\shaders" + "\\default_texture.jpg"))
        self.font_cache = {}
        self.Initialize[0] = True # must be at the end

    def hide_cursor(self):
        self.wnd.cursor = False

    def show_cursor(self):
        self.wnd.cursor = True

    def wire_shading(self, objs):
        for obj in objs:

            if obj.Mesh is None or obj.Mesh.vertices() == []:
                continue

            # Convert vertices to numpy
            # verts = [(v * obj.size * 0.5).to_np() for v in
            #          obj.Mesh.vertices]  # Ensure this returns list or np.array of floats
            verts = [v.to_np() for v in obj.Mesh.vertices()]  # no size, no 0.5

            lines = []
            for i, j in obj.Mesh.edges():
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

    def solid_shading(self, objs):
        for obj in objs:
            if obj.Mesh is None:
                continue

            # Convert vertices to numpy (scaled and centered)
            verts = [v.to_np() for v in obj.Mesh.vertices()]

            # Build triangle vertex list
            triangles = []
            if obj.Mesh.triangles():
                for tri in obj.Mesh.triangles():  # tri = (i, j, k)
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
                    'len': len(triangles) // 3,
                })

    def material_preview_shading(self, objs):
        for obj in objs:
            if obj.Mesh is None:
                continue

            verts = [v.to_np() for v in obj.Mesh.vertices()]
            uvs = obj.Mesh.uvs()
            uvs = uvs if uvs is not None and len(uvs) > 0 else []

            vertex_data = []
            if obj.Mesh.triangles() is not None:
                for tri in obj.Mesh.triangles():
                    for index in tri:

                        # position
                        vertex_data += list(verts[index])

                        # # normal (temporary placeholder)
                        # vertex_data += [0.0, 0.0, 1.0]

                        # uv
                        if len(uvs) > 0:
                            vertex_data += list(uvs[index])
                        else:
                            x, y, z = verts[index]
                            vertex_data += [x * 0.5 + 0.5, y * 0.5 + 0.5]

                vbo = np.array(vertex_data, dtype='f4')
                vao_buffer = self.ctx.buffer(vbo.tobytes())

                vao = self.ctx.vertex_array(
                    self.material_prog,
                    [(vao_buffer, "3f 2f", "in_position", "in_texcoord")]
                )

                self.meshes.append({
                    'obj': obj,
                    'vbo': vao_buffer,
                    'vao': vao,
                    'len': len(vertex_data) // 5,
                })

    def render_mesh(self, item, shading, cam_pos):
        obj = item['obj']
        pos = obj.transform.position.to_np()
        size = obj.transform.size.to_np()
        rot = obj.transform.quaternion

        model = (
                Matrix44.from_scale(size * 0.5)
                @ Matrix44.from_quaternion(PyrrQuat([rot.x, rot.y, rot.z, rot.w]))
                @ Matrix44.from_translation(pos)
        )
        if shading == "wire":
            self.wire_rendering(item, model, obj)
        elif shading == "solid":
            self.solid_rendering(item, model, obj, cam_pos)
        elif shading == "material preview":
            self.material_preview_rendering(item, model, obj, cam_pos)

    def wire_rendering(self, item, model, obj):
        item['vao'].render(mode=moderngl.LINES, vertices=item['len'])
        self.wire_prog['model'].write(model.astype('f4').tobytes())
        self.wire_prog['view'].write(self.view.astype('f4').tobytes())
        self.wire_prog['projection'].write(self.projection.astype('f4').tobytes())
        # self.prog['lightPos'].value = cam_pos  # your light source coordinates

        color = obj.material.color if hasattr(obj.material, 'color') else (1.0, 1.0, 1.0)
        self.wire_prog['color'].value = color

    def solid_rendering(self, item, model, obj, cam_pos):
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

    def material_preview_rendering(self, item, model, obj, cam_pos):
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Set matrices
        self.material_prog['model'].write(model.astype('f4').tobytes())
        self.material_prog['view'].write(self.view.astype('f4').tobytes())
        self.material_prog['projection'].write(self.projection.astype('f4').tobytes())

        # Lighting uniforms
        # self.material_prog['light_pos'].value = tuple(cam_pos)
        # self.material_prog['light_color'].value = (1.0, 1.0, 1.0)
        # self.material_prog['view_pos'].value = tuple(cam_pos)

        # Bind texture
        texture = obj.Mesh.texture()

        if texture:
            if not hasattr(obj.Mesh, "gpu_texture"):
                obj.Mesh.gpu_texture = self.image_to_texture(texture)

            obj.Mesh.gpu_texture.use(location=0)
        else:
            self.default_texture.use(location=0)
        # Draw mesh
        item['vao'].render(mode=moderngl.TRIANGLES, vertices=item['len'])

    def prepare_meshes(self):
        shading = self.cam.shading
        objs = self.root_object.get_all_children()
        if shading == "wire":
            self.wire_shading(objs)
        elif shading == "solid":
            self.solid_shading(objs)
        elif shading == "material preview":
            self.material_preview_shading(objs)

    def prepare_missing_meshes(self, missing):
        shading = self.cam.shading
        if shading == "wire":
            self.wire_shading(missing)
        elif shading == "solid":
            self.solid_shading(missing)
        elif shading == "material preview":
            self.material_preview_shading(missing)

    def cleanup_removed_meshes(self, removed_objs):
        self.meshes = [m for m in self.meshes if m['obj'] not in removed_objs]

    def resize(self, width: int, height: int):
        self.width, self.height = width, height
        self.projection = Matrix44.perspective_projection(self.fov, self.wnd.aspect_ratio, 0.1, 1000.0)
        self.ortho_projection = Matrix44.orthogonal_projection(0, width, 0, height, -1.0, 1.0)

    def render_ui(self):
        if not self.ui_elements and not self.text_elements:
            return

        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        render_items = []
        render_items.extend(self.ui_elements)
        render_items.extend(self.text_elements)

        render_items.sort(key=lambda e: e.layer)

        for item in render_items:
            if isinstance(item, Box):
                self._render_ui_element(item)
            else:
                self._render_text_element(item)

        self.ctx.enable(moderngl.DEPTH_TEST)

    def flush_ui(self):
        self.ui_elements = []
        self.text_elements = []

    def _render_ui_element(self, element):
        vertices = element.vertices().astype("f4")

        self.ui_vbo.orphan(vertices.nbytes)
        self.ui_vbo.write(vertices)

        self.ui_prog["ortho"].write(self.ortho_projection.astype("f4").tobytes())
        if element.texture:
            element.texture.use(0)
            self.ui_prog["use_texture"].value = 1

        else:
            if element.texture_path:
                element.texture = self.load_texture(element.texture_path)
                element.texture.use(0)
                self.ui_prog["use_texture"].value = 1
            else:
                self.ui_prog["use_texture"].value = 0

        self.ui_prog["tex"].value = 0

        vertex_count = vertices.size // 8  # example if vertex = x,y,u,v,r,g,b,a
        self.ui_vao.render(mode=moderngl.TRIANGLES, vertices=vertex_count)


    def get_font(self, size):
        if size not in self.font_cache:
            self.font_cache[size] = ImageFont.truetype(
                "C:/Windows/Fonts/arial.ttf", size
            )
        return self.font_cache[size]

    def _render_text_element(self, text):
        img = Image.new("RGBA", self.window_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        font_size = int(64 * text.scale)
        font = self.get_font(font_size)

        draw.text(
            text.center,
            text.text,
            font=font,
            fill=text.color + (int(255 * text.opacity),),
            anchor="mm"
        )

        text_data = np.array(img).astype('u1')

        self.texture.write(text_data.tobytes())
        self.texture.use(location=0)
        self.text_vao.render(moderngl.TRIANGLE_STRIP)

    def add_text_rect(self, text):
        self.text_elements.append(text)

    def add_ui_rect(self, box):
        self.ui_elements.append(box)

    def rendering_setup(self):
        # if self.camera_obj.World.RunningFlag[0]:
        #     self.wnd.close()

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

        cam_pos = self.camera_obj.transform.position.to_np()
        cam_rot = self.camera_obj.transform.quaternion
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
            PyrrVector3(cam_pos),
            PyrrVector3(target.tolist()),
            PyrrVector3(up.tolist())  # or [0,1,0] if not rotated
        )
        return cam_pos, target, up, shading

    def on_render(self, time: float, frametime: float):
        cam_pos, target, up, shading = self.rendering_setup()
        for item in self.meshes:
            self.render_mesh(item, shading, cam_pos)

        # --- Render UI on top ---
        ### memory leak on the ui
        render_items= []
        render_items.extend(self.ui_elements)
        render_items.extend(self.text_elements)
        render_items.sort(key=lambda e: e.layer)
        if len(render_items) > 100:
            raise Exception("too many itmes to render")
        self.render_ui()

        # self.render_text()
        # self.render_elements()
        # self.text_vbo.render(moderngl.TRIANGLE_STRIP)
        ### memory leak on the ui

    def on_key_event(self, key, action, modifiers):
        if action != 0:
            self.text_input = key


    def on_mouse_press_event(self, x, y, button):
        # 1=left, 2=middle, 3=right (usually)
        self._mouse_input = True
        self.mouse_pos = (x, y)

    def on_mouse_release_event(self, x, y, button):
        # 1=left, 2=middle, 3=right (usually)
        self._mouse_input = False
        self.mouse_pos = (x, y)
    def get_mouse_input(self):
        return self._mouse_input

def run_renderer(root_object, Initialize, Exit):
    BereshitRenderer.Initialize = Initialize
    BereshitRenderer.Exit = Exit
    BereshitRenderer.root_object = root_object  # 👈 inject your object here
    moderngl_window.run_window_config(BereshitRenderer, args=['--window', 'glfw'])



class Text:
    def __init__(self, text="", center=(0.0, 0.0), size=(512, 128), scale=1.0, color=(255, 255, 255), opacity=1,
                 container=None, layer=0):
        self.container = container
        self.text = text
        self.center = center
        self.size = size
        self.scale = scale
        self.color = color
        self.opacity = opacity
        self.layer = layer


class Box:
    def __init__(self, center=(960, 540), size=(100, 100), scale=1.0, color=(255, 255, 255), opacity=1, layer=0, texture=None,container=None,
                 children=None , clickable=False):
        self.container = container
        self.children = children
        self.center = (center[0], 1080 - center[1])
        self.size = size
        self.scale = scale
        self.color = (color[0] / 255, color[1] / 255, color[2] / 255)
        self.opacity = opacity
        self.layer = layer
        if texture:
            self.texture_path = texture
        else:
            self.texture_path = None
        self.texture = None

    def click(self, position):
        # the collider is not right is the window is not full screen, should resize for the real screen size
        return (
                self.center[0] - self.size[0] / 2 <= position[0] <= self.center[0] + self.size[0] / 2 and
                -self.center[1] + 1080 - self.size[1] / 2 <= position[1] <= -self.center[1] + 1080 + self.size[1] / 2
        )

    def vertices(self):
        hw, hh = self.size[0] / 2, self.size[1] / 2
        x, y = self.center

        r, g, b = self.color
        a = self.opacity  # <-- add opacity

        vertices = np.array([
            # x, y, u, v, r, g, b, a
            x - hw, y - hh, 0.0, 0.0, r, g, b, a,
            x + hw, y - hh, 1.0, 0.0, r, g, b, a,
            x + hw, y + hh, 1.0, 1.0, r, g, b, a,

            x - hw, y - hh, 0.0, 0.0, r, g, b, a,
            x + hw, y + hh, 1.0, 1.0, r, g, b, a,
            x - hw, y + hh, 0.0, 1.0, r, g, b, a,
        ], dtype="f4")

        return vertices
