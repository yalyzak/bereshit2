
from bereshit import Material, MeshRander
from bereshit.bereshitCore import GameObject



class GameObject(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Keeps original Python component objects alive
        self._py_components = {}


        self.add_component(Material.Material())
        self.add_component(MeshRander.MeshRander(shape="box"))


    def add_component(self, component):

        component.attach(self)
        super().add_component(component)

        # Save by component name, for cam.Camera
        if component.name != 'Component':
            self._py_components[component.name] = component
        else:
            self._py_components[component.__class__.__name__] = component


        return self

    def __getattr__(self, name):
        if "_py_components" in self.__dict__:
            if name in self._py_components:
                return self._py_components[name]

        raise AttributeError(name)