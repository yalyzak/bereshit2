import socket
import struct

clients = {}   # (ip, port) -> id
next_id = 1

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5000))
print("UDP Server listening on port 5000...")


while True:
    try:
        data, addr = sock.recvfrom(1024)
    except Exception as e:
        print("Socket error:", e)
        continue

    if not data:
        continue

    # Assign ID if new client
    if addr not in clients:
        try:
            clients[addr] = next_id
            print(f"New client {addr} assigned ID {next_id}")

            # Send assigned ID back (4 bytes)
            msg = struct.pack("!I", next_id)
            sock.sendto(msg, addr)

            next_id += 1
        except Exception as e:
            print("Error assigning ID:", e)
        continue

    # Validate message (must contain at least name_len field)
    try:
        if len(data) < 4:
            print(f"Ignoring too-short packet from {addr}")
            continue

        name_len = struct.unpack("!I", data[:4])[0]

        # Expected size for full message
        expected_size = 4 + name_len + struct.calcsize("!I fff fff ffff fff fff")
        if len(data) != expected_size:
            print(f"Ignoring malformed packet from {addr}, size {len(data)} expected {expected_size}")
            continue

    except struct.error as e:
        print(f"Struct unpack error from {addr}:", e)
        continue
    except Exception as e:
        print(f"Unexpected error decoding from {addr}:", e)
        continue

    # Relay to all other clients
    for other_addr in list(clients.keys()):
        if other_addr == addr:
            continue
        try:
            sock.sendto(data, other_addr)
        except Exception as e:
            print(f"Error sending to {other_addr}: {e}")
            # Optionally remove dead clients
            # del clients[other_addr]
