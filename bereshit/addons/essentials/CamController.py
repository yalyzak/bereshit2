import time
import keyboard
from bereshit import Vector3

class CamController:
    def __init__(self,speed=15,speed2=15):
        self.force_amount = speed
        self.force_amount2 = speed2

    def keyboard_controller(self,dt):
        if keyboard.is_pressed('esc'):
            print("Paused. Release ESC to continue.")

            # Wait until ESC is released
            while keyboard.is_pressed('esc'):
                time.sleep(0.05)

            print("Now press ESC again to continue.")

            # Wait for ESC to be pressed again
            while not keyboard.is_pressed('esc'):
                time.sleep(0.05)

            # Wait for ESC to be released again before continuing
            while keyboard.is_pressed('esc'):
                time.sleep(0.05)

            print("Continuing...")

        if keyboard.is_pressed('w'):
            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))
            # flatten to XZ plane
            forward = Vector3(forward.x, 0, forward.z).normalized() * self.force_amount
            self.parent.Rigidbody.velocity += forward * dt


        if keyboard.is_pressed('s'):
            backward = self.parent.quaternion.rotate(Vector3(0, 0, -1))
            backward = Vector3(backward.x, 0, backward.z).normalized() * self.force_amount
            self.parent.Rigidbody.velocity += backward * dt

        if keyboard.is_pressed('a'):
            right = self.parent.quaternion.rotate(Vector3(1, 0, 0))
            right = Vector3(right.x, 0, right.z).normalized() * self.force_amount
            self.parent.Rigidbody.velocity += right * dt

        if keyboard.is_pressed('d'):
            left = self.parent.quaternion.rotate(Vector3(-1, 0, 0))
            left = Vector3(left.x, 0, left.z).normalized() * self.force_amount
            self.parent.Rigidbody.velocity += left * dt

        if keyboard.is_pressed('space'):
            self.parent.Rigidbody.velocity += Vector3(0, self.force_amount2, 0) * dt

        if keyboard.is_pressed('left shift'):
            self.parent.Rigidbody.velocity += Vector3(0, -self.force_amount2, 0) * dt

    def keyboard_controller(self, dt):
        if keyboard.is_pressed('esc'):
            print("Paused. Release ESC to continue.")

            # Wait until ESC is released
            while keyboard.is_pressed('esc'):
                time.sleep(0.05)

            print("Now press ESC again to continue.")

            # Wait for ESC to be pressed again
            while not keyboard.is_pressed('esc'):
                time.sleep(0.05)

            # Wait for ESC to be released again before continuing
            while keyboard.is_pressed('esc'):
                time.sleep(0.05)

            print("Continuing...")

        if keyboard.is_pressed('w'):
            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))
            # flatten to XZ plane
            forward = Vector3(forward.x, 0, forward.z).normalized() * self.force_amount
            self.parent.position += forward * dt

        if keyboard.is_pressed('s'):
            backward = self.parent.quaternion.rotate(Vector3(0, 0, -1))
            backward = Vector3(backward.x, 0, backward.z).normalized() * self.force_amount
            self.parent.position += backward * dt

        if keyboard.is_pressed('a'):
            right = self.parent.quaternion.rotate(Vector3(1, 0, 0))
            right = Vector3(right.x, 0, right.z).normalized() * self.force_amount
            self.parent.position += right * dt

        if keyboard.is_pressed('d'):
            left = self.parent.quaternion.rotate(Vector3(-1, 0, 0))
            left = Vector3(left.x, 0, left.z).normalized() * self.force_amount
            self.parent.position += left * dt

        if keyboard.is_pressed('space'):
            self.parent.position += Vector3(0, self.force_amount2, 0) * dt

        if keyboard.is_pressed('left shift'):
            self.parent.position += Vector3(0, -self.force_amount2, 0) * dt
    def Update(self,dt):
        self.keyboard_controller(dt)

        # # Get the player's current position
        # player_pos = self.player.position
        #
        # # Calculate new camera position: 10 cm behind player
        # new_cam_pos = player_pos + Vector3(0,1.0,- 0.2)
        #
        # # Update this camera's transform
        # self.parent.position = new_cam_pos
