#version 330

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

in vec3 in_position;
in vec3 in_normal;

out vec3 frag_pos;
out vec3 normal;

void main() {
    // Transform vertex to world space
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_pos = world_pos.xyz;

    // Transform normal correctly (ignore translation)
    mat3 normal_matrix = transpose(inverse(mat3(model)));
    normal = normalize(normal_matrix * in_normal);

    // Final clip-space position
    gl_Position = projection * view * world_pos;
}
