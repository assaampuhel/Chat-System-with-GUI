import socket
import threading

# Server details
HOST = '127.0.0.1'
PORT = 12345

# Create socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Function to receive messages
def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                break
            print(message)
        except:
            print("An error occurred. Disconnected from server.")
            client.close()
            break

# Function to send messages
def send_messages():
    while True:
        msg = input()
        client.send(msg.encode())
        if msg.lower() == "exit":
            break

# Start threads for sending and receiving
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

send_thread = threading.Thread(target=send_messages)
send_thread.start()

# 