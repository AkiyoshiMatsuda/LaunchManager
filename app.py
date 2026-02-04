from flask import Flask, render_template, redirect, url_for, jsonify
from process_manager import ManagedProcess

app = Flask(__name__)

# =========================
# Managed Projects
# =========================

backend = ManagedProcess(
    name="todo-backend",
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
