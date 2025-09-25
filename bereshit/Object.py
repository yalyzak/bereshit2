import copy
import math
import traceback

import numpy as np

from bereshit.Material import Material
from bereshit.MeshRander import MeshRander
from bereshit.Quaternion import Quaternion
from bereshit.Vector3 import Vector3

class Position(Vector3): pass

class LocalPosition(Vector3): pass


class CenterOfGravity(Vector3): pass


class Rotation(Vector3): pass

class LocalRotation(Vector3): pass

class Size(Vector3):
    def __init__(self, x=1, y=1, z=1):
        super().__init__(x, y, z)

class Object:

    def _compute_quaternion(self):
        roll = math.radians(self.rotation.x)
        pitch = math.radians(self.rotation.y)
        yaw = math.radians(self.rotation.z)

        c1 = math.cos(yaw / 2)
        s1 = math.sin(yaw / 2)
        c2 = math.cos(pitch / 2)
        s2 = math.sin(pitch / 2)
        c3 = math.cos(roll / 2)
        s3 = math.sin(roll / 2)

        w = c1 * c2 * c3 + s1 * s2 * s3
        x = c1 * c2 * s3 - s1 * s2 * c3
        y = c1 * s2 * c3 + s1 * c2 * s3
        z = s1 * c2 * c3 - c1 * s2 * s3

        return Quaternion(x, y, z, w)

    @property
    def local_position(self):
        if self.parent is None:
            return copy.copy(self.position)

        # Step 1: Offset vector from parent to this object
        offset = self.position - self.parent.position

        # Step 2: Rotate offset into local space (undo parent rotation)
        inverse_quaternion = -self.parent.rotation
        local_offset = rotate_vector_old(offset, Vector3(0, 0, 0), inverse_quaternion)

        return local_offset

    @local_position.setter
    def local_position(self, new_local_position):
        if self.parent is None:
            self.position = copy.copy(new_local_position)
        else:
            # Step 1: Rotate local position to world space using parent's rotation
            rotated_offset = rotate_vector_old(new_local_position, Vector3(0, 0, 0), self.parent.rotation)

            # Step 2: Translate by parent position
            self.position = self.parent.position + rotated_offset

    def __copy__(self):
        return Object(self.value)

    def __deepcopy__(self, memo):
        obj_copy = type(self)(
            position=copy.deepcopy(self.position, memo),
            rotation=copy.deepcopy(self.rotation, memo),
            size=copy.deepcopy(self.size, memo),
            children=copy.deepcopy(self.children, memo),
            components=copy.deepcopy(self.components, memo),
            name=copy.deepcopy(self.name, memo),

        )
        memo[id(self)] = obj_copy

        obj_copy.__default_position = copy.deepcopy(self.__default_position, memo)

        # Fix parent for children
        obj_copy.components = {}
        for name, comp in self.components.items():
            comp_copy = copy.deepcopy(comp, memo)
            if hasattr(comp_copy, 'obj'):
                comp_copy.obj = obj_copy
            obj_copy.components[name] = comp_copy
            if hasattr(comp_copy, 'parent'):
                comp_copy.parent = obj_copy
        # Fix component references
        # for comp in obj_copy.components.values():

        #     if hasattr(comp, 'obj'):
        #         comp.obj = obj_copy

        return obj_copy

    def add_child(self, new_child):
        if new_child.parent == None:
            new_child.parent = self
        new_child.world = self
        for i, child in enumerate(self.children):
            if child.name == new_child.name:
                self.children[i] = new_child

                # render.prepare_mesh_for_object(new_child)
                break
        else:
            # render.prepare_mesh_for_object(new_child)
            self.children.append(new_child)

    def add_component(self, component, name=None):
        if name is None:
            name = component.__class__.__name__
            if hasattr(component, "attach"):
                result = component.attach(self)
                if result is not None:
                    name = result
        else:
            if hasattr(component, "attach"):
                component.attach(self)  # call it, but ignore the result

        self.components[name] = component
        component.parent = self  # optional back-reference
        if hasattr(component, 'start') and component.start is not None:
            component.start()
        return self

    def __init__(self, position=None, rotation=None, size=None, children=None, components=None,
                 name=""):
        self.parent = None
        self.children = children or []
        self.name = name
        self.size = Size(*size) if isinstance(size, tuple) else size or Size()
        self.components = components or {}
        self.local_rotation = LocalRotation()

        for child in self.children:
            if isinstance(child, Object):
                child.parent = self
        self.position = Position(*position) if isinstance(position, tuple) else position or Position()

        self.__default_position = copy.copy(self.position)
        # self.__default_position = Vector3(0,0,0)

        self.rotation = Rotation(*rotation) if isinstance(rotation, tuple) else rotation or Rotation()
        self.world = None

        # self.quaternion = self._compute_quaternion()

        self.quaternion = Quaternion.euler(self.rotation)
        self._rotation_dirty = False
        self.add_component(Material())
        self.add_component(MeshRander(shape="box"))

        def findWorld(child):
            parent = child.parent
            if parent is None:
                return child

            return findWorld(parent)

        for child in self.get_all_children():
            child.world = findWorld(child)

    def search(self, target_name):
        if hasattr(self, 'name') and self.name == target_name:
            return self
        if hasattr(self, 'children'):
            for child in self.children:
                result = child.search(target_name)  # ✅ fix here
                if result:
                    return result
        return None

    def search_by_component(self, component_name):
        # Check if this object has the desired component
        if hasattr(self, "components") and component_name in self.components:
            return self
        # Recursively check children
        if hasattr(self, "children"):
            for child in self.children:
                result = child.search_by_component(component_name)
                if result:
                    return result
        return None

    def remove_component(self, name):
        if name in self.components:
            del self.components[name]

    def get_component(self, name):
        return self.components.get(name, None)

    def __getattr__(self, name):
        # Allow normal attribute access
        if hasattr(type(self), name):
            return object.__getattribute__(self, name)
        # Only called if normal attribute lookup fails
        component = self.components.get(name)
        if component is not None:
            return component
        raise AttributeError(f"'{self.name}' object has no attribute or component '{name}'")



    def rotate_around_axis(self, axis, angle_rad):
        """
        Rotates the object around a given axis by angle_rad (in radians).
        """
        axis = axis.normalized()

        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        ux, uy, uz = axis.x, axis.y, axis.z

        # Rodrigues' rotation formula
        R = np.array([
            [cos_a + ux ** 2 * (1 - cos_a), ux * uy * (1 - cos_a) - uz * sin_a, ux * uz * (1 - cos_a) + uy * sin_a],
            [uy * ux * (1 - cos_a) + uz * sin_a, cos_a + uy ** 2 * (1 - cos_a), uy * uz * (1 - cos_a) - ux * sin_a],
            [uz * ux * (1 - cos_a) - uy * sin_a, uz * uy * (1 - cos_a) + ux * sin_a, cos_a + uz ** 2 * (1 - cos_a)]
        ])

        if not hasattr(self, 'rotation_matrix'):
            self.rotation_matrix = np.eye(3)

        self.rotation_matrix = R @ self.rotation_matrix

    def get_all_colliders(self):
        all_bereshit = []
        collider = self.get_component("collider")
        if collider:
            all_bereshit.append(self)
        for child in self.get_all_children():
            all_bereshit.extend(child.get_all_colliders())
        return all_bereshit







    def set_rotation(self, new_world_rot: Vector3):
        """
        Explicitly set this object's world‐space rotation to `new_world_rot`.
        Also recompute `local_rotation` so that:
            local_rotation = new_world_rot - parent.rotation
        (or = new_world_rot if there's no parent).
        """
        # 1. Assign the new world rotation
        self.rotation = Vector3(new_world_rot.x, new_world_rot.y, new_world_rot.z)
        self._rotation_dirty = True
        # 2. Compute and store the local offset from parent
        if self.parent is not None:
            self.local_rotation = Vector3(
                self.rotation.x - self.parent.rotation.x,
                self.rotation.y - self.parent.rotation.y,
                self.rotation.z - self.parent.rotation.z
            )
        else:
            # No parent means local == world
            self.local_rotation = Vector3(self.rotation.x,
                                          self.rotation.y,
                                          self.rotation.z)

    def add_rotation(self, delta: Vector3, forall=False):
        """
        Add an incremental rotation `delta` (world‐space Euler angles)
        on top of the current world rotation. Then update local_rotation.
        """
        # 1. Compute the new world rotation by simple vector addition
        new_world_rot = Vector3(
            self.rotation.x + delta.x,
            self.rotation.y + delta.y,
            self.rotation.z + delta.z
        )

        # 2. Delegate to set_rotation to keep local_rotation in sync
        self.set_rotation(new_world_rot)
        if forall:
            self._set_rotation_recursive(delta)
            self.set_projection(delta)

    def add_rotation_old(self, rotation):
        self.set_rotation(self.rotation + rotation)

    def set_projection(self, pivot=np.array([0, 0, 0])):
        for child in self.children:
            target = child
            vector = target.position
            # if np.allclose(pivot, [0, 0, 0]):
            pivot = target.parent.position
            angles = target.parent.local_rotation
            rotated = rotate_vector_old(vector, pivot, angles)
            # target.set_position(Vector3(*rotated))
            target.position = Vector3(*rotated)
            target.set_projection(pivot=pivot)

    def find_center_of_gravity(self):
        bereshit = self.get_all_children()
        positions = [obj.position.to_tuple() for obj in bereshit]
        masses = [obj.Rigidbody.mass for obj in bereshit]
        x_cog, y_cog, z_cog = calculate_center_of_gravity_3d(positions, masses)
        print(f"Center of Gravity: ({x_cog:.2f}, {y_cog:.2f}, {z_cog:.2f})")

    def getdefault_position(self):
        return self.__default_position

    def set_default_position(self):
        self.__default_position = copy.copy(self.position)
        for child in self.children:
            child.set_default_position()

    def reset_to_default(self):
        self.position = copy.copy(self.__default_position)
        if self.get_component("Rigidbody") is not None:
            self.Rigidbody.acceleration = Vector3(0, 0, 0)
            self.Rigidbody.velocity = Vector3(0, 0, 0)

        for child in self.children:
            child.reset_to_default()

    def rotate_point(self):
        for child in self.children:
            child.rotate_point()

    def get_children_bereshit(self):
        return [child.obj for child in self.children]

    def get_all_children(self):
        all_objs = []
        for child in self.children:
            target = child
            all_objs.append(target)
            all_objs.extend(target.get_all_children())
        return all_objs

    def get_all_children_physics(self):
        all_objs = []
        for child in self.children:
            rb = child.get_component("Rigidbody")
            collider = child.get_component("collider")
            if rb and collider:
                all_objs.append(child)
            all_objs.extend(child.get_all_children_physics())
        return all_objs

    def get_all_children_not_physics(self):
        all_objs = []
        for child in self.children:
            rb = child.get_component("Rigidbody")
            # collider = child.get_component("collider")
            if not rb:
                all_objs.append(child)
            all_objs.extend(child.get_all_children_physics())
        return all_objs

    def __repr__(self):
        children_repr = ",\n    ".join(repr(child) for child in self.children)
        return (f"{self.name}(\n"
                f"  Position={self.position},\n"
                f"  Rotation={self.rotation},\n"
                f"  Size={self.size},\n"
                f"  children=[\n    {children_repr}\n  ]\n"
                f")")
