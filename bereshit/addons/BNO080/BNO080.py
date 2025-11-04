import serial
import threading
import time
from bereshit.Vector3 import Vector3
from bereshit.Quaternion import Quaternion

class readData:
    def __init__(self, port='COM4', baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = False
        self.lock = threading.Lock()

        # Latest quaternion values
        self.qI = self.qJ = self.qK = self.qReal = 0.0
        self.accuracy = 0.0

        # Base quaternion (first stable reading)
        self.base_quat = None
        self.base_captured = False

        # Parent object (set externally by Bereshit)
        self.parent = None

    # ----------------------------------------------------------------------
    def Start(self):
        """Open serial port and start background thread"""
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            print(f"[readData] Connected to {self.port}")
        except Exception as e:
            print(f"[readData] Failed to open {self.port}: {e}")

    # ----------------------------------------------------------------------
    def _read_loop(self):
        """Continuously reads quaternion data from serial"""
        while self.running:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if not line:
                    continue

                parts = line.split(',')
                if len(parts) >= 5:
                    with self.lock:
                        self.qI = float(parts[0])
                        self.qJ = float(parts[1])
                        self.qK = float(parts[2])
                        self.qReal = float(parts[3])
                        self.accuracy = float(parts[4])

                        # Capture first quaternion as base
                        if not self.base_captured:
                            self.base_quat = Quaternion(self.qI, self.qJ, self.qK, self.qReal)
                            self.base_captured = True
                            print(f"[readData] Base quaternion captured: {self.base_quat}")

            except Exception as e:
                print(f"[readData] Error: {e}")
                time.sleep(0.05)

    # ----------------------------------------------------------------------
    def Update(self, dt):
        """Called every frame — updates parent rotation relative to base"""
        if not self.parent or not self.base_captured:
            return

        with self.lock:
            current = Quaternion(self.qJ, self.qI, self.qK, self.qReal)
            # Compute relative rotation from base
            relative = current * self.base_quat.conjugate()

            # Apply to parent
            self.parent.quaternion = relative

    # ----------------------------------------------------------------------
    def Stop(self):
        """Stops the thread and closes the serial port"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[readData] Stopped")
