import socket
import threading
import sqlite3
import json
import time
from datetime import datetime

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = {}  # username: (connection, address)
        self.setup_database()
        
    def setup_database(self):
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_seen TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def start(self):
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        try:
            auth_data = client_socket.recv(1024).decode('utf-8')
            auth_info = json.loads(auth_data)
            
            username = auth_info.get('username')
            password = auth_info.get('password')
            action = auth_info.get('action', 'login')
            
            if action == 'register':
                success = self.register_user(username, password)
                if success:
                    self.clients[username] = (client_socket, address)
                    response = {'status': 'success', 'message': 'Registration successful'}
                else:
                    response = {'status': 'error', 'message': 'Username already exists'}
                client_socket.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'login':
                success = self.authenticate_user(username, password)
                if success:
                    self.clients[username] = (client_socket, address)
                    response = {'status': 'success', 'message': 'Login successful'}
                    unread_messages = self.get_unread_messages(username)
                    response['unread_messages'] = unread_messages
                else:
                    response = {'status': 'error', 'message': 'Invalid credentials'}
                client_socket.send(json.dumps(response).encode('utf-8'))
            
            if username in self.clients:
                self.broadcast_active_users()
                
                while True:
                    try:
                        message_data = client_socket.recv(4096).decode('utf-8')
                        if not message_data:
                            break
                        
                        message_obj = json.loads(message_data)
                        
                        if message_obj.get('type') == 'message':
                            receiver = message_obj.get('receiver')
                            content = message_obj.get('content')
                            
                            self.save_message(username, receiver, content)
                            
                            if receiver in self.clients:
                                receiver_socket = self.clients[receiver][0]
                                forward_message = {
                                    'type': 'message',
                                    'sender': username,
                                    'content': content,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                try:
                                    receiver_socket.send(json.dumps(forward_message).encode('utf-8'))
                                except (ConnectionResetError, BrokenPipeError):
                                    print(f"Failed to send message to {receiver} (disconnected)")
                                    
                    except json.JSONDecodeError:
                        continue
                    except (ConnectionResetError, BrokenPipeError):
                        break
                    
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            if username in self.clients:
                del self.clients[username]
                self.update_last_seen(username)
                self.broadcast_active_users()
            client_socket.close()
    
    def register_user(self, username, password):
        try:
            conn = sqlite3.connect('chat_app.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, last_seen) VALUES (?, ?, ?)",
                (username, password, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username, password):
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == password:
            self.update_last_seen(username)
            return True
        return False
    
    def update_last_seen(self, username):
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_seen = ? WHERE username = ?",
               (datetime.now().isoformat(), username))
        conn.commit()
        conn.close()
    
    def save_message(self, sender, receiver, content):
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)",
                      (sender, receiver, content))
        conn.commit()
        conn.close()
    
    def get_unread_messages(self, username):
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, sender, content, timestamp FROM messages 
            WHERE receiver = ? AND is_read = 0
            ORDER BY timestamp
        """, (username,))
        
        messages = []
        for msg_id, sender, content, timestamp in cursor.fetchall():
            messages.append({
                'id': msg_id,
                'sender': sender,
                'content': content,
                'timestamp': timestamp
            })
            cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (msg_id,))
        
        conn.commit()
        conn.close()
        return messages
    
    def broadcast_active_users(self):
        active_users = list(self.clients.keys())
        
        for username, (client_socket, _) in self.clients.items():
            try:
                message = {
                    'type': 'active_users',
                    'users': active_users
                }
                client_socket.send(json.dumps(message).encode('utf-8'))
            except:
                pass


if __name__ == "__main__":
    server = ChatServer()
    server.start()
