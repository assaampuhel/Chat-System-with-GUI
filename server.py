import socket
import threading

# Server configuration
HOST = '127.0.0.1'
PORT = 12345

# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"Server started and listening on {HOST}:{PORT}...")

# List to store all connected clients
clients = []
nicknames = []

# Broadcast message to all clients
def broadcast(message, sender_conn=None):
    for client in clients:
        # Don’t send back to the sender if sender_conn is given
        if client != sender_conn:
            try:
                client.send(message)
            except:
                # Remove disconnected clients safely
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                nicknames.remove(nickname)
                broadcast(f"{nickname} has been disconnected unexpectedly.\n".encode())

# Handle messages from a single client
def handle_client(conn, addr):
    print(f"New connection from {addr}")
    
    # Ask for a nickname
    conn.send("Enter your nickname: ".encode())
    nickname = conn.recv(1024).decode()
    nicknames.append(nickname)
    clients.append(conn)

    print(f"Nickname of {addr} is {nickname}")
    broadcast(f"\n{nickname} joined the chat!\n".encode(), sender_conn=conn)
    conn.send("Connected to the server! Type 'exit' to leave.\n".encode())

    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
            
            # Handle exit message
            if message.lower() == "exit":
                broadcast(f"\n{nickname} has left the chat.\n".encode(), sender_conn=conn)
                print(f"{nickname} disconnected.")
                conn.send("You have left the chat. Goodbye!\n".encode())
                conn.close()
                clients.remove(conn)
                nicknames.remove(nickname)
                break

            # Broadcast the message to everyone
            full_msg = f"{nickname}: {message}\n"
            print(full_msg.strip())
            broadcast(full_msg.encode(), sender_conn=conn)
        except:
            # Handle unexpected disconnection
            if conn in clients:
                clients.remove(conn)
                nickname = nicknames[clients.index(conn)] if conn in clients else "Unknown"
                broadcast(f"{nickname} has been disconnected.\n".encode())
            break

# Accept incoming connections
def receive_connections():
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

# Start server
receive_connections()