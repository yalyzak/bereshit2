import socket
import struct




print("UDP Server listening on port 5000...")
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
print(f"Your Computer's Local IP Address is: {IPAddr}")
def get_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # connect() doesn't actually send packets
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
print("Your computer's IPv4 address is:", get_ipv4())

class Server:
    def __init__(self):
        self.clients = set()

        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 5000))

    def Add_Client(self, addr):
        self.clients.add(addr)
        print("New client:", addr)
    def Unpack(self, data):
        if len(data) < 4:
            raise ValueError("Packet too short")

        # First 4 bytes = name length
        name_len = struct.unpack("!I", data[:4])[0]
        fmt = f"!I{name_len}s fff fff ffff"  # 6 floats total: pos(3) + vel(3)
        expected_len = struct.calcsize(fmt)

        if len(data) != expected_len:
            print(f"Bad packet length: got {len(data)}, expected {expected_len}")
            return None
        unpacked = struct.unpack(fmt, data)

        return unpacked
    def Broadcast(self, addr, data):
        for other_addr in list(self.clients):
            if other_addr != addr:
                try:
                    self.sock.sendto(data, other_addr)
                except Exception as e:
                    print(f"Error sending to {other_addr}: {e}")
                    self.clients.discard(other_addr)


    def Main(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
            except ConnectionResetError:
                # Ignore ICMP "port unreachable" errors (Windows quirk)
                continue
            except Exception as e:
                print("Recv error:", e)
                continue

            if addr not in self.clients:
                self.Add_Client(addr)

            # Try to decode safely
            try:
                result = self.Unpack(data)
                if result is None:
                    self.sock.sendto("Bad packet length".encode(), addr)
                else:
                    _, name, x, y, z, xq, yq, zq, wq, vx, vy, vz = result
                    # Broadcast to all other clients
                    self.Broadcast(addr,data)

            except Exception as e:
                print(f"Bad packet from {addr}: {e}")

server = Server()
server.Main()