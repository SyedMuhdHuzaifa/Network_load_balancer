import os
import subprocess

HAPROXY_CFG_PATH = "../haproxy/haproxy.cfg"  # Adjust if needed

ALGORITHMS = {
    "Round Robin": "flask_backends_rr",
    "Least Connections": "flask_backends_lc",
    "IP Hashing": "flask_backends_iphash"
}

def switch_algorithm(algorithm_name):
    """
    Replaces DYNAMIC_BACKEND in haproxy.cfg with the selected backend.
    Then reloads HAProxy to apply changes.
    """
    if algorithm_name not in ALGORITHMS:
        print(f"[ERROR] Invalid algorithm: {algorithm_name}")
        return False

    try:
        backend_to_use = ALGORITHMS[algorithm_name]

        # Read current haproxy.cfg
        with open(HAPROXY_CFG_PATH, "r") as file:
            lines = file.readlines()

        # Replace the default_backend line
        updated_lines = []
        for line in lines:
            if line.strip().startswith("default_backend"):
                updated_lines.append(f"    default_backend {backend_to_use}\n")
            else:
                updated_lines.append(line)

        # Write the updated config
        with open(HAPROXY_CFG_PATH, "w") as file:
            file.writelines(updated_lines)

        # Reload HAProxy to apply the new config
        subprocess.run(["sudo", "systemctl", "reload", "haproxy"], check=True)
        print(f"[INFO] Switched to {algorithm_name} → {backend_to_use}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to switch algorithm: {e}")
        return False
