import traceback

import numpy as np

from bereshit.Quaternion import Quaternion
from bereshit.Rigidbody import Rigidbody
from bereshit.Vector3 import Vector3


class World:
    def __init__(self, children=None,gizmos=None,gravity=Vector3(0, -9.8, 0)):
        self.children = children or []
        self.Camera = self.search_by_component('Camera')
        self.gizmos = gizmos
        self.gravity = gravity



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

    def apply_gravity(self,children):
        for child in children:
            rb = child.get_component("Rigidbody")
            # # === 2) APPLY GRAVITY (AND TORSOUE DUE TO GRAVITY) ===
            if rb.useGravity:
                rb.force += self.gravity * rb.mass

    def solve_collections(self, children, dt, gizmos):

        contacts = []
        contacts2 = []

        beta = 0.0  # softness factor for positional correction

        # STEP 1: Collect all contacts (use ALL manifold points)
        for i in range(len(children)):
            obj1 = children[i]
            rb1 = obj1.get_component("Rigidbody")

            for j in range(i + 1, len(children)):
                obj2 = children[j]
                rb2 = obj2.get_component("Rigidbody")

                # Skip if neither has a Rigidbody or both are kinematic
                if (rb1 is None or rb1.isKinematic) and (rb2 is None or rb2.isKinematic):
                    continue

                result = obj1.collider.check_collision(obj2, single_point=False)
                if result is None:
                    continue

                contact_points = result  # contact_points = [(cp, n, pn), ...]

                # Optional extra data (same per manifold)
                # rb1, rb2 = ref
                # ref_face_center, incident_face = arr[0], arr[1] if isinstance(arr, (list, tuple)) and len(
                #     arr) >= 2 else (None, None)
                if type(contact_points[0]) == tuple:  # For each point in the manifold, add a separate constraint
                    N = len(contact_points)
                    for (contact_point, normal, penetration) in contact_points:
                        contact_point = Vector3(contact_point)
                        r1 = contact_point - rb1.parent.position
                        r2 = contact_point - rb2.parent.position

                        v1 = (rb1.velocity + rb1.angular_velocity.cross(r1)* 0.0) if (
                                rb1 and not rb1.isKinematic) else Vector3(0, 0, 0)
                        v2 = (rb2.velocity + rb2.angular_velocity.cross(r2)* 0.0) if (
                                rb2 and not rb2.isKinematic) else Vector3(0, 0, 0)

                        v_rel = v1 - v2  # B minus A (matches normal pointing A->B)
                        v_norm = v_rel.dot(normal)

                        contacts2.append({
                            "j1" : 0,
                            "r1": r1,
                            "r2": r2,
                            "rb1": rb1,
                            "rb2": rb2,
                            "normal": normal,
                            "v_norm": v_norm,
                            "penetration": penetration,
                            "contact_point": contact_point,
                            # "ref_face_center": ref_face_center,
                            # "incident_face": incident_face,
                        })
                    contacts.append(contacts2)
                elif type(contact_points[0]) == Vector3:
                    contact_point, normal, penetration = contact_points
                    r1 = contact_point - rb1.parent.position
                    r2 = contact_point - rb2.parent.position

                    v1 = (rb1.velocity + rb1.angular_velocity.cross(r1)) if (
                            rb1 and not rb1.isKinematic) else Vector3(0, 0, 0)
                    v2 = (rb2.velocity + rb2.angular_velocity.cross(r2)) if (
                            rb2 and not rb2.isKinematic) else Vector3(0, 0, 0)

                    v_rel = v1 - v2  # B minus A (matches normal pointing A->B)
                    v_norm = v_rel.dot(normal)

                    contacts.append([{
                        "j1": 0,
                        "r1": r1,
                        "r2": r2,
                        "rb1": rb1,
                        "rb2": rb2,
                        "normal": normal,
                        "v_norm": v_norm,
                        "penetration": penetration,
                        "contact_point": contact_point,
                        # "ref_face_center": ref_face_center,
                        # "incident_face": incident_face,
                    }])
        if gizmos:
            self.set_gizmos(contacts=contacts)
        N = 0
        for i in range(len(contacts)):
            N += len(contacts[i])
        if N == 0:
            return contacts

        k = np.zeros((N, 2))
        for contact_point in contacts:
            length = len(contact_point)
            for i, c in enumerate(contact_point):
                rb1 = c["rb1"]
                rb2 = c["rb2"]
                restitution = 0.0

                if c["v_norm"] > -0.1 and c["v_norm"] < 0:
                    restitution
                elif rb1 and rb2:
                    restitution = min(rb1.restitution, rb2.restitution)
                elif rb1:
                    restitution = rb1.restitution
                elif rb2:
                    restitution = rb2.restitution

                rn1 = c["r1"].cross(c["normal"])  # Vector3
                rn2 = c["r2"].cross(c["normal"])

                if not rb1.isKinematic:
                    term1 = (Vector3.from_np(Iinv_world(rb1) @ rn1.to_np())).cross(c["r1"])
                else:
                    term1 = Vector3(0, 0, 0)

                if not rb2.isKinematic:
                    term2 = (Vector3.from_np(Iinv_world(rb2) @ rn2.to_np())).cross(c["r2"])
                else:
                    term2 = Vector3(0, 0, 0)
                denominator = (0 if rb1.isKinematic else 1 / rb1.mass) \
                              + (0 if rb2.isKinematic else 1 / rb2.mass) \
                              + c["normal"].dot(term1 + term2)
                denominator2 = (0 if rb1.isKinematic else 1 / rb1.mass) \
                               + (0 if rb2.isKinematic else 1 / rb2.mass)
                c["J1"] = (-(1 + restitution) * c["v_norm"]) / (denominator2 * length)
                # k[i, 0] = (-(1 + restitution) * c["v_norm"]) / (denominator2 * length)
                # c["J1"] = (-(1 + restitution) * c["v_norm"]) / denominator
                # k[i] /= length

        # STEP 4: Solve impulses (nonnegative)

        # impulses = np.linalg.pinv(A) @ b
        # impulses = np.maximum(impulses, 0.0)
        # STEP 5: Apply impulses for each contact point
        for contact_point in contacts:
            for i, contact in enumerate(contact_point):
                J1 = contact["J1"]

                if contact["v_norm"] >= 0:
                    continue
                #     J = 0
                #
                #
                #     continue  # separating
                flage = (restitution == 0)
                # flage = False
                n = contact["normal"]

                if contact["rb1"] and contact["rb2"]:
                    rb1 = contact["rb1"]
                    rb2 = contact["rb2"]
                    # rb1.isKinematic = True
                    # rb2.isKinematic = True

                    if not rb1.isKinematic and not rb2.isKinematic:
                        self.resolve_dynamic_collision(contact, J1,0, flage)
                        self.apply_friction_impulse(contact, n, J1)
                    elif (not rb1.isKinematic) or (not rb2.isKinematic):
                        self.resolve_kinematic_collision(contact, J1, 0, flage)
                        self.apply_friction_impulse(contact, n, J1)

        return contacts

    def apply_friction_impulse(self, contact, normal, Jn):
        """
        Applies Coulomb friction impulse based on the relative velocity,
        including angular friction effect.
        """
        rb1 = contact["rb1"]
        rb2 = contact["rb2"]
        contact_point = contact["contact_point"]  # required for torque calculation

        v1 = rb1.velocity if rb1 and not rb1.isKinematic else Vector3(0, 0, 0)
        v2 = rb2.velocity if rb2 and not rb2.isKinematic else Vector3(0, 0, 0)
        v_rel = v1 - v2

        tangent = v_rel - normal * v_rel.dot(normal)
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
        Jt_magnitude = -v_rel.dot(tangent)
        denom = 0.0
        if rb1 and not rb1.isKinematic:
            denom += 1.0 / rb1.mass
        if rb2 and not rb2.isKinematic:
            denom += 1.0 / rb2.mass

        if denom == 0.0:
            return

        Jt_magnitude /= denom
        max_friction = mu * Jn
        Jt_magnitude = max(-max_friction, min(Jt_magnitude, max_friction))

        Jt = tangent * Jt_magnitude

        # Apply linear and angular friction impulses
        if rb1 and not rb1.isKinematic:
            rb1.velocity += Jt / rb1.mass
            r1 = contact_point - rb1.parent.position
            angular_impulse1 = r1.cross(Jt)
            # rb1.angular_velocity += Vector3.from_np(rb1.inverse_inertia @ angular_impulse1.to_np())

        if rb2 and not rb2.isKinematic:
            rb2.velocity -= Jt / rb2.mass
            r2 = contact["r2"]
            angular_impulse2 = r2.cross(-Jt)
            # rb2.angular_velocity += Vector3.from_np(rb2.inverse_inertia @ angular_impulse2.to_np())

    def resolve_dynamic_collision(self, contact, J,J2, flage):
        """
        Applies linear and angular impulse to both dynamic bodies, factoring restitution.
        """
        n = contact["normal"]
        contact_point = contact["contact_point"]  # world-space contact point
        rb1 = contact["rb1"]
        rb2 = contact["rb2"]

        impulse_vec = n * J
        impulse_vec2 = n * J2
        # impulse_vec = np.maximum(impulse_vec, 0.0)
        if rb1 and not rb1.isKinematic:
            rb1.velocity += impulse_vec / rb1.mass
            if flage:
                rb1.force = Vector3()
                # rb1.velocity = Vector3()

            # Angular impulse for rb1
            r1 = contact["r1"]
            angular_impulse1 = r1.cross(impulse_vec2)
            rb1.angular_velocity += -Vector3.from_np(rb1.inverse_inertia @ angular_impulse1.to_np())

        if rb2 and not rb2.isKinematic:
            rb2.velocity -= impulse_vec / rb2.mass
            if flage:
                rb2.force = Vector3()
                # rb2.velocity = Vector3()
            # Angular impulse for rb2
            r2 = contact["r2"]
            angular_impulse2 = r2.cross(impulse_vec2)
            rb2.angular_velocity += -Vector3.from_np(rb2.inverse_inertia @ angular_impulse2.to_np())

    def resolve_kinematic_collision(self, contact, J, J2, flage):
        """
        Applies linear and angular impulse to the dynamic body only, factoring restitution.
        """
        n = contact["normal"]
        contact_point = contact["contact_point"]  # world-space contact point
        rb1 = contact["rb1"]
        rb2 = contact["rb2"]

        impulse_vec = n * J
        impulse_vec2 = n * J2

        if rb1 and not rb1.isKinematic:
            velocity = impulse_vec / rb1.mass
            r1 = contact["r1"]

            rb1.velocity += velocity
            # rb1.angular_velocity += r1.cross(velocity)


        if rb2 and not rb2.isKinematic:
            velocity = -impulse_vec / rb2.mass
            r2 = contact["r2"]

            rb2.velocity += velocity
            # rb2.angular_velocity += r2.cross(impulse_vec) / rb2.inertia

    def set_gizmos(self, contacts=[]):
        g = False
        for contact_point in contacts:
            for i, contact in enumerate(contact_point):
                self.gizmos.children[i].position = contact['contact_point']
                # self.children[1].children[i].quaternion = Quaternion.look_rotation(contact["normal"], Vector3(0,1,0))
                g = True

                for j in range(4):
                    pass

                    # self.children[1].children[i].children[j].position = contact['ref_face_center'][j]
                    #
                    # self.children[1].children[i].children[j + 4].position = contact['incident_face'][j]
        # while g:
        #     pass
        # Object(position=contacts['contact_point'])

    @staticmethod
    def solve_joints(children, dt):
        """
        Go through all objects, find joints, and solve their constraints.
        """
        for child in children:
            joint = child.get_component("joint")
            if joint is not None:
                joint.solve(dt)

    def Start(self):
        children1 = self.get_all_children()
        for child in children1:
            for component in child.components.values():
                if hasattr(component, 'Start') and component.Start is not None:
                    try:
                        component.Start()
                    except:
                        print(f"[Error] Exception in {component.__class__.__name__}.Start():")
                        traceback.print_exc()

    def update(self, dt, check=True, gizmos=False):
        allchildren = self.get_all_children()
        if check:
            for child in allchildren:
                for component in child.components.values():
                    if hasattr(component, 'Update') and component.Update is not None:
                        try:
                            component.Update(dt)
                        except Exception as e:
                            print(f"[Error] Exception in {component.__class__.__name__}.Update(): {e}")
                            traceback.print_exc()

        children = self.get_all_children_physics()
        self.apply_gravity(children)  # APPLY GRAVITY and external forces
        self.solve_collections(children, dt, gizmos)  # handel collisions and friction
        self.solve_joints(children, dt)

        for child in children:
            rb = child.get_component("Rigidbody")
            if rb is not None:
                child_children = child.get_all_children_not_physics()
                for child_of_child in child_children:
                    if child_of_child.get_component("Rigidbody") is not None:
                        child_of_child.position += child_of_child.Rigidbody.velocity * dt \
                                                   + 0.5 * child_of_child.Rigidbody.acceleration * dt * dt
                if not rb.isKinematic:
                    self.integrat(child,dt)

        for child in allchildren:
            child.rotation = child.quaternion.to_euler()
    @staticmethod
    def integrat(self, dt):
        rb = self.get_component("Rigidbody")
        # === 4) INTEGRATION PHASE ===
        # 4.1) Linear acceleration & velocity:
        rb.acceleration = rb.force / rb.mass

        # 4.2) Angular acceleration & velocity (component‐wise):
        rb.angular_acceleration = Vector3(
            rb.torque.x / rb.inertia.x if rb.inertia.x != 0 else 0,
            rb.torque.y / rb.inertia.y if rb.inertia.y != 0 else 0,
            rb.torque.z / rb.inertia.z if rb.inertia.z != 0 else 0
        )
        rb.angular_velocity += rb.angular_acceleration * dt
        # 4.3) Integrate rotation
        ang_disp = rb.angular_velocity * dt \
                   + 0.5 * rb.angular_acceleration * dt * dt

        self.quaternion *= Quaternion.euler(ang_disp)

        self.position += rb.velocity * dt \
                         + 0.5 * rb.acceleration * dt * dt

        rb.velocity += rb.acceleration * dt

        rb.force = Vector3(0, 0, 0)
        rb.torque = Vector3(0, 0, 0)

        rb.angular_acceleration = Vector3(0, 0, 0)
        rb.torque = Vector3(0, 0, 0)

        # rb.energy = 0.5 * self.parent.Rigidbody.mass * self.parent.Rigidbody.velocity.magnitude() ** 2 +
        # self.parent.Rigidbody.mass * 9.8 * self.parent.position.y
def Iinv_world(rb):
    if not rb or rb.isKinematic:
        # return identity-like mapper
        class _Zero:
            def __matmul__(self, x): return x  # won't be used

        return _Zero()
    # If rb.inverse_inertia is BODY-space, rotate it:
    # expected fields: rb.inv_inertia_body (3x3), rb.rotation_matrix (R)
    if hasattr(rb, "inverse_inertia") and hasattr(rb.parent.quaternion, "to_matrix3"):
        R = rb.parent.quaternion.to_matrix3()  # 3x3 world-from-body
        return R @ rb.inverse_inertia @ R.T
    # else assume the given one is already world
    return rb.inverse_inertia