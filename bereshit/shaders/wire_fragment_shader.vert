#version 330
out vec4 f_color;
uniform vec3 color;
void main() {
  f_color = vec4(color, 1.0);
}