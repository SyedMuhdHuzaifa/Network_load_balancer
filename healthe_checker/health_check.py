import time
import requests
import json
import os

CHECK_INTERVAL = 5
SERVERS_FILE = 'servers.json'

def load_servers():
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("❗ Error reading servers.json - invalid JSON format.")
    else:
        print(f"⚠️ {SERVERS_FILE} not found.")
    return []

def check_server_health():
    print("🔍 Starting dynamic health checks using servers.json...")
    while True:
        servers = load_servers()
        if not servers:
            print("⚠️ No servers found to check.")
        for server in servers:
            try:
                r = requests.get(server['url'], timeout=1)
                if r.status_code == 200:
                    print(f"✅ {server['name']} is ONLINE")
                else:
                    print(f"⚠️ {server['name']} is UNREACHABLE (Status: {r.status_code})")
            except requests.exceptions.RequestException:
                print(f"❌ {server['name']} is OFFLINE")
        print("⏱️ Waiting for next check...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    check_server_health()
