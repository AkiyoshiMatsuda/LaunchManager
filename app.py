# # from flask import Flask, render_template, redirect, url_for, jsonify
# # from process_manager import ManagedProcess
# # from project_loader import load_project_configs

# # app = Flask(__name__)

# # # =========================
# # # Load projects from JSON
# # # =========================

# # configs = load_project_configs("projects")

# # # id -> ManagedProcess
# # processes: dict[str, ManagedProcess] = {}

# # for cfg in configs:
# #     processes[cfg.id] = ManagedProcess(
# #         name=cfg.id,          # logs/{id}/ と一致
# #         command=cfg.command,
# #         cwd=cfg.cwd,
# #         env=cfg.env
# #     )

# # # =========================
# # # Routes
# # # =========================

# # @app.route("/")
# # def index():
# #     projects_view = []

# #     for cfg in configs:
# #         proc = processes.get(cfg.id)
# #         projects_view.append({
# #             "id": cfg.id,
# #             "name": cfg.name,
# #             "status": proc.status if proc else "UNKNOWN",
# #             "pid": proc.pid if proc else None,
# #         })

# #     return render_template("index.html", projects=projects_view)

# # @app.route("/status")
# # def status():
# #     """
# #     JS からポーリングされる状態取得API（複数対応）
# #     """
# #     return jsonify([
# #         {
# #             "id": pid,
# #             "status": proc.status,
# #             "pid": proc.pid
# #         }
# #         for pid, proc in processes.items()
# #     ])


# # @app.route("/start/<project_id>", methods=["POST"])
# # def start_project(project_id):
# #     proc = processes.get(project_id)
# #     if proc:
# #         proc.start()
# #     return redirect(url_for("index"))


# # @app.route("/stop/<project_id>", methods=["POST"])
# # def stop_project(project_id):
# #     proc = processes.get(project_id)
# #     if proc:
# #         proc.stop()
# #     return redirect(url_for("index"))


# # @app.route("/restart/<project_id>", methods=["POST"])
# # def restart_project(project_id):
# #     proc = processes.get(project_id)
# #     if proc:
# #         proc.restart()
# #     return redirect(url_for("index"))


# # if __name__ == "__main__":
# #     app.run(debug=True)

# from flask import Flask, render_template, redirect, url_for, jsonify
# from process_manager import ManagedProcess
# from project_loader import load_project_configs

# app = Flask(__name__)

# # =========================
# # Load projects from JSON
# # =========================

# configs = load_project_configs("projects")

# # id -> ManagedProcess
# processes: dict[str, ManagedProcess] = {}

# for cfg in configs:
#     processes[cfg.id] = ManagedProcess(
#         name=cfg.id,          # logs/{id}/ と一致
#         command=cfg.command,
#         cwd=cfg.cwd,
#         env=cfg.env
#     )

# # =========================
# # Auto Start (safe for debug reloader)
# # =========================

# def _auto_start_projects():
#     """
#     cfg.auto_start == True のものを起動する。
#     Flask debug のリローダーで2重起動しやすいので、
#     "WERKZEUG_RUN_MAIN" を見てメインプロセス側だけで実行する。
#     """
#     for cfg in configs:
#         if getattr(cfg, "auto_start", False):
#             proc = processes.get(cfg.id)
#             if proc:
#                 proc.start()

# # debug=True のとき、Werkzeug はリローダーで2回プロセスを起動する。
# # WERKZEUG_RUN_MAIN == "true" のときが「本体」側。
# # debug=False のときは環境変数が無いのでそのまま起動してOK。
# if (not app.debug) or (True):
#     # app.debug はこの時点だとまだ反映されないことがあるので、環境変数で判定
#     import os
#     if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("FLASK_RUN_FROM_CLI") is None:
#         # 本体側 or 直接 python app.py のとき
#         _auto_start_projects()

# # =========================
# # Routes
# # =========================

# @app.route("/")
# def index():
#     projects_view = []

