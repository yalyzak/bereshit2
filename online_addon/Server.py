import selectors
import socket

sel = selectors.DefaultSelector()
clients = {}  # conn -> address

def accept(sock):
    conn, addr = sock.accept()
    print("Accepted connection from", addr)
    conn.setblocking(False)
    clients[conn] = addr
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn):
    try:
        data = conn.recv(1024)
        if data:
            msg = data.decode()
            print(f"Received from {clients[conn]}: {msg}")

            # Echo to everyone except the sender
            for other_conn in list(clients.keys()):
                if other_conn is not conn:
                    try:
                        other_conn.sendall(data)
                    except Exception:
                        print(f"Error sending to {clients[other_conn]}")
                        sel.unregister(other_conn)
                        other_conn.close()
                        del clients[other_conn]

        else:
            # Client closed connection
            print(f"Closing connection {clients[conn]}")
            sel.unregister(conn)
            conn.close()
            del clients[conn]

    except ConnectionResetError:
        print(f"Client reset connection {clients[conn]}")
        sel.unregister(conn)
        conn.close()
        del clients[conn]


# Create listening socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", 5000))
sock.listen()
sock.setblocking(False)

sel.register(sock, selectors.EVENT_READ, accept)

print("Server listening on port 5000...")

# Event loop
while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        callback = key.data
        callback(key.fileobj)
