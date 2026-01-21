# # from flask import Flask, render_template, redirect, url_for
# # import subprocess
# # import socket
# # import re
# # import time

# # def wait_for_port_close(port, host="127.0.0.1", timeout=5):
# #     start = time.time()
# #     while time.time() - start < timeout:
# #         if not is_port_open(port, host):
# #             return True
# #         time.sleep(0.2)
# #     return False


# # def wait_for_port(port, host="127.0.0.1", timeout=5):
# #     start = time.time()
# #     while time.time() - start < timeout:
# #         if is_port_open(port, host):
# #             return True
# #         time.sleep(0.2)
# #     return False

# # def get_pid_by_port(port):
# #     cmd = f'netstat -ano | findstr :{port}'
# #     result = subprocess.run(
# #         cmd,
# #         shell=True,
# #         capture_output=True,
# #         text=True
# #     )

# #     if result.returncode != 0:
# #         return None

# #     for line in result.stdout.splitlines():
# #         parts = line.split()

# #         # 期待する形式:
# #         # TCP local foreign STATE PID
# #         if len(parts) < 5:
# #             continue

# #         state = parts[-2]
# #         pid = parts[-1]

# #         # LISTENING のみ対象、PID=0は除外
# #         if state.upper() == "LISTENING" and pid.isdigit() and pid != "0":
# #             return pid

# #     return None


# # def is_port_open(port, host="127.0.0.1"):
# #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
# #         s.settimeout(0.5)
# #         return s.connect_ex((host, port)) == 0

# # app = Flask(__name__)

# # @app.route("/")
# # def index():
# #     backend_running = is_port_open(8080)
# #     return render_template(
# #         "index.html",
# #         backend_running=backend_running
# #     )

# # @app.route("/start_backend", methods=["POST"])
# # def start_backend():
# #     subprocess.Popen(
# #         ["cmd", "/c", "go run main.go"],
# #         cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
# #     )

# #     # ★ ここがポイント
# #     wait_for_port(8080, timeout=5)

# #     return redirect(url_for("index"))

# # @app.route("/stop_backend", methods=["POST"])
# # def stop_backend():
# #     pid = get_pid_by_port(8080)
# #     print("PID:", pid)

# #     if pid:
# #         result = subprocess.run(
# #             ["taskkill", "/PID", pid, "/F"],
# #             capture_output=True,
# #             text=True
# #         )
# #         print("STDOUT:", result.stdout)
# #         print("STDERR:", result.stderr)

# #     return redirect(url_for("index"))


# # @app.route("/restart_backend", methods=["POST"])
# # def restart_backend():
# #     # --- stop ---
# #     pid = get_pid_by_port(8080)
# #     if pid:
# #         subprocess.run(
# #             ["taskkill", "/PID", pid, "/F"],
# #             capture_output=True
# #         )

# #     # ポートが閉じるまで待つ
# #     wait_for_port_close(8080, timeout=5)

# #     # --- start ---
# #     subprocess.Popen(
# #         ["cmd", "/c", "go run main.go"],
# #         cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
# #     )

# #     # ポートが開くまで待つ
# #     wait_for_port(8080, timeout=5)

# #     return redirect(url_for("index"))


# # @app.route("/frontend_start", methods=["POST"])
# # def start_frontend():
# #     subprocess.Popen(
# #         ["cmd", "/c", "npm run dev"],
# #         cwd=r""
# #     )
# #     return redirect(url_for("index"))
# # if __name__ == "__main__":
# #     app.run(debug=True)

# from flask import Flask, render_template, redirect, url_for
# from process_manager import ManagedProcess

# app = Flask(__name__)

# # =========================
# # Managed Projects
# # =========================

# backend = ManagedProcess(
#     name="todo-backend",
#     command=["cmd", "/c", "go run main.go"],
#     cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
# )

# # =========================
# # Routes
# # =========================

# @app.route("/")
# def index():
#     return render_template(
#         "index.html",
#         backend_status=backend.status,
#         backend_pid=backend.pid
#     )

# @app.route("/start_backend", methods=["POST"])
# def start_backend():
#     backend.start()
#     return redirect(url_for("index"))

# @app.route("/stop_backend", methods=["POST"])
# def stop_backend():
#     backend.stop()
#     return redirect(url_for("index"))

# @app.route("/restart_backend", methods=["POST"])
# def restart_backend():
#     backend.restart()
#     return redirect(url_for("index"))


# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask, render_template, redirect, url_for, jsonify
from process_manager import ManagedProcess

app = Flask(__name__)

# =========================
# Managed Projects
# =========================

backend = ManagedProcess(
    name="todo-backend",
    # command=["cmd", "/c", "go run main.go"],
    command=[r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be\todoapp.exe"],
    cwd=r"C:\Users\akiyoshi\Desktop\todoapp\todoapp-be"
)

# =========================
# Routes
# =========================

@app.route("/")
def index():
    # 状態表示は JS がやるので最小限
    return render_template("index.html")


@app.route("/status")
def status():
    """
    JS からポーリングされる状態取得API
    """
    return jsonify({
        "name": backend.name,
        "status": backend.status
    })


@app.route("/start_backend", methods=["POST"])
def start_backend():
    backend.start()
    return redirect(url_for("index"))


@app.route("/stop_backend", methods=["POST"])
def stop_backend():
    backend.stop()
    return redirect(url_for("index"))


@app.route("/restart_backend", methods=["POST"])
def restart_backend():
    backend.restart()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
