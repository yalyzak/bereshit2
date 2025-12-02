#version 330

in vec2 in_position;
in vec4 in_color;     // <-- NOW includes r, g, b, a

uniform mat4 ortho;

out vec4 v_color;     // output full color + alpha

void main() {
    gl_Position = ortho * vec4(in_position, 0.0, 1.0);
    v_color = in_color;
}
