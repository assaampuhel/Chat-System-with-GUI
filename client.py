import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from datetime import datetime
import hashlib

# ===== CONFIG =====
HOST = "127.0.0.1"   # <-- change to server IP (e.g., '192.168.1.5') for LAN use
PORT = 12345
# ==================


def deterministic_color(name):
    """Return a hex color chosen deterministically from username."""
    colors = [
        "#FF6B6B", "#4ECDC4", "#FFD93D", "#6A5ACD",
        "#1E90FF", "#FF8C00", "#9B59B6", "#2ECC71",
        "#E67E22", "#3498DB", "#E74C3C", "#16A085"
    ]
    h = int(hashlib.sha256(name.encode()).hexdigest(), 16)
    return colors[h % len(colors)]


class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Room")
        self.master.geometry("600x520")
        self.master.configure(bg="#121212")

        # Prompt for username
        self.username = simpledialog.askstring("Nickname", "Enter your nickname:", parent=self.master)
        if not self.username:
            self.master.destroy()
            return

        # Networking
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((HOST, PORT))
        except Exception as e:
            messagebox.showerror("Connection error", f"Could not connect to server:\n{e}")
            self.master.destroy()
            return

        # Send nickname once
        try:
            self.sock.send(self.username.encode("utf-8"))
        except Exception:
            messagebox.showerror("Connection error", "Failed to send nickname.")
            self.master.destroy()
            return

        # UI: chat display
        self.text_area = scrolledtext.ScrolledText(
            master, wrap=tk.WORD, bg="#0F0F0F", fg="#E8E8E8",
            font=("Consolas", 11), padx=8, pady=8
        )
        self.text_area.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)

        # Define basic tags up-front
        self.text_area.tag_config("system", foreground="#9AA3B2", font=("Consolas", 9, "italic"))
        self.text_area.tag_config("timestamp", foreground="#6A9955", font=("Consolas", 8))
        self.text_area.tag_config("self_name", foreground=deterministic_color(self.username), font=("Consolas", 10, "bold"))
        self.text_area.tag_config("self_msg", foreground="#FFFFFF", font=("Consolas", 11))
        self.text_area.tag_config("other_msg", foreground="#DDDDDD", font=("Consolas", 11))

        # Input area
        bottom = tk.Frame(master, bg="#121212")
        bottom.pack(fill=tk.X, padx=12, pady=(0,12))

        self.entry = tk.Entry(bottom, font=("Consolas", 12), bg="#1E1E1E", fg="#FFFFFF", insertbackground='white')
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(bottom, text="Send", width=10, bg="#4CAF50", fg="white", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

        # Map for colors of remote users
        self.user_colors = {self.username: deterministic_color(self.username)}

        # Flag and receive thread
        self.running = True
        self.recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.recv_thread.start()

        # Show connection system message locally
        self.display_system(f"Connected to server. Type 'exit' to leave.")

        # Handle window close
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- network receive ----------
    def receive_loop(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    # connection closed by server
                    self.schedule_system("Disconnected from server.")
                    break
                text = data.decode("utf-8", errors="replace")
                # Process possible multi-line
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Expected server format for user messages:
                    # "[HH:MM AM] username: message"
                    # Server join/leave are: "[HH:MM AM] Server: ...", treat Server as system
                    if ": " in line:
                        # parse first token(s) timestamp then username: message
                        # We'll try to extract username part after timestamp
                        # Find first '] ' to separate timestamp (if present)
                        username = None
                        message_body = None
                        if line.startswith("[") and "]" in line:
                            # split at first ']'
                            try:
                                _, rest = line.split("]", 1)
                                rest = rest.strip()
                                if ": " in rest:
                                    username, message_body = rest.split(": ", 1)
                            except Exception:
                                username = None
                        else:
                            # fallback split at first ': '
                            try:
                                username, message_body = line.split(": ", 1)
                            except:
                                username = None

                        if username:
                            if username.strip() == "Server":
                                self.schedule_system(line)
                            else:
                                uname = username.strip()
                                # ensure color exists
                                if uname not in self.user_colors:
                                    self.user_colors[uname] = deterministic_color(uname)
                                # schedule UI update
                                self.schedule_user_message(line, uname, message_body.strip())
                        else:
                            # unknown format -> system
                            self.schedule_system(line)
                    else:
                        # no colon -> system message
                        self.schedule_system(line)
            except Exception:
                break
        self.running = False
        try:
            self.sock.close()
        except:
            pass

    # ---------- sending ----------
    def send_message(self, event=None):
        msg = self.entry.get().strip()
        if not msg:
            return
        try:
            # send only the raw message; server will prepend username
            self.sock.send(msg.encode("utf-8"))
        except Exception:
            self.display_system("Failed to send message. Connection may be closed.")
            self.on_close()
            return

        # display own message instantly
        ts = datetime.now().strftime("[%I:%M %p]")
        self.display_local_user(self.username, msg, ts)
        self.entry.delete(0, tk.END)

        if msg.lower() == "exit":
            # inform server and close
            self.on_close()

    # ---------- UI scheduling helpers (thread-safe) ----------
    def schedule_system(self, text):
        self.master.after(0, lambda: self.display_system(text))

    def schedule_user_message(self, full_line, username, message):
        # extract timestamp from full_line if present
        ts = None
        if full_line.startswith("[") and "]" in full_line:
            try:
                ts = full_line.split("]")[0] + "]"
            except:
                ts = datetime.now().strftime("[%I:%M %p]")
        else:
            ts = datetime.now().strftime("[%I:%M %p]")
        self.master.after(0, lambda: self._display_remote_user(username, message, ts))

    # ---------- UI display functions (main thread) ----------
    def display_system(self, text):
        self.text_area.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("[%I:%M %p]")
        self.text_area.insert(tk.END, f"{timestamp} ", ("timestamp",))
        self.text_area.insert(tk.END, f"{text}\n", ("system",))
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def display_local_user(self, username, message, timestamp):
        self.text_area.config(state=tk.NORMAL)
        # timestamp
        self.text_area.insert(tk.END, f"{timestamp} ", ("timestamp",))
        # username tag already configured for self
        self.text_area.insert(tk.END, f"{username}: ", ("self_name",))
        self.text_area.insert(tk.END, f"{message}\n", ("self_msg",))
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def _display_remote_user(self, username, message, timestamp):
        self.text_area.config(state=tk.NORMAL)
        # timestamp
        self.text_area.insert(tk.END, f"{timestamp} ", ("timestamp",))
        tagname = f"user_{username}"

        # ✅ FIX: check tag existence safely
        existing_tags = self.text_area.tag_names()
        if tagname not in existing_tags:
            self.text_area.tag_config(
                tagname,
                foreground=self.user_colors.get(username, "#DDDDDD"),
                font=("Consolas", 10, "bold")
            )

        self.text_area.insert(tk.END, f"{username}: ", (tagname,))
        self.text_area.insert(tk.END, f"{message}\n", ("other_msg",))
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    # ---------- cleanup ----------
    def on_close(self):
        if self.running:
            try:
                # attempt to inform server of exit
                self.sock.send("exit".encode("utf-8"))
            except:
                pass
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()