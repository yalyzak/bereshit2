 #version 330
in vec2 in_position;
in vec3 in_color;
uniform mat4 ortho;
out vec3 v_color;
void main() {
    gl_Position = ortho * vec4(in_position, 0.0, 1.0);
    v_color = in_color;
}