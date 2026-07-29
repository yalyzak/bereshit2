from bereshit.bereshitCore import Component

class Component(Component):
    def __copy__(self):
        cls = type(self)
        result = cls.__new__(cls)
        Component.__init__(result)
        result.__dict__.update(self.__dict__)
        return result