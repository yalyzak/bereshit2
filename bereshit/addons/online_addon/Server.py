import socket
import struct

clients = set()

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5000))

print("UDP Server listening on port 5000...")

while True:
    try:
        data, addr = sock.recvfrom(1024)
    except ConnectionResetError:
        # Ignore ICMP "port unreachable" errors (Windows quirk)
        continue
    except Exception as e:
        print("Recv error:", e)
        continue

    if addr not in clients:
        clients.add(addr)
        print("New client:", addr)

    # Try to decode safely
    try:
        if len(data) < 4:
            raise ValueError("Packet too short")

        # First 4 bytes = name length
        name_len = struct.unpack("!I", data[:4])[0]
        fmt = f"!I{name_len}s fff fff ffff"   # 6 floats total: pos(3) + vel(3)
        expected_len = struct.calcsize(fmt)

        if len(data) != expected_len:
            raise ValueError(f"Bad packet length: got {len(data)}, expected {expected_len}")

        unpacked = struct.unpack(fmt, data)
        _, name, x, y, z, xq, yq, zq, wq, vx, vy, vz = unpacked


        # Broadcast to all other clients
        for other_addr in list(clients):
            if other_addr != addr:
                try:
                    sock.sendto(data, other_addr)
                except Exception as e:
                    print(f"Error sending to {other_addr}: {e}")
                    clients.discard(other_addr)

    except Exception as e:
        print(f"Bad packet from {addr}: {e}")