#     for cfg in configs:
#         proc = processes.get(cfg.id)
#         projects_view.append({
#             "id": cfg.id,
#             "name": cfg.name,
#             "status": proc.status if proc else "UNKNOWN",
#             "pid": proc.pid if proc else None,
#             "error": proc.last_error if proc else None,  # ★ 追加
#         })

#     return render_template("index.html", projects=projects_view)


# @app.route("/status")
# def status():
#     """
#     JS からポーリングされる状態取得API（複数対応）
#     """
#     return jsonify([
#         {
#             "id": pid,
#             "status": proc.status,
#             "pid": proc.pid,
#             "error": proc.last_error,   # ★ 追加
#         }
#         for pid, proc in processes.items()
#     ])


# @app.route("/start/<project_id>", methods=["POST"])
# def start_project(project_id):
#     proc = processes.get(project_id)
#     if proc:
#         proc.start()
#     return redirect(url_for("index"))


# @app.route("/stop/<project_id>", methods=["POST"])
# def stop_project(project_id):
#     proc = processes.get(project_id)
#     if proc:
#         proc.stop()
#     return redirect(url_for("index"))


# @app.route("/restart/<project_id>", methods=["POST"])
# def restart_project(project_id):
#     proc = processes.get(project_id)
#     if proc:
#         proc.restart()
#     return redirect(url_for("index"))


# if __name__ == "__main__":
#     # debug=True のときリローダー2重起動があるので、auto_start は上でガード済み
#     app.run(debug=True)


from flask import Flask, render_template, redirect, url_for, jsonify
from process_manager import ManagedProcess
from project_loader import load_project_configs
import os

app = Flask(__name__)

# =========================
# Load projects from JSON
# =========================

configs = load_project_configs("projects")

processes: dict[str, ManagedProcess] = {}
for cfg in configs:
    processes[cfg.id] = ManagedProcess(
        name=cfg.id,
        command=cfg.command,
        cwd=cfg.cwd,
        env=cfg.env
    )

# =========================
# Auto Start (safe)
# =========================

def auto_start_projects():
    for cfg in configs:
        if getattr(cfg, "auto_start", False):
            proc = processes.get(cfg.id)
            if proc:
                proc.start()

# ★ debugリローダー対策：
# debug=True のときは子プロセス側だけが WERKZEUG_RUN_MAIN=true
# debug=False のときは環境変数が無いので、そのまま実行してOK
def should_autostart_now() -> bool:
    flag = os.environ.get("WERKZEUG_RUN_MAIN")
    if flag is None:
        # debug=False か、リローダー無しの通常起動
        return True
    return flag == "true"

# =========================
# Routes
# =========================

@app.route("/")
def index():
    projects_view = []
    for cfg in configs:
        proc = processes.get(cfg.id)
        projects_view.append({
            "id": cfg.id,
            "name": cfg.name,
            "status": proc.status if proc else "UNKNOWN",
            "pid": proc.pid if proc else None,
            "error": proc.last_error if proc else None,
        })
    return render_template("index.html", projects=projects_view)


@app.route("/status")
def status():
    return jsonify([
        {
            "id": pid,
            "status": proc.status,
            "pid": proc.pid,
            "error": proc.last_error,
        }
        for pid, proc in processes.items()
    ])


@app.route("/start/<project_id>", methods=["POST"])
def start_project(project_id):
    proc = processes.get(project_id)
    if proc:
        proc.start()
    return redirect(url_for("index"))


@app.route("/stop/<project_id>", methods=["POST"])
def stop_project(project_id):
    proc = processes.get(project_id)
    if proc:
        proc.stop()
    return redirect(url_for("index"))


@app.route("/restart/<project_id>", methods=["POST"])
def restart_project(project_id):
    proc = processes.get(project_id)
    if proc:
        proc.restart()
    return redirect(url_for("index"))


if __name__ == "__main__":
    # ★ ここでだけ auto_start する（import時に動かさない）
    if should_autostart_now():
        auto_start_projects()

    app.run(debug=True)
