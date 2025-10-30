# 🗨️ Chat System using Python Sockets and Tkinter

## 📘 Overview
This project is a **real-time chat application** built using Python’s `socket` and `threading` libraries, along with a **Tkinter-based GUI** for the client interface.  
It enables multiple clients to connect to a single server and exchange messages instantly.

---

## 🏗️ Project Structure
Chat-System/
│
├── server.py     # Handles all incoming client connections and message broadcasting
├── client.py     # Provides GUI interface for chatting
└── README.md     # Documentation (this file)

---

## ⚙️ How It Works

### **Server Side (`server.py`)**
1. Creates a **TCP socket** to listen for incoming connections.
2. Uses **multi-threading** to handle multiple clients concurrently.
3. Broadcasts each message to all connected clients.
4. Gracefully removes disconnected clients to maintain stability.

### **Client Side (`client.py`)**
1. Connects to the server using its IP and port number.
2. Provides a **Tkinter GUI** where users can type and send messages.
3. Uses a separate thread to receive incoming messages asynchronously.
4. Displays chat history in a scrollable text area.

---

## 🚀 How to Run the Project

### **Step 1: Run the Server**
```bash
python3 server.py
```

You should see a message like:
```bash
Server started on IP 127.0.0.1 and port 55555
Waiting for connections...
```

Enter your username when prompted and start chatting!

⸻

## 🧩 Key Features
1. Real-time chat communication
2. Multi-client support via threading
3. Simple and elegant Tkinter GUI
4. Message broadcasting to all users
5. Handles client disconnections gracefully

⸻

## 🧠 Approach Summary
1. Socket Programming: Used TCP sockets to enable communication between server and clients.
2. Concurrency: Used Python’s threading module so that each client runs independently
3. GUI Design: Built with Tkinter, ensuring smooth message sending and real-time updates.
4. Problem Handling: Implemented safe socket closure and message queue handling to prevent crashes.

⸻

## 🧾 Example Output

Server Terminal:
```bash
New connection: 127.0.0.1
User joined: Alice
Message from Bob: Hello everyone!
```

Client Window:
```bash
Alice: Hi Bob!
Bob: Hello everyone!
```