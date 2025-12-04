import socket
import threading
import json
import random
import string

HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001

rooms = {}
user_rooms = {}
# rooms[passcode] = {
#    "users": {
#        username: (ip, udp_port)
#    }
# }

# ---------------------------------------------------
# Utility
# ---------------------------------------------------

def generate_passcode(length=6):
    chars = string.ascii_uppercase + string.digits
    return "0"
    return ''.join(random.choices(chars, k=length))


# ---------------------------------------------------
# TCP HANDLER (room creation, joining)
# ---------------------------------------------------

def handle_tcp_client(conn, addr):
    print("[TCP] Connection from", addr)

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            msg = json.loads(data.decode())
            action = msg.get("action")

            # --- Create Room ---
            if action == "create_room":
                passcode = generate_passcode()
                rooms[passcode] = {"users": {}}
                conn.send(json.dumps({"status": "ok", "room": passcode}).encode())

            # --- Find Room ---
            elif action == "find_room":
                room = msg["room"]
                exists = room in rooms
                conn.send(json.dumps({"exists": exists}).encode())

            # --- Join Room ---
            elif action == "join_room":
                room = msg["room"]
                username = msg["username"]
                udp_port = msg["udp_port"]  # client tells us its UDP listening socket

                # Room not found
                if room not in rooms:
                    conn.send(json.dumps({
                        "status": "error",
                        "message": "Room not found"
                    }).encode())
                    continue

                # Username already exists
                if username in rooms[room]["users"]:
                    conn.send(json.dumps({
                        "status": "error",
                        "message": "Username already taken"
                    }).encode())
                    continue

                # OK: add user
                rooms[room]["users"][username] = (addr[0], udp_port)
                user_rooms[username] = room
                conn.send(json.dumps({"status": "ok"}).encode())


    except Exception as e:
        print("[ERROR]", e)

    finally:
        conn.close()
        print("[TCP] Closed", addr)


def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, TCP_PORT))
    s.listen()
    print(f"[TCP] Listening on {HOST}:{TCP_PORT}")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()


# ---------------------------------------------------
# UDP BROADCAST HANDLER
# ---------------------------------------------------

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((HOST, UDP_PORT))

def broadcast(room, sender, message):
    if room not in rooms:
        return
    for username, (ip, port) in rooms[room]["users"].items():
        if username != sender:
            payload = json.dumps({
                "room": room,
                "from": sender,
                "message": message
            }).encode()

            udp_socket.sendto(payload, (ip, port))


def udp_server():
    print(f"[UDP] Listening for broadcast messages on {HOST}:{UDP_PORT}")

    while True:
        try:
            data, addr = udp_socket.recvfrom(4096)
        except ConnectionResetError:
            # Ignore – usually remote client closed or unreachable
            continue

        msg = json.loads(data.decode())
        # msg = { "action": "broadcast", "room": "...", "username": "...", "message": "..." }

        if msg.get("action") == "broadcast":
            username = msg["username"]
            message = msg["message"]

            # server decides room
            room = user_rooms.get(username)
            if room:
                broadcast(room, username, message)


def main():
    print("[SERVER] Starting...")

    threading.Thread(target=tcp_server, daemon=True).start()
    udp_server()   # UDP must stay on main thread


if __name__ == "__main__":
    main()
