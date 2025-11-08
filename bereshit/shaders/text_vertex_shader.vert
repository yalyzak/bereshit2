#version 330
in vec2 in_vert;
in vec2 in_tex;
out vec2 v_tex;

void main() {
    v_tex = in_tex;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
