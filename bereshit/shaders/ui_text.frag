#version 330

in vec2 v_uv;
out vec4 f_color;

uniform sampler2D tex;
uniform vec4 color;

void main() {
    vec4 t = texture(tex, v_uv);
    f_color = t * color;
}
