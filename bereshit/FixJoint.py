class FixJoint:
    def __init__(self, other_object):
        """
        other_object: the Object you want to fix to.
        """
        self.other_object = other_object
        self.bodyA = None  # Will be filled in at attach time
        self.bodyB = other_object.get_component("Rigidbody")

        # Compute initial offset
        self.local_offset = None

    def attach(self, owner_object):
        """
        Called when this component is attached to an object.
        """
        self.bodyA = owner_object.get_component("Rigidbody")
        if self.bodyA is None or self.bodyB is None:
            raise ValueError("FixJoint requires both objects to have rigidbodies")
        if self.bodyB.isKinematic:
            raise ValueError("can not joint a Kinematic body")
        self.local_offset = self.bodyB.parent.position - self.bodyA.parent.position
        self.anchor_world = self.bodyA.parent.position + self.local_offset
        self.defaultA = self.bodyA.parent.quaternion
        self.defaultB = self.bodyB.parent.quaternion
        return "joint"

    def solve(self, dt):
        """
        Enforce linear velocity matching at the joint point (no relative motion).
        Only linear impulse correction (ignores angular).
        """
        deltaA = self.bodyA.parent.quaternion.conjugate() * self.defaultA

        deltaB = self.defaultB - self.bodyB.parent.quaternion
        local_offset = deltaA.rotate(self.local_offset)


        # Velocities at anchor points
        vA = self.bodyA.velocity  # ignoring angular contribution
        vB = self.bodyB.velocity

        # Relative velocity
        v_rel = vB - vA

        # Effective mass
        inv_massA = 1.0 / self.bodyA.mass if self.bodyA.mass > 0 else 0.0
        inv_massB = 1.0 / self.bodyB.mass if self.bodyB.mass > 0 else 0.0
        if self.bodyA.isKinematic:
            inv_massA = 0
        effective_mass = 1.0 / (inv_massA + inv_massB) if (inv_massA + inv_massB) > 0 else 0.0

        # Compute impulse to cancel relative velocity
        impulse = v_rel * (-effective_mass)
        target_position_B = self.bodyA.parent.position + local_offset
        correction = target_position_B - self.bodyB.parent.position
        if not self.bodyA.isKinematic and not self.bodyB.isKinematic:
            # Both dynamic — apply impulse to both
            self.bodyA.velocity -= impulse * inv_massA
            self.bodyB.velocity += impulse * inv_massB
        elif not self.bodyB.isKinematic:
            # Only B is dynamic — treat A as fixed
            self.bodyB.velocity += impulse * inv_massB
            self.bodyB.parent.position += correction
