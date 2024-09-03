import http.server
import socketserver
import json
from threading import Thread
from queue import Queue
from collections import deque
import time

# Global deque to store updates with a maximum size
MAX_UPDATES = 100
update_deque = deque(maxlen=MAX_UPDATES)

class NimbusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('nimbus_ui.html', 'rb') as file:
                self.wfile.write(file.read())
        elif self.path == '/updates':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            updates = list(update_deque)
            self.wfile.write(json.dumps(updates).encode())
        else:
            super().do_GET()

def run_server():
    with socketserver.TCPServer(("", 8000), NimbusHandler) as httpd:
        print("Server running on port 8000")
        httpd.serve_forever()

def start_server():
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

def update_ui(data):
    timestamp = time.time()
    update_deque.append({"timestamp": timestamp, "data": data})

if __name__ == "__main__":
    start_server()