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

    if addr not in clients:
        clients.add(addr)
        print("New client:", addr)

    # Unpack message
    name_len = struct.unpack("!I", data[:4])[0]
    fmt = f"!I{name_len}sfff"
    _, name, x, y, z = struct.unpack(fmt, data)

    print(f"From {addr} -> Name: {name.decode()}, Pos: ({x:.2f}, {y:.2f}, {z:.2f})")

    # Broadcast to all other clients
    for other_addr in clients:
        if other_addr != addr:
            try:
                sock.sendto(data, other_addr)
            except Exception:
                print(f"Error sending to {other_addr}")