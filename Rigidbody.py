import numpy as np

from bereshit import Quaternion, World
from bereshit.Vector3 import Vector3

from bereshit.bereshitCore import Component



class Rigidbody(Component):
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
    Scale = 1

    def __init__(self, obj=None, mass=1.0, size=Vector3(1, 1, 1), position=Vector3(0, 0, 0),
                 center_of_mass=Vector3(0, 0, 0), velocity=None, angular_velocity=None, force=None,
                 isKinematic=False, useGravity=True, drag=0.98, friction_coefficient=0.6, restitution=0.6, COM=None,
                 Freeze_Rotation=None):
        super().__init__()

        self.mass = mass
        self.invMass = 0.0 if isKinematic else 1 / mass
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
        self.Freeze_Rotation = Freeze_Rotation or Vector3(0, 0, 0)
        self.useGravity = useGravity

        if angular_velocity is None:
            angular_velocity = Vector3(0, 0, 0)
        self.angular_velocity = angular_velocity

        self.normal_force = Vector3()
        self._COM = COM

    def apply_gravity(self, Gravity):
        if self.useGravity:
            self.force += Gravity * self.mass

    @staticmethod
    def solve_impulse(rb1, rb2, contact_point, normal, penetration, dt, apply_friction=False):
        if not rb1.isKinematic:
            rb1.velocity += (rb1.force * rb1.invMass) * dt
            rb1.force.Zero()
        if not rb2.isKinematic:
            rb2.velocity += (rb2.force * rb2.invMass) * dt
            rb2.force.Zero()

        r1 = contact_point - rb1.parent.position
        r2 = contact_point - rb2.parent.position

        v1_at_p = rb1.velocity - rb1.angular_velocity.cross(r1)
        v2_at_p = rb2.velocity - rb2.angular_velocity.cross(r2)
        relative_vel = v2_at_p - v1_at_p
        v_norm = relative_vel.dot(normal)

        if v_norm >= 0:
            return 0

        rn1 = r1.cross(normal)
        rn2 = r2.cross(normal)

        if not rb1.isKinematic:
            term1 = (Vector3.from_np(rb1.Iinv_world() @ rn1.to_np())).cross(r1)
        else:
            term1 = Vector3(0, 0, 0)

        if not rb2.isKinematic:
            term2 = (Vector3.from_np(rb2.Iinv_world() @ rn2.to_np())).cross(r2)
        else:
            term2 = Vector3(0, 0, 0)

        restitution = rb1._get_restitution(rb2, v_norm)

        k_linear = (0 if rb1.isKinematic else rb1.invMass) + (0 if rb2.isKinematic else rb2.invMass)
        k_angular = normal.dot(term1 + term2)
        inv_eff_mass = k_linear + k_angular

        Rigidbody.positional_correction(rb1, rb2, penetration, normal, inv_eff_mass)

        J = -(1 + restitution) * v_norm / inv_eff_mass

        Rigidbody.apply_impulse_pair(rb1, rb2, normal * J, r1, r2)

        if apply_friction:
            rb1._apply_friction_impulse(rb2, relative_vel, normal, J, r1, r2)

    @staticmethod
    def positional_correction(rb1, rb2, penetration, normal, inv_eff_mass):
        percent = 0.11  # how aggressively to fix (0.2–0.8 is typical)
        slop = 0.05  # small tolerance to ignore tiny penetrations

        correction_mag = max(penetration - slop, 0) / inv_eff_mass * percent
        correction = normal * correction_mag

        if not rb1.isKinematic:
            rb1.parent.position -= correction * rb1.invMass

        if not rb2.isKinematic:
            rb2.parent.position += correction * rb2.invMass

    def _apply_friction_impulse(self, other, relative_vel, normal, J, r1, r2):
        """
        Applies Coulomb friction impulse based on the relative velocity,
        including angular friction effect.
        """
        rb1 = self
        rb2 = other

        tangent = relative_vel - normal * relative_vel.dot(normal)
        tangent_length = tangent.magnitude()

        if tangent_length < 1e-6:
            return  # No significant tangential motion

        tangent = tangent.normalized()

        # Friction coefficient
        if rb1 and rb2:
            mu = rb1._get_friction(rb2)
        elif rb1:
            mu = rb1.friction_coefficient
        elif rb2:
            mu = rb2.friction_coefficient
        else:
            mu = Rigidbody._default_friction

        # Compute friction impulse scalar
        Jt_magnitude = -relative_vel.dot(tangent)

        denom = 0.0

        if rb1 and not rb1.isKinematic:
            denom += 1.0 / rb1.mass

            r1xt = r1.cross(tangent)
            ang1 = rb1.Iinv_world() @ r1xt.to_np()
            ang1 = Vector3.from_np(ang1)
            denom += (ang1.cross(r1)).dot(tangent)

        if rb2 and not rb2.isKinematic:
            denom += 1.0 / rb2.mass

            r2xt = r2.cross(tangent)
            ang2 = rb2.Iinv_world() @ r2xt.to_np()
            ang2 = Vector3.from_np(ang2)
            denom += (ang2.cross(r2)).dot(tangent)

        if denom == 0.0:
            return
        Jt_magnitude /= denom
        max_friction = mu * J
        Jt_magnitude = max(-max_friction, min(Jt_magnitude, max_friction))

        Rigidbody.apply_impulse_pair(self, other, tangent * Jt_magnitude, r1, r2)

    @staticmethod
    def apply_impulse_pair(rb1, rb2, impulse_vec, r1, r2):
        negative_impulse = -impulse_vec

        if rb1 and not rb1.isKinematic:
            rb1.velocity += negative_impulse * rb1.invMass
            rb1.applyTorqueImpulse(impulse_vec, r1)

        if rb2 and not rb2.isKinematic:
            rb2.velocity += impulse_vec * rb2.invMass
            rb2.applyTorqueImpulse(negative_impulse, r2)

    def integrate(self, dt):

        self.acceleration = self.force * self.invMass
        angular_acceleration = self.torque.MatrixMultiplication(self._Iinv_world)
        if not self.Freeze_Rotation.x:
            self.angular_acceleration.x = angular_acceleration.x
        if not self.Freeze_Rotation.y:
            self.angular_acceleration.y = angular_acceleration.y
        if not self.Freeze_Rotation.z:
            self.angular_acceleration.z = angular_acceleration.z

        ang_disp = self.angular_velocity * dt + 0.5 * self.angular_acceleration * dt * dt

        self.angular_velocity += self.angular_acceleration * dt

        self.parent.quaternion *= Quaternion.euler_radians(ang_disp)

        if ang_disp.magnitude() > 0:
            self._update_inertia_world()
            self.parent.rotation = self.parent.quaternion.to_euler()
            self.parent.Cache.rotation_dirty = True
            self.parent.Cache.rotation_dirty_abs = True
            self.parent.Cache.aabb_dirty = True
            self.parent.up = self.parent.quaternion.rotate(Vector3(0, 1, 0))
            self.parent.forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))

        self.parent.position += self.velocity * dt + 0.5 * self.acceleration * dt * dt

        if (self.velocity.x or self.velocity.y or self.velocity.z) or (self.acceleration.x or self.acceleration.y or self.acceleration.z):
            self.parent.Cache.aabb_dirty = True

        self.velocity += self.acceleration * dt

        self.force.Zero()
        self.torque.Zero()

    def _get_friction(self, other_rb):
        """
        Returns the friction coefficient for the pair of materials.
        """
        return min(self.friction_coefficient,
                   other_rb.friction_coefficient)  # needs to better config friction_coefficient
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

    def _get_restitution(rb1, rb2, v_norm=None):
        restitution = 0.0
        if v_norm > -1:
            restitution
        elif rb1 and rb2:
            restitution = min(rb1.restitution, rb2.restitution)
        elif rb1:
            restitution = rb1.restitution
        elif rb2:
            restitution = rb2.restitution
        return restitution

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
        if self._COM is None:
            hx = owner_object.transform.size.x
            hy = owner_object.transform.size.y
            hz = owner_object.transform.size.z
            self.inertia = Vector3(
                (1 / 12) * self.mass * (hy ** 2 + hz ** 2),
                (1 / 12) * self.mass * (hx ** 2 + hz ** 2),
                (1 / 12) * self.mass * (hy ** 2 + hx ** 2)
            )

            self.inv_inertia = self.inertia.inverse()

            self.inertia_tensor = np.array([
                [self.inertia.x, 0.0, 0.0],
                [0.0, self.inertia.y, 0.0],
                [0.0, 0.0, self.inertia.z]
            ])

        else:
            def box_inertia_vector(mass, hx, hy, hz, com_offset):
                """
                Returns the inertia as a Vector3 (Ixx, Iyy, Izz)
                for a solid box with dimensions hx, hy, hz,
                shifted by a COM offset using the parallel-axis theorem.

                com_offset = Vector3(dx, dy, dz)
                """

                # === Base inertia at geometric center ===
                Ixx = (1 / 12) * mass * (hy * hy + hz * hz)
                Iyy = (1 / 12) * mass * (hx * hx + hz * hz)
                Izz = (1 / 12) * mass * (hx * hx + hy * hy)

                # === COM offset ===
                dx, dy, dz = com_offset.x, com_offset.y, com_offset.z

                # parallel-axis correction (diagonal terms)
                # d^2 - dx^2  → contributes to Ixx
                # d^2 - dy^2  → contributes to Iyy
                # d^2 - dz^2  → contributes to Izz
                d2 = dx * dx + dy * dy + dz * dz

                Ixx += mass * (d2 - dx * dx)
                Iyy += mass * (d2 - dy * dy)
                Izz += mass * (d2 - dz * dz)

                return Vector3(Ixx, Iyy, Izz)

            hx = owner_object.size.x
            hy = owner_object.size.y
            hz = owner_object.size.z

            self.inertia = box_inertia_vector(self.mass, hx, hy, hz, self._COM)
        self.center_of_mass = owner_object.transform.position
        self.obj = owner_object
        self.material = owner_object.material.kind
        self.forward = owner_object.transform.quaternion.rotate(owner_object.transform.position)

        EPSILON = 1e-8  # Small value to avoid division by zero

        def safe_inverse(value):
            return 1.0 / value if abs(value) > EPSILON else 0.0

        self.inverse_inertia = np.diag([
            safe_inverse(self.inertia.x),
            safe_inverse(self.inertia.y),
            safe_inverse(self.inertia.z)
        ])
        self.parent = owner_object
        self._update_inertia_world()

    def _update_inertia_world(self):
        if not self or self.isKinematic:
            self._Iinv_world = np.zeros((3, 3))
            return None

        R = self.parent.transform.quaternion.to_matrix3(self.parent.Cache)
        self._Iinv_world = R @ self.inverse_inertia @ R.T

    def Iinv_world(self):
        return self._Iinv_world

    def applyTorqueImpulse(self, impulse, R):
        torque_impulse = R.cross(impulse)
        local_torque_impulse = self.parent.quaternion.rotate_conjugated(torque_impulse)
        local_delta_w = local_torque_impulse * self.inv_inertia
        ang_impulse = self.parent.quaternion.rotate(local_delta_w)
        if self.Freeze_Rotation.x == 0:
            self.angular_velocity.x += ang_impulse.x
        if self.Freeze_Rotation.y == 0:
            self.angular_velocity.y += ang_impulse.y
        if self.Freeze_Rotation.z == 0:
            self.angular_velocity.z += ang_impulse.z
