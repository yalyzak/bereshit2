#version 330
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
in vec3 in_position;
void main() {
  gl_Position = projection * view * model * vec4(in_position, 1.0);
}