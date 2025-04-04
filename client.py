import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import json
from datetime import datetime


class ModernUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Chat App")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Colors and styling
        self.bg_color = "#f0f2f5"
        self.accent_color = "#1877f2"
        self.light_accent = "#e4f0fd"
        self.text_color = "#050505"
        self.secondary_text = "#65676b"
        self.configure(bg=self.bg_color)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TButton', background=self.accent_color, foreground='white', borderwidth=0, font=('Helvetica', 10, 'bold'))
        self.style.map('TButton', background=[('active', '#166fe5')])
        self.style.configure('TEntry', fieldbackground='white', borderwidth=1)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)

        self.current_frame = None
        self.show_login_frame()

        self.client_socket = None
        self.connected = False
        self.username = ""
        self.active_users = []
        self.current_chat = None

    def show_login_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

        login_frame = ttk.Frame(self)
        login_frame.pack(expand=True, fill='both', padx=20, pady=20)

        center_frame = ttk.Frame(login_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        title_label = ttk.Label(center_frame, text="Modern Chat", font=('Helvetica', 24, 'bold'), foreground=self.accent_color)
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        server_frame = ttk.Frame(center_frame)
        server_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky='ew')

        ttk.Label(server_frame, text="Server:").grid(row=0, column=0, padx=(0, 10))
        self.server_entry = ttk.Entry(server_frame, width=15)
        self.server_entry.insert(0, "localhost")
        self.server_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(server_frame, text="Port:").grid(row=0, column=2, padx=(0, 10))
        self.port_entry = ttk.Entry(server_frame, width=6)
        self.port_entry.insert(0, "5555")
        self.port_entry.grid(row=0, column=3)

        ttk.Label(center_frame, text="Username:").grid(row=2, column=0, sticky='w', pady=(0, 10))
        self.username_entry = ttk.Entry(center_frame, width=30)
        self.username_entry.grid(row=2, column=1, pady=(0, 10), padx=(10, 0))

        ttk.Label(center_frame, text="Password:").grid(row=3, column=0, sticky='w', pady=(0, 10))
        self.password_entry = ttk.Entry(center_frame, width=30, show="•")
        self.password_entry.grid(row=3, column=1, pady=(0, 10), padx=(10, 0))

        button_frame = ttk.Frame(center_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

        login_btn = ttk.Button(button_frame, text="Login", command=self.login)
        login_btn.grid(row=0, column=0, padx=(0, 10))

        register_btn = ttk.Button(button_frame, text="Register", command=self.register)
        register_btn.grid(row=0, column=1)

        self.current_frame = login_frame

    def show_chat_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

        chat_frame = ttk.Frame(self)
        chat_frame.pack(expand=True, fill='both')

        paned_window = tk.PanedWindow(chat_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Contacts / users list panel
        contacts_frame = ttk.Frame(paned_window, style='TFrame')
        contacts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        # Add the user listbox here
        self.users_listbox = tk.Listbox(contacts_frame, font=('Helvetica', 10), activestyle='dotbox')
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        paned_window.add(contacts_frame)
        paned_window.paneconfigure(contacts_frame, minsize=200)

        # Main chat area pane
        self.chat_pane = ttk.Frame(paned_window)
        paned_window.add(self.chat_pane)

        self.welcome_label = ttk.Label(
            self.chat_pane,
            text="Select a user to start chatting",
            font=('Helvetica', 14),
            foreground=self.secondary_text
        )
        self.welcome_label.place(relx=0.5, rely=0.5, anchor='center')

        self.current_frame = chat_frame
        self.update_users_list()

    def show_message_area(self, selected_user):
        for widget in self.chat_pane.winfo_children():
            widget.destroy()

        header_frame = ttk.Frame(self.chat_pane, style='TFrame')
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        user_label = ttk.Label(header_frame, text=selected_user, font=('Helvetica', 12, 'bold'), foreground=self.text_color)
        user_label.pack(side=tk.LEFT)

        self.chat_history = scrolledtext.ScrolledText(self.chat_pane, wrap=tk.WORD, bg='white', font=('Helvetica', 10), highlightthickness=0, bd=0)
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        self.chat_history.configure(state='disabled')

        input_frame = ttk.Frame(self.chat_pane)
        input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.message_entry = tk.Text(input_frame, height=3, font=('Helvetica', 10), wrap=tk.WORD, relief=tk.GROOVE, borderwidth=1)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", self.send_message_event)

        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message_btn)
        send_btn.pack(side=tk.RIGHT)

        self.message_entry.focus_set()
        self.load_chat_history(selected_user)

    def connect_to_server(self):
        try:
            host = self.server_entry.get()
            port = int(self.port_entry.get())
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))

            receiver_thread = threading.Thread(target=self.receive_messages)
            receiver_thread.daemon = True
            receiver_thread.start()
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            return False

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return
        if self.connect_to_server():
            auth_data = {'action': 'login', 'username': username, 'password': password}
            self.client_socket.send(json.dumps(auth_data).encode('utf-8'))
            self.username = username

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return
        if self.connect_to_server():
            auth_data = {'action': 'register', 'username': username, 'password': password}
            self.client_socket.send(json.dumps(auth_data).encode('utf-8'))
            self.username = username

    def logout(self):
        if self.client_socket:
            self.client_socket.close()
        self.connected = False
        self.show_login_frame()

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                message = json.loads(data)
                if message.get('status') == 'success':
                    if message.get('message') in ['Login successful', 'Registration successful']:
                        self.connected = True
                        self.after(100, self.show_chat_frame)
                        if 'unread_messages' in message:
                            for msg in message['unread_messages']:
                                self.display_message(msg['sender'], msg['content'], msg['timestamp'], is_self=False)
                elif message.get('status') == 'error':
                    messagebox.showerror("Error", message.get('message', 'Unknown error'))
                elif message.get('type') == 'active_users':
                    self.active_users = message.get('users', [])
                    self.after(100, self.update_users_list)
                elif message.get('type') == 'message':
                    sender = message.get('sender')
                    content = message.get('content')
                    timestamp = message.get('timestamp')
                    if self.current_chat == sender:
                        self.display_message(sender, content, timestamp, is_self=False)
            except json.JSONDecodeError:
                continue
            except ConnectionError:
                messagebox.showerror("Connection Lost", "Lost connection to the server.")
                self.after(100, self.show_login_frame)
                break
            except Exception as e:
                print(f"Error receiving messages: {e}")
                break

    def update_users_list(self):
        if hasattr(self, 'users_listbox'):
            self.users_listbox.delete(0, tk.END)
            for user in self.active_users:
                if user != self.username:
                    self.users_listbox.insert(tk.END, user)

    def on_user_select(self, event):
        if not hasattr(self, 'users_listbox'):
            return
        selection = self.users_listbox.curselection()
        if selection:
            selected_user = self.users_listbox.get(selection[0])
            self.current_chat = selected_user
            self.show_message_area(selected_user)

    def send_message_btn(self):
        if self.current_chat:
            content = self.message_entry.get("1.0", tk.END).strip()
            if content:
                self.send_message(self.current_chat, content)
                self.message_entry.delete("1.0", tk.END)

    def send_message_event(self, event):
        if event.state != 1:
            self.send_message_btn()
            return "break"

    def send_message(self, receiver, content):
        if not self.connected or not self.client_socket:
            messagebox.showerror("Error", "Not connected to server.")
            return
        message = {'type': 'message', 'receiver': receiver, 'content': content}
        try:
            self.client_socket.send(json.dumps(message).encode('utf-8'))
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.display_message(self.username, content, timestamp, is_self=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")

    def display_message(self, sender, content, timestamp, is_self=False):
        if not hasattr(self, 'chat_history'):
            return
        self.chat_history.configure(state='normal')
        display_time = timestamp.split()[1][:5] if isinstance(timestamp, str) else datetime.now().strftime('%H:%M')
        if self.chat_history.index('end-1c') != '1.0':
            self.chat_history.insert(tk.END, '\n')
        tag = "self" if is_self else "other"
        name = "You" if is_self else sender
        self.chat_history.insert(tk.END, f"{name} ({display_time}): ", tag)
        self.chat_history.insert(tk.END, content)
        self.chat_history.tag_configure("self", foreground=self.accent_color, font=('Helvetica', 10, 'bold'))
        self.chat_history.tag_configure("other", foreground="#E91E63", font=('Helvetica', 10, 'bold'))
        self.chat_history.see(tk.END)
        self.chat_history.configure(state='disabled')

    def load_chat_history(self, user):
        self.chat_history.configure(state='normal')
        self.chat_history.delete('1.0', tk.END)
        self.chat_history.insert(tk.END, f"Started chatting with {user}\n")
        self.chat_history.configure(state='disabled')

if __name__ == "__main__":
    app = ModernUI()
    app.mainloop()