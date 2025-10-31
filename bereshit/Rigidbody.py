import numpy as np
from bereshit.Vector3 import Vector3



class Rigidbody:
    _friction_table = {
        ("Steel", "Concrete"): 0.6,
        ("Rubber", "Concrete"): 0.9,
        ("Rubber", "Steel"): 0.8,
        ("Wood", "Ice"): 0.04,
        ("Steel", "Steel"): 0.5,
        ("floor", "Steel"): 0.2,
        ("Steel", "Steel"): 0.2,
        # ("Steel", "Ice"): 0.1,
        # add more as needed
    }
    _default_friction = 0.6

    def __init__(self, obj=None, mass=1.0, size=Vector3(1, 1, 1), position=Vector3(0, 0, 0),
                 center_of_mass=Vector3(0, 0, 0), velocity=None, angular_velocity=None, force=None,
                 isKinematic=False, useGravity=True, drag=0.98, friction_coefficient=0.6, restitution=0.6,COM=None):
        self.mass = mass
        self.material = ""
        self.drag = drag
        self.obj = obj
        self.energy = 0
        self.restitution = restitution
        self.friction_coefficient = friction_coefficient if friction_coefficient is not None else self._default_friction
        self.center_of_mass = center_of_mass if center_of_mass else position
        self.velocity = velocity or Vector3(0, 0, 0)
        self.acceleration = Vector3()
        self.angular_acceleration = Vector3(0, 0, 0)
        self.torque = Vector3()
        self.force = force or Vector3(0, 0, 0)
        self.isKinematic = isKinematic
        self.forward = Vector3()

        self.useGravity = useGravity

        if angular_velocity is None:
            angular_velocity = Vector3(0, 0, 0)
        self.angular_velocity = angular_velocity

        self.normal_force = Vector3()

    def _get_friction(self, other_rb):
        """
        Returns the friction coefficient for the pair of materials.
        """

        if not other_rb:
            return self.friction_coefficient
        if self.friction_coefficient != Rigidbody._default_friction or other_rb.friction_coefficient != Rigidbody._default_friction:
            return min(self.friction_coefficient, other_rb.friction_coefficient)
        mat1 = self.material
        mat2 = other_rb.material
        key = (mat1, mat2)
        rev_key = (mat2, mat1)

        if key in Rigidbody._friction_table:
            return Rigidbody._friction_table[key]
        elif rev_key in Rigidbody._friction_table:
            return Rigidbody._friction_table[rev_key]
        else:
            return Rigidbody._default_friction

    def AddForce(self, force, ContactPoint=None):
        # Linear force always contributes directly to acceleration
        self.force += force

        if ContactPoint is not None:
            # r is the lever arm (vector from center of mass to contact point)
            r = self.parent.position - ContactPoint
            # torque = r × F
            self.torque += r.cross(force)

    def attach(self, owner_object):
        # self.size = owner_object.size
        # self.position = owner_object.position
        self.center_of_mass = owner_object.position
        self.obj = owner_object
        self.material = owner_object.material.kind
        self.forward = owner_object.quaternion.rotate(owner_object.position)
        EPSILON = 1e-8  # Small value to avoid division by zero

        hx = owner_object.size.x / 2
        hy = owner_object.size.y
        hz = owner_object.size.z

        self.inertia = Vector3(
            (1 / 12) * self.mass * (hy ** 2 + hz ** 2),  # I_x (unchanged)
            (1 / 12) * self.mass * (hx * 2) ** 2 + self.mass * (hx) ** 2 + (1 / 12) * self.mass * (hz ** 2),
            # simplified below
            (1 / 12) * self.mass * (hx * 2) ** 2 + self.mass * (hx) ** 2 + (1 / 12) * self.mass * (hy ** 2)
        )

        def safe_inverse(value):
            return 1.0 / value if abs(value) > EPSILON else 0.0

        self.inverse_inertia = np.diag([
            safe_inverse(self.inertia.x),
            safe_inverse(self.inertia.y),
            safe_inverse(self.inertia.z)
        ])
