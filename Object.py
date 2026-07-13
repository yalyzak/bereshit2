import copy
import math
import traceback

import numpy as np
from bereshit.bereshitCore import World
from bereshit.Material import Material
from bereshit.MeshRander import MeshRander
from bereshit.Quaternion import Quaternion
from bereshit.Vector3 import Vector3
from bereshit.Cache import Cache


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
        local_offset = self.parent.quaternion.rotate(offset)

        return local_offset

    @property
    def local_rotation(self):
        if self.parent is None:
            return copy.copy(self.rotation)

        return (self.parent.quaternion.inverse() * self.quaternion).to_euler()

    @local_rotation.setter
    def local_rotation(self, new_local_rotation):
        old_world_rot = self.quaternion

        local_quat = Quaternion.euler(new_local_rotation)

        if self.parent is None:
            self.quaternion = local_quat
        else:
            self.quaternion = self.parent.quaternion * local_quat

        rotation_delta = self.quaternion * old_world_rot.inverse()

        for child in self.children:
            offset = child.position - self.position
            child.position = self.position + rotation_delta.rotate(offset)

            # rotate child's orientation too
            child.quaternion = rotation_delta * child.quaternion

            child.Cache.set_dirty()

        self.Cache.set_dirty()

    @local_position.setter
    def local_position(self, new_local_position):
        old_world_position = copy.copy(self.position)

        if self.parent is None:
            self.position = copy.copy(new_local_position)
            self.Cache.set_dirty()
        else:
            # Convert local position to world position
            world_offset = self.parent.quaternion.rotate(new_local_position)
            self.position = self.parent.position + world_offset
            self.Cache.set_dirty()

        # World-space movement delta
        world_delta = self.position - old_world_position

        joint = self.get_component("Joint")
        if joint:
            joint.cast_anchor()

        # Update children LOCAL positions instead of world positions
        for child in self.children:
            local_delta = child.parent.quaternion.inverse().rotate(world_delta)
            child.local_position += local_delta

    def set_default_quaternion(self):
        self.__default_quaternion = copy.deepcopy(self.quaternion)

    def set_default_position(self):
        self.__default_position = copy.deepcopy(self.position)

    def set_default(self):
        self.set_default_quaternion()
        self.set_default_position()

    def __copy__(self):
        return Object(self.value)

    def __deepcopy__(self, memo):
        cls = type(self)

        # 1. Create empty shell
        obj_copy = cls.__new__(cls)
        obj_copy.parent = None
        # 2. Register EARLY (prevents recursion & preserves identity)
        memo[id(self)] = obj_copy

        # 3. Copy simple attributes
        obj_copy.position = copy.deepcopy(self.position, memo)
        obj_copy.rotation = copy.deepcopy(self.rotation, memo)
        obj_copy.quaternion = copy.deepcopy(self.quaternion, memo)
        obj_copy.size = copy.deepcopy(self.size, memo)
        obj_copy.name = copy.deepcopy(self.name, memo)
        obj_copy.__default_position = copy.deepcopy(self.__default_position, memo)
        obj_copy.__default_quaternion = copy.deepcopy(self.__default_quaternion, memo)
        obj_copy.Cache = copy.deepcopy(self.Cache, memo)

        # 4. Copy children (MANUALLY to control parent)
        obj_copy.children = []
        for child in self.children:
            child_copy = copy.deepcopy(child, memo)

            # Force parent assignment (no hasattr)
            child_copy.parent = obj_copy

            obj_copy.children.append(child_copy)
        # obj_copy.local_position = copy.deepcopy(self.local_position, memo)

        # 5. Copy components (carefully fix back-references)
        obj_copy.components = {}
        for name, comp in self.components.items():
            comp_copy = copy.deepcopy(comp, memo)

            if hasattr(comp_copy, 'obj'):
                comp_copy.obj = obj_copy
            if hasattr(comp_copy, 'parent'):
                comp_copy.parent = obj_copy

            obj_copy.components[name] = comp_copy

        return obj_copy

    def add_child(self, new_child):
        if new_child.parent == None:
            new_child.parent = self
        new_child.World = self

        for i, child in enumerate(self.children):
            if child.name == new_child.name:
                raise Exception("fuck you i did not program this yat"
                                "to solve this name the object with a unique name")
        else:
            self.children.append(new_child)
            # World.Objects.append(new_child)

    def _remove_child(self, child):
        if child in self.children:
            self.children.remove(child)

    def destroy(self):
        if self.parent:
            self.parent._remove_child(self)
        # if self.World:
        #     self.World._remove_object(self)
        del self

    def add_component(self, *components):
        for component in components:
            if isinstance(component, list) or isinstance(component, tuple):
                for c in component:
                    self.add_component(c)  # recursive flatten
            else:
                # --- single component ---
                name = component.__class__.__name__
                if hasattr(component, "attach"):
                    result = component.attach(self)
                    if result is not None:
                        name = result
                else:
                    if hasattr(component, "attach"):
                        component.attach(self)  # ignore result
                if self.components.get(name):
                    i = 0
                    while self.components.get(name):
                        name = f"{name}_{i}"
                        i += 1
                self.components[name] = component
                component.parent = self  # optional back-reference
                component.Active = True

                if hasattr(component, 'start') and component.start is not None:
                    component.start()

        return self

    def __init__(self, position=None, rotation=None, size=None, quaternion=None, children=None, components=None,
                 name=""):
        self.parent = None
        self.children = children or []
        self.name = name
        self.size = Size(*size) if isinstance(size, tuple) else size or Size()
        self.components = {}

        for child in self.children:
            if isinstance(child, Object):
                child.parent = self
        self.position = Position(*position) if isinstance(position, tuple) else position or Position()

        self.__default_position = copy.copy(self.position)

        self.rotation = Rotation(*rotation) if isinstance(rotation, tuple) else rotation or Rotation()

        self.__default_rotation = copy.copy(self.rotation)

        self.world = None

        self.quaternion = Quaternion.euler(self.rotation) if not quaternion else quaternion

        self.__default_quaternion = copy.copy(self.quaternion)

        self.up = self.quaternion.rotate(Vector3(0, 1, 0))
        self.forward = self.quaternion.rotate(Vector3(0, 0, 1))

        self.add_component(Material())
        self.add_component(MeshRander(shape="box"))

        self.Cache = Cache()

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
        results = []

        # Check current object
        if hasattr(self, "components") and component_name in self.components:
            results.append(self)

        # Recursively check children
        if hasattr(self, "children"):
            for child in self.children:
                results.extend(child.search_by_component(component_name))

        return results

    def search_by_name(self, object_name):
        results = []

        # Check current object
        if self.name == object_name:
            results.append(self)

        # Recursively check children
        for child in self.children:
            results.extend(child.search_by_name(object_name))

        return results

    def remove_component(self, name):
        if name in self.components:
            del self.components[name]

    def get_component(self, name):
        if isinstance(name, str):
            return self.components.get(name)
        else:
            # name is a class
            for c in self.components.values():
                if isinstance(c, name):
                    return c
        return None

    def get_all_components(self, name):
        components = []
        if isinstance(name, str):
            components.append(self.components.get(name))
        else:
            # name is a class
            for c in self.components.values():
                if isinstance(c, name):
                    components.append(c)
        return components

    def __getattr__(self, name):
        component = self.components.get(name)
        if component is not None:
            return component
        raise AttributeError(
            f"'{self.name}' object has no attribute or component '{name}'"
        )

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

    def add_rotation(self, delta):
        self.quaternion *= delta
        for child in self.children:
            child.set_projection(delta, self.position)

    def add_rotation_old(self, rotation):
        self.set_rotation(self.rotation + rotation)

    def set_projection(self, delta, position):
        self.position = delta.rotate(self.position - position) + position
        self.quaternion *= delta

    @property
    def default_position(self):
        return self.__default_position

    @property
    def default_rotation(self):
        return self.__default_rotation

    def set_default_position(self):
        self.__default_position = copy.copy(self.position)
        for child in self.children:
            child.set_default_position()

    def get_default_position(self):
        return copy.copy(self.__default_position)

    def get_default_quaternion(self):
        return copy.copy(self.__default_quaternion)

    def Call_reset_to_default(self):
        for component in self.components.values():
            if hasattr(component, 'Reset') and component.Reset is not None and component.Active == True:
                try:
                    component.Reset()
                except Exception as e:
                    print(f"[Error] Exception in {component.__class__.__name__}.Reset(): {e}")
                    traceback.print_exc()

    def reset_to_default(self):
        self.position = self.get_default_position()
        self.quaternion = self.get_default_quaternion()
        if self.get_component("Rigidbody") is not None:
            self.Rigidbody.acceleration = Vector3(0, 0, 0)
            self.Rigidbody.velocity = Vector3(0, 0, 0)
            self.Rigidbody.angular_velocity = Vector3(0, 0, 0)
            self.Rigidbody.angular_acceleration = Vector3(0, 0, 0)
            self.Cache.set_dirty()

        self.Call_reset_to_default()

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
            collider = child.get_component("Collider")
            if rb and collider:
                all_objs.append(child)
            all_objs.extend(child.get_all_children_physics())
        return all_objs

    def get_all_children_not_physics(self):
        all_objs = []
        for child in self.children:
            rb = child.get_component("Rigidbody")
            # collider = child.get_component("Collider")
            if not rb:
                all_objs.append(child)
            all_objs.extend(child.get_all_children_physics())
        return all_objs

    def findTheCenterOfMass(self):
        objs = self.get_all_children_physics()
        if self.get_component("Rigidbody"):
            objs.append(self)
        total_mass = 0
        weighted_sum = Vector3(0, 0, 0)
        for obj in objs:
            weighted_sum += obj.position * obj.Rigidbody.mass
            total_mass += obj.Rigidbody.mass

        return weighted_sum / total_mass

    def __repr__(self):
        children_repr = ",\n    ".join(repr(child) for child in self.children)
        return (f"{self.name}(\n"
                f"  Position={self.position},\n"
                f"  Rotation={self.rotation},\n"
                f"  Size={self.size},\n"
                f"  children=[\n    {children_repr}\n  ]\n"
                f")")
