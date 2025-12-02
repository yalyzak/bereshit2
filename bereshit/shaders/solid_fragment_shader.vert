#version 330

in vec3 frag_pos;
in vec3 normal;

uniform vec3 light_pos;
uniform vec3 light_color;
uniform vec3 object_color;
uniform vec3 view_pos;

out vec4 frag_color;

void main()
{
    // Normalize directions
    vec3 norm = normalize(normal);
    vec3 light_dir = normalize(light_pos - frag_pos);

    // --- Distance attenuation ---
    float distance = length(light_pos - frag_pos);
    // Quadratic attenuation model:  1 / (a + b*d + c*d^2)
    float constant  = 1.0;    // minimum light strength
    float linear    = 0.01;   // small linear falloff
    float quadratic = 0.001;  // faster quadratic falloff
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));

    // --- Ambient term ---
    float ambient_strength = 0.6;
    vec3 ambient = ambient_strength * light_color;

    // --- Diffuse term ---
    float diff = max(dot(norm, light_dir), 0.0);
    vec3 diffuse = diff * light_color;

    // --- Specular term ---
    float specular_strength = 0.5;
    vec3 view_dir = normalize(view_pos - frag_pos);
    vec3 reflect_dir = reflect(-light_dir, norm);
    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32);
    vec3 specular = specular_strength * spec * light_color;

    // --- Combine lighting and apply attenuation ---
    vec3 lighting = (ambient + diffuse + specular) * attenuation;

    frag_color = vec4(lighting * object_color, 1.0);
}
