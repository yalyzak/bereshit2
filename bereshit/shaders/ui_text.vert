#version 330

in vec2 in_pos;
in vec2 in_uv;

out vec2 v_uv;

uniform vec2 screen_size;

void main() {
    // Convert from pixel coords → NDC (-1..1)
    vec2 pos = in_pos / screen_size * 2.0 - 1.0;
    pos.y = -pos.y; // flip Y (so top-left is 0,0)
    gl_Position = vec4(pos, 0.0, 1.0);
    v_uv = in_uv;
}
