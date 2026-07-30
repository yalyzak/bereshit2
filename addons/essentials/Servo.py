from bereshit import HingeJoint, MeshRander, Component, Vector3
import keyboard


class Servo(Component):
    def __init__(self, mount, axis, max_rotation=90, min_rotation=-90, speed=10, torque=1, max_speed=60):
        super(Servo, self).__init__()
        self._servo = None
        self._mount = mount
        self._axis = axis
        self._max_r = max_rotation
        self._min_r = min_rotation
        self._speed = speed
        self._torque = torque
        self._max_speed = max_speed

    def attach(self, parent):
        self._servo = parent


        self._servo.add_component(
            HingeJoint(self._mount, self._axis),
            ServoController(self._mount, max_rotation=self._max_r, min_rotation=self._min_r, input_speed=self._speed, max_speed=self._max_speed, max_torque=self._torque))

        return "Servo"


class ServoController(Component):
    def get_target_angle(self):
        return self._target_angle

    def __init__(self, other, max_rotation=90, min_rotation=-90, max_speed=1, input_speed=60, max_torque=1):
        super(ServoController, self).__init__()
        self._target_angle = 0.0

        self.max_speed = max_speed
        self.input_speed = input_speed
        self.max_torque = max_torque

        self._axis = Vector3()
        self.max_rotation = max_rotation
        self.min_rotation = min_rotation
        self.other = other

    def Reset(self):
        self._target_angle = 0.0

    def move(self, input_value, dt):
        joint = self.parent.HingeJoint
        self._axis = joint.axis_world.normalized()

        self._target_angle += input_value * self.input_speed * dt
        self._target_angle = max(
            min(self._target_angle, self.max_rotation),
            self.min_rotation
        )

    def fix(self, dt):
        axis = self.parent.HingeJoint.axis_world.normalized()
        rb = self.parent.Rigidbody

        relative_q = self.other.transform.quaternion.conjugate() * self.parent.transform.quaternion
        current_angle = relative_q.to_euler().dot(axis)

        error = self._target_angle - current_angle
        error = (error + 180) % 360 - 180

        angular_velocity = rb.angular_velocity.dot(axis)

        # degrees/sec
        max_speed = self.max_speed

        # slow down near target
        slow_distance = 20.0  # degrees
        desired_velocity = max_speed * max(min(error / slow_distance, 1.0), -1.0)

        # velocity controller
        velocity_error = desired_velocity - angular_velocity

        # convert velocity error into torque
        torque = velocity_error * self.max_torque

        # clamp torque
        torque = max(min(torque, self.max_torque), -self.max_torque)

        # stop jitter near target
        if abs(error) < 0.3 and abs(angular_velocity) < 0.2:
            torque = 0

        self.parent.Rigidbody.apply_angular_impulse(torque * dt * axis)

    def clamp_rotation(self):
        self.parent.transform.quaternion = max(min(self.parent.transform.quaternion.to_euler(), self.max_rotation), -self.max_rotation)

    def clamp_speed(self):
        self.parent.Rigidbody.angular_velocity.z = max(min(self.parent.Rigidbody.angular_velocity.z, self.max_speed),
                                                       -self.max_speed)

    def apply_angular_impulse(self, impulse: Vector3):
        rb = self.parent.Rigidbody
        delta_w = rb.Iinv_world() @ impulse.to_np()
        rb.angular_velocity += Vector3.from_np(delta_w)

    def PhysicsUpdate(self, dt):
        self.fix(dt)


class ServoControllerKeyboard(ServoController):
    def __init__(self, other, max=90, min=-90, keys=["e", "q"]):
        super().__init__(other, max, min)
        self.key0 = keys[0]
        self.key1 = keys[1]

    @staticmethod
    def get_keyboard_input(key_neg, key_pos):
        value = 0.0
        if keyboard.is_pressed(key_neg):
            value -= 1.0
        if keyboard.is_pressed(key_pos):
            value += 1.0
        return value

    def PhysicsUpdate(self, dt):
        super().PhysicsUpdate(dt)
        input_value = ServoControllerKeyboard.get_keyboard_input(self.key0, self.key1)
        if input_value != 0:
            self.move(input_value, dt)




