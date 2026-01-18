from flask import Flask, render_template, redirect, url_for
import subprocess
import socket
import re
import time

def wait_for_port_close(port, host="127.0.0.1", timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        if not is_port_open(port, host):
            return True
        time.sleep(0.2)
    return False


def wait_for_port(port, host="127.0.0.1", timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port, host):
            return True
        time.sleep(0.2)
    return False


def get_pid_by_port(port):
    cmd = f'netstat -ano | findstr :{port}'
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None

    # 最後の列が PID
    match = re.search(r'\s+(\d+)$', result.stdout.strip())
    if match:
        return match.group(1)

    return None

def is_port_open(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

app = Flask(__name__)

@app.route("/")
def index():
    backend_running = is_port_open(8080)
    return render_template(
        "index.html",
        backend_running=backend_running
    )

# @app.route("/start_backend", methods=["POST"])
# def start_backend():
#     subprocess.Popen(
#         ["cmd","/c","go run main.go"],
#         cwd = r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
#     )
#     return redirect(url_for("index"))

@app.route("/start_backend", methods=["POST"])
def start_backend():
    subprocess.Popen(
        ["cmd", "/c", "go run main.go"],
        cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
    )

    # ★ ここがポイント
    wait_for_port(8080, timeout=5)

    return redirect(url_for("index"))


@app.route("/stop_backend", methods=["POST"])
def stop_backend():
    pid = get_pid_by_port(8080)

    if pid:
        subprocess.run(
            ["taskkill", "/PID", pid, "/F"],
            capture_output=True
        )

    return redirect(url_for("index"))

@app.route("/restart_backend", methods=["POST"])
def restart_backend():
    # --- stop ---
    pid = get_pid_by_port(8080)
    if pid:
        subprocess.run(
            ["taskkill", "/PID", pid, "/F"],
            capture_output=True
        )

    # ポートが閉じるまで待つ
    wait_for_port_close(8080, timeout=5)

    # --- start ---
    subprocess.Popen(
        ["cmd", "/c", "go run main.go"],
        cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
    )

    # ポートが開くまで待つ
    wait_for_port(8080, timeout=5)

    return redirect(url_for("index"))


@app.route("/frontend_start", methods=["POST"])
def start_frontend():
    subprocess.Popen(
        ["cmd", "/c", "npm run dev"],
        cwd=r""
    )
    return redirect(url_for("index"))
if __name__ == "__main__":
    app.run(debug=True)