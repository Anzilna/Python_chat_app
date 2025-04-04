# run.py
import subprocess
import threading
import os
import time
import sys

def start_server():
    print("Starting server...")
    server_process = subprocess.Popen([sys.executable, "server.py"])
    return server_process

def start_client():
    print("Starting client...")
    client_process = subprocess.Popen([sys.executable, "client.py"])
    return client_process

if __name__ == "__main__":
    # Start the server first
    server = start_server()
    
    # Wait a moment for the server to initialize
    time.sleep(1)
    
    # Start the client
    client = start_client()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.terminate()
        server.terminate()
        print("Done.")