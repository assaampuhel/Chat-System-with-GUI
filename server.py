import socket
import threading
from datetime import datetime

HOST = "0.0.0.0"
PORT = 12345

clients = {}            # conn -> username
clients_lock = threading.Lock()


def broadcast(message, sender_conn=None):
    """Send message (str) to all connected clients except sender_conn."""
    with clients_lock:
        for conn in list(clients.keys()):
            if conn == sender_conn:
                continue
            try:
                conn.send(message.encode("utf-8"))
            except Exception:
                # remove dead connections
                try:
                    conn.close()
                except:
                    pass
                remove_client(conn)


def handle_client(conn, addr):
    username = None
    try:
        # Expect first message from client to be the username
        raw = conn.recv(1024)
        if not raw:
            conn.close()
            return
        username = raw.decode("utf-8", errors="replace").strip()
        if not username:
            conn.close()
            return

        with clients_lock:
            clients[conn] = username

        join_msg = f"[{datetime.now().strftime('%I:%M %p')}] Server: {username} joined the chat!"
        print(join_msg)
        broadcast(join_msg, sender_conn=None)

        # Main receive loop
        while True:
            data = conn.recv(4096)
            if not data:
                # client disconnected
                break
            msg = data.decode("utf-8", errors="replace").strip()
            if not msg:
                continue

            if msg.lower() == "exit":
                # client requested exit
                break

            timestamp = datetime.now().strftime("[%I:%M %p]")
            formatted = f"{timestamp} {username}: {msg}"
            print(formatted)
            # broadcast to all OTHER clients (sender sees own msg locally)
            broadcast(formatted, sender_conn=conn)

    except Exception as e:
        print(f"Exception with {addr}: {e}")

    finally:
        # clean up and announce leave
        if username:
            with clients_lock:
                if conn in clients:
                    del clients[conn]
        try:
            conn.close()
        except:
            pass

        leave_msg = f"[{datetime.now().strftime('%I:%M %p')}] Server: {username or 'Unknown'} left the chat."
        print(leave_msg)
        broadcast(leave_msg, sender_conn=None)


def remove_client(conn):
    with clients_lock:
        if conn in clients:
            del clients[conn]
    try:
        conn.close()
    except:
        pass


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow quick restart during development
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(100)
    print(f"🚀 Server started on {HOST}:{PORT}")
    print("Waiting for connections...")

    try:
        while True:
            conn, addr = server.accept()
            print(f"✅ Connection from {addr}")
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        with clients_lock:
            for c in list(clients.keys()):
                try:
                    c.close()
                except:
                    pass
        try:
            server.close()
        except:
            pass


if __name__ == "__main__":
    start_server()