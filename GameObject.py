import copy

from bereshit import Material, MeshRander
from bereshit.bereshitCore import GameObject


class GameObject(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Keeps original Python component objects alive
        self._components = {}
        self._py_components = []


        self.add_component(Material.Material())
        self.add_component(MeshRander.MeshRander(shape="box"))

    def add_component(self, *components):
        for component in components:
            self._add_component(component)
        return self

    def _add_component(self, component):
        name= None
        if "attach" in type(component).__dict__:
            name = component.attach(self)
        super().add_component(component)

        # Save by component name, for cam.Camera
        if not name:
            self._components[component.__class__.__name__] = component
            if component.is_python_component():
                self._py_components.append(component)
        else:
            self._components[name] = component
            if component.is_python_component():
                self._py_components.append(component)

        return self

    def __getattr__(self, name):
        if "_components" in self.__dict__:
            if name in self._components:
                return self._components[name]

        raise AttributeError(name)

    def __deepcopy__(self, memo):
        # Return the existing copy when this object was already visited.
        if id(self) in memo:
            return memo[id(self)]

        obj = GameObject(
            self.transform.position,
            self.transform.rotation,
            self.transform.size,
            [],
            self.name
        )

        # Register the copy BEFORE recursively copying components or children.
        memo[id(self)] = obj

        for component in self._components.values():
            component_copy = copy.copy(component)

            if component_copy is not None:
                obj.add_component(component_copy)

        for child in self.children:
            child_copy = copy.deepcopy(child, memo)
            obj.add_child(child_copy)

        return obj