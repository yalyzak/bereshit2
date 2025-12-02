#version 330
in vec4 v_color;       // one input: r,g,b,a
out vec4 fragColor;

void main() {
    fragColor = v_color;
}
