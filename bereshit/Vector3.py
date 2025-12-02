import math
import numpy as np
from math import sqrt
from dataclasses import dataclass



class Vector3:

    def __init__(self,x=0,y=0,z=0):
        if type(x) == tuple and len(x) == 3:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
        else:
            self.x = x
            self.y = y
            self.z = z

    def floor(self):
        factor = 10 ** 5
        return Vector3(math.floor(self.x * factor) / factor, math.floor(self.y * factor) / factor,
                       math.floor(self.x * factor) / factor)

    def __iadd__(self, other):
        if isinstance(other, Vector3):
            self.x += other.x
            self.y += other.y
            self.z += other.z
        elif isinstance(other, (list, tuple, np.ndarray)):
            self.x += other[0]
            self.y += other[1]
            self.z += other[2]
        else:
            raise TypeError(f"Unsupported type for +=: {type(other)}")
        return self

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __add__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        elif isinstance(other, (list, tuple, np.ndarray)) and len(other) == 3:
            return Vector3(self.x + other[0], self.y + other[1], self.z + other[2])
        raise TypeError(f"Unsupported type for addition: {type(other)}")

    def __sub__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        raise TypeError("Subtraction only supported between Vector3 instances")

    def __truediv__(self, other):
        if isinstance(other, Vector3):
            if other.x == 0 or other.y == 0 or other.z == 0:
                raise ZeroDivisionError("Division by zero in vector components")

            return Vector3(
                self.x / other.x if other.x != 0 else 0,
                self.y / other.y if other.y != 0 else 0,
                self.z / other.z if other.z != 0 else 0
            )
        elif isinstance(other, (int, float)):
            return Vector3(self.x / other, self.y / other, self.z / other)
        raise TypeError(f"Unsupported division between Vector3 and {type(other)}")

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector3(self.x * other, self.y * other, self.z * other)
        elif isinstance(other, Vector3):
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        raise TypeError("Unsupported type for multiplication")

    def __copy__(self):
        return Vector3(self.x, self.y, self.z)

    def __eq__(self, other):
        return isinstance(other, Vector3) and (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __rmatmul__(self, matrix):
        """
        Enables: matrix @ Vector3
        Assumes matrix is a 3x3 NumPy array or list-of-lists.
        """
        if isinstance(matrix, (list, tuple)):
            matrix = np.array(matrix)
        result = matrix @ self.to_np()
        return Vector3.from_np(result)

    def dis(self, other: 'Vector3') -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return sqrt(dx * dx + dy * dy + dz * dz)

    @staticmethod
    def rotate_vector_old(vector, pivot, angles):
        vector = np.array([vector.x, vector.y, vector.z])
        pivot = np.array([pivot.x, pivot.y, pivot.z])
        angles = np.array([angles.x, angles.y, angles.z])

        angle_x, angle_y, angle_z = np.radians(angles)
        R_x = np.array([[1, 0, 0],
                        [0, math.cos(angle_x), -math.sin(angle_x)],
                        [0, math.sin(angle_x), math.cos(angle_x)]])
        R_y = np.array([[np.cos(angle_y), 0, np.sin(angle_y)],
                        [0, 1, 0],
                        [-math.sin(angle_y), 0, math.cos(angle_y)]])
        R_z = np.array([[math.cos(angle_z), -math.sin(angle_z), 0],
                        [math.sin(angle_z), math.cos(angle_z), 0],
                        [0, 0, 1]])
        R = R_z @ R_y @ R_x
        temp = R @ (vector - pivot) + pivot

        return Vector3(temp[0], temp[1], temp[2])

    @staticmethod
    def mean(vectors: list):
        n = len(vectors)
        if n == 0:
            return Vector3(0, 0, 0)
        sx = sum(v.x for v in vectors)
        sy = sum(v.y for v in vectors)
        sz = sum(v.z for v in vectors)
        return Vector3(sx / n, sy / n, sz / n)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def to_np(self):
        if isinstance(self, Vector3):
            return np.array([self.x, self.y, self.z], dtype='f4')
        elif isinstance(self, list):
            return np.array([np.array([item.x, item.y, item.z], dtype='f4') for item in self])

    @classmethod
    def from_np(cls, arr):
        """Create a Vector3 from a NumPy array or list."""
        return cls(arr[0], arr[1], arr[2])

    def magnitude(self):
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalized(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)  # Handle zero-length vector safely
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    def direction_vector(self, other):
        return (other - self).normalized()

    def reduce_vector_along_direction(size_vector, direction_vector):
        dot = size_vector.dot(direction_vector)
        if dot > 0:
            return direction_vector * dot
        else:
            return Vector3(0, 0, 0)

    def __rmul__(self, other):
        return self.__mul__(other)

    def to_tuple(self):
        return self.x, self.y, self.z

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __repr__(self):
        return f"Vector3(x={self.x}, y={self.y}, z={self.z})"