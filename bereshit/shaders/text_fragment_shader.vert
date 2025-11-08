#version 330
uniform sampler2D Texture;
in vec2 v_tex;
out vec4 fragColor;

void main() {
    fragColor = texture(Texture, v_tex);
}
