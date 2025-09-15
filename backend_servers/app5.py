from flask import Flask, request
import json
import datetime
import os

app = Flask(__name__)
server_id = "Server 5"  # Change this in app2.py, app3.py accordingly
log_file = "../logs/server_logs.json"  # Shared log file
PORT = 5005
REGISTRY_PATH = "../load_balancer_ui/servers.json"
def register_server():
    if not os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'w') as f:
            json.dump({}, f)

    with open(REGISTRY_PATH, 'r+') as f:
        servers = json.load(f)
        if server_id not in servers:
            servers[server_id] = f"http://127.0.0.1:{PORT}"
            f.seek(0)
            json.dump(servers, f, indent=4)
            f.truncate()
            print(f"[INFO] Registered {server_id} on port {PORT}")
@app.route('/')
def home():
    log_request()
    return f"Hello from {server_id}!"

def log_request():
    log_data = {
        "server": server_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "client_ip": request.remote_addr
    }

    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_data)

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=4)

if __name__ == '__main__':
    register_server()
    app.run(host='0.0.0.0', port=PORT)  # Change port for each file
