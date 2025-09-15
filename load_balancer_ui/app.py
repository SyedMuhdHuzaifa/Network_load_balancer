from flask import Flask, render_template, jsonify, request, redirect, url_for
import requests
import json
import os
from collections import Counter
import subprocess
import signal
import threading
import time
from haproxy_switcher import switch_algorithm


app = Flask(__name__)

SERVERS_FILE = 'servers.json'
REQUEST_LOG_FILE = '../logs/server_logs.json'
ALGO_FILE = '../haproxy/current_algorithm.txt'
running_processes = {}
last_message = "No messages yet"



def load_servers():
    if not os.path.exists(SERVERS_FILE):
        return {}
    with open(SERVERS_FILE, 'r') as f:
        return json.load(f)

# Load request counts from shared log
def get_request_counts():
    if not os.path.exists(REQUEST_LOG_FILE):
        return {}
    try:
        with open(REQUEST_LOG_FILE, 'r') as f:
            logs = json.load(f)
        return Counter(log['server'] for log in logs)
    except json.JSONDecodeError:
        return {}


def poll_backend():
    global last_message
    while True:
        try:
            res = requests.get("http://127.0.0.1:8080", timeout=2)
            last_message = res.text
        except Exception as e:
            last_message = "❌ Error contacting HAProxy"
        time.sleep(5)


@app.route('/current-backend')
def current_backend():
    with open("../haproxy/haproxy.cfg", "r") as f:
        for line in f:
            if line.strip().startswith("default_backend"):
                return line.strip().split(" ")[1]
    return "Unknown"


def get_current_algorithm():
    try:
        with open('../haproxy/haproxy.cfg', 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith('default_backend') and not line.startswith('#'):
                    backend = line.split()[1]
                    if backend == 'flask_backends_rr':
                        return "Round Robin"
                    elif backend == 'flask_backends_lc':
                        return "Least Connections"
                    elif backend == 'flask_backends_iphash':
                        return "IP Hashing"
        return "Unknown"
    except Exception as e:
        print(f"Error reading algorithm: {e}")
        return "Unknown"


@app.route('/')
def index():
    servers = load_servers()
    statuses = {}
    ports = {}
    for name, url in servers.items():
        try:
            r = requests.get(url, timeout=1)
            statuses[name] = "🟢 Online" if r.status_code == 200 else "🔴 Error"
            ports[name] = int(url.split(":")[-1])
        except:
            statuses[name] = "🔴 Offline"
            ports[name] = int(url.split(":")[-1])

    counter = get_request_counts()
    algorithm = get_current_algorithm()
    return render_template('index.html', statuses=statuses, counter=counter, algorithm=algorithm, ports=ports)

@app.route('/last_response')
def get_last_message():
    return jsonify({"message": last_message})


@app.route('/set-algorithm/<alg_key>')
def set_algorithm(alg_key):
    mapping = {
        "rr": "Round Robin",
        "lc": "Least Connections",
        "ip": "IP Hashing"
    }

    selected = mapping.get(alg_key)
    if selected and switch_algorithm(selected):
        with open("selected_algorithm.txt", "w") as f:
            f.write(selected)
        return redirect("/")
    return "Failed to switch algorithm", 500


@app.route('/status')
def status():
    servers = load_servers()
    statuses = {}
    for name, url in servers.items():
        try:
            r = requests.get(url, timeout=1)
            statuses[name] = "🟢 Online" if r.status_code == 200 else "🔴 Error"
        except:
            statuses[name] = "🔴 Offline"
    return jsonify(statuses)

@app.route('/counter')
def counter():
    return jsonify(get_request_counts())

@app.route('/logs')
def show_logs():
    try:
        with open('../logs/access.log', 'r') as f:
            lines = f.readlines()[-10:]
        return "<br>".join(lines)
    except FileNotFoundError:
        return "No logs found."

if __name__ == '__main__':
    t = threading.Thread(target=poll_backend)
    t.daemon = True
    t.start()
    app.run(debug=True, port=8000)


