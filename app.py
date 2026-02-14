# # from __future__ import annotations

# # from flask import Flask, Response, abort, request,render_template, redirect, url_for, jsonify
# # from process_manager import ManagedProcess
# # from project_loader import load_project_configs
# # from logging_config import get_log_paths
# # from pathlib import Path
# # import json

# # app = Flask(__name__)

# # PROJECTS_DIR = "projects"

# # # =========================
# # # State (in-memory)
# # # =========================

# # configs = []
# # processes: dict[str, ManagedProcess] = {}


# # def rebuild_registry() -> None:
# #     """
# #     projects/*.json を読み直して、
# #     configs と processes を作り直す。
# #     既に起動中のプロセスは可能なら引き継ぐ（同じidなら維持）。
# #     """
# #     global configs, processes

# #     new_configs = load_project_configs(PROJECTS_DIR)

# #     new_processes: dict[str, ManagedProcess] = {}

# #     # 既存のManagedProcessを引き継ぎ
# #     for cfg in new_configs:
# #         old = processes.get(cfg.id)
# #         if old is not None:
# #             # 設定が変わっている可能性があるので反映（cwd/command/env）
# #             old.command = cfg.command
# #             old.cwd = cfg.cwd
# #             old.env = cfg.env
# #             new_processes[cfg.id] = old
# #         else:
# #             new_processes[cfg.id] = ManagedProcess(
# #                 name=cfg.id,
# #                 command=cfg.command,
# #                 cwd=cfg.cwd,
# #                 env=cfg.env
# #             )

# #     configs = new_configs
# #     processes = new_processes


# # def auto_start_projects() -> None:
# #     """
# #     auto_start=true のものを起動
# #     """
# #     for cfg in configs:
# #         if getattr(cfg, "auto_start", False):
# #             proc = processes.get(cfg.id)
# #             if proc:
# #                 proc.start()


# # def find_config(project_id: str):
# #     for cfg in configs:
# #         if cfg.id == project_id:
# #             return cfg
# #     return None


# # def toggle_autostart_in_json(cfg) -> None:
# #     """
# #     cfg.source のJSONを読み書きして auto_start を反転する
# #     """
# #     src = getattr(cfg, "source", "") or ""
# #     if not src:
# #         # sourceが無い場合は fallback で projects/{id}.json を使う
# #         src = str(Path(PROJECTS_DIR) / f"{cfg.id}.json")

# #     path = Path(src)
# #     if not path.exists():
# #         raise FileNotFoundError(f"config json not found: {path}")

# #     with open(path, "r", encoding="utf-8") as f:
# #         data = json.load(f)

# #     current = bool(data.get("auto_start", False))
# #     data["auto_start"] = (not current)

# #     # 見やすく保存（差分も追いやすい）
# #     with open(path, "w", encoding="utf-8") as f:
# #         json.dump(data, f, ensure_ascii=False, indent=2)


# # # 初期ロード
# # rebuild_registry()

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
# #             "error": proc.last_error if proc else None,
# #             "auto_start": bool(getattr(cfg, "auto_start", False)),
# #         })
# #     return render_template("index.html", projects=projects_view)


# # @app.route("/status")
# # def status():
# #     return jsonify([
# #         {
# #             "id": pid,
# #             "status": proc.status,
# #             "pid": proc.pid,
# #             "error": proc.last_error,
# #         }
# #         for pid, proc in processes.items()
# #     ])

# # def tail_lines(path, n: int) -> str:
# #     """
# #     末尾n行を返す（大きいファイルでもそこそこ軽い版）
# #     """
# #     if not path.exists():
# #         return ""

# #     # シンプル実装（βならこれで十分）
# #     with open(path, "r", encoding="utf-8", errors="replace") as f:
# #         lines = f.readlines()
# #     return "".join(lines[-n:])

# # @app.route("/logs/<project_id>/<kind>",methods=["GET"])
# # def get_logs(project_id: str, kind: str):
# #     if project_id not in processes:
# #         abort(404)

# #     if kind not in ("stdout", "stderr", "manager"):
# #         abort(400)

# #     try:
# #         n = int(request.args.get("n", "200"))
# #     except ValueError:
# #         n = 200

# #     n = max(1, min(n, 2000))  # 上限つけとく

# #     paths = get_log_paths(project_id)
# #     text = tail_lines(paths[kind], n)

# #     return Response(text, mimetype="text/plain; charset=utf-8")

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


# # @app.route("/toggle_autostart/<project_id>", methods=["POST"])
# # def toggle_autostart(project_id):
# #     cfg = find_config(project_id)
# #     if not cfg:
# #         return redirect(url_for("index"))

# #     # JSONを反転 → 再ロード
# #     toggle_autostart_in_json(cfg)
# #     rebuild_registry()

# #     return redirect(url_for("index"))


# # if __name__ == "__main__":
# #     # auto_startは起動時に実行
# #     auto_start_projects()

# #     # debugはOK、reloaderは切る（2重起動で同期が壊れるため）
# #     app.run(debug=True, use_reloader=False)

# from __future__ import annotations

# from flask import Flask, Response, abort, request, render_template, redirect, url_for, jsonify
# from process_manager import ManagedProcess
# from project_loader import load_project_configs
# from logging_config import get_log_paths
# from pathlib import Path
# import json

# app = Flask(__name__)

# PROJECTS_DIR = "projects"

# # =========================
# # State (in-memory)
# # =========================

# configs = []
# processes: dict[str, ManagedProcess] = {}


# def rebuild_registry() -> None:
#     """
#     projects/*.json を読み直して、
#     configs と processes を作り直す。
#     既に起動中のプロセスは可能なら引き継ぐ（同じidなら維持）。
#     """
#     global configs, processes

#     new_configs = load_project_configs(PROJECTS_DIR)
#     new_processes: dict[str, ManagedProcess] = {}

#     for cfg in new_configs:
#         old = processes.get(cfg.id)
#         if old is not None:
#             # 設定反映（起動中なら継続して動かす）
#             old.command = cfg.command
#             old.cwd = cfg.cwd
#             old.env = cfg.env

#             # ★ wait_port / timeout も反映（今回の追加ポイント）
#             old.wait_port = getattr(cfg, "wait_port", None)
#             old.startup_timeout_sec = getattr(cfg, "startup_timeout_sec", 8.0)

#             new_processes[cfg.id] = old
#         else:
#             new_processes[cfg.id] = ManagedProcess(
#                 name=cfg.id,
#                 command=cfg.command,
#                 cwd=cfg.cwd,
#                 env=cfg.env,
#                 wait_port=getattr(cfg, "wait_port", None),                 # ★
#                 startup_timeout_sec=getattr(cfg, "startup_timeout_sec", 8.0),  # ★
#             )

#     configs = new_configs
#     processes = new_processes


# def auto_start_projects() -> None:
#     """auto_start=true のものを起動"""
#     for cfg in configs:
#         if getattr(cfg, "auto_start", False):
#             proc = processes.get(cfg.id)
#             if proc:
#                 proc.start()


# def find_config(project_id: str):
#     for cfg in configs:
#         if cfg.id == project_id:
#             return cfg
#     return None


# def toggle_autostart_in_json(cfg) -> None:
#     """
#     cfg.source のJSONを読み書きして auto_start を反転する
#     """
#     src = getattr(cfg, "source", "") or ""
#     if not src:
#         src = str(Path(PROJECTS_DIR) / f"{cfg.id}.json")

#     path = Path(src)
#     if not path.exists():
#         raise FileNotFoundError(f"config json not found: {path}")

#     with open(path, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     current = bool(data.get("auto_start", False))
#     data["auto_start"] = (not current)

#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)


# # 初期ロード
# rebuild_registry()

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
#             "error": proc.last_error if proc else None,

#             "auto_start": bool(getattr(cfg, "auto_start", False)),

#             # ★ 表示に使いたければテンプレで使える
#             "wait_port": getattr(cfg, "wait_port", None),
#             "startup_timeout_sec": getattr(cfg, "startup_timeout_sec", 8.0),
#         })

#     return render_template("index.html", projects=projects_view)


# @app.route("/status")
# def status():
#     # wait_port を入れた ManagedProcess は STARTING→RUNNING が遅れるので
#     # ここはそのままポーリングで追従する
#     return jsonify([
#         {
#             "id": pid,
#             "status": proc.status,
#             "pid": proc.pid,
#             "error": proc.last_error,
#         }
#         for pid, proc in processes.items()
#     ])


# def tail_lines(path: Path, n: int) -> str:
#     """末尾n行を返す（βならreadlinesでOK）"""
#     if not path.exists():
#         return ""
#     with open(path, "r", encoding="utf-8", errors="replace") as f:
#         lines = f.readlines()
#     return "".join(lines[-n:])


# @app.route("/logs/<project_id>/<kind>", methods=["GET"])
# def get_logs(project_id: str, kind: str):
#     if project_id not in processes:
#         abort(404)

#     if kind not in ("stdout", "stderr", "manager"):
#         abort(400)

#     try:
#         n = int(request.args.get("n", "200"))
#     except ValueError:
#         n = 200

#     n = max(1, min(n, 2000))

#     paths = get_log_paths(project_id)
#     text = tail_lines(paths[kind], n)
#     return Response(text, mimetype="text/plain; charset=utf-8")


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


# @app.route("/toggle_autostart/<project_id>", methods=["POST"])
# def toggle_autostart(project_id):
#     cfg = find_config(project_id)
#     if not cfg:
#         return redirect(url_for("index"))

#     toggle_autostart_in_json(cfg)
#     rebuild_registry()
#     return redirect(url_for("index"))


# if __name__ == "__main__":
#     # auto_start は起動時に実行
#     auto_start_projects()

#     # debugはOK、reloaderは切る（2重起動で同期が壊れるため）
#     app.run(debug=True, use_reloader=False)


from __future__ import annotations

from flask import Flask, Response, abort, request, render_template, redirect, url_for, jsonify
from process_manager import ManagedProcess
from project_loader import load_project_configs
from logging_config import get_log_paths
from pathlib import Path
import json
import re

app = Flask(__name__)

PROJECTS_DIR = "projects"

# =========================
# State (in-memory)
# =========================

configs = []
processes: dict[str, ManagedProcess] = {}


def rebuild_registry() -> None:
    global configs, processes

    new_configs = load_project_configs(PROJECTS_DIR)
    new_processes: dict[str, ManagedProcess] = {}

    for cfg in new_configs:
        old = processes.get(cfg.id)
        if old is not None:
            old.command = cfg.command
            old.cwd = cfg.cwd
            old.env = cfg.env
            old.wait_port = getattr(cfg, "wait_port", None)
            old.startup_timeout_sec = getattr(cfg, "startup_timeout_sec", 8.0)
            new_processes[cfg.id] = old
        else:
            new_processes[cfg.id] = ManagedProcess(
                name=cfg.id,
                command=cfg.command,
                cwd=cfg.cwd,
                env=cfg.env,
                wait_port=getattr(cfg, "wait_port", None),
                startup_timeout_sec=getattr(cfg, "startup_timeout_sec", 8.0),
            )

    configs = new_configs
    processes = new_processes


def auto_start_projects() -> None:
    for cfg in configs:
        if getattr(cfg, "auto_start", False):
            proc = processes.get(cfg.id)
            if proc:
                proc.start()


def find_config(project_id: str):
    for cfg in configs:
        if cfg.id == project_id:
            return cfg
    return None


def _project_json_path(project_id: str) -> Path:
    return Path(PROJECTS_DIR) / f"{project_id}.json"


def toggle_autostart_in_json(cfg) -> None:
    src = getattr(cfg, "source", "") or ""
    if not src:
        src = str(_project_json_path(cfg.id))

    path = Path(src)
    if not path.exists():
        raise FileNotFoundError(f"config json not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current = bool(data.get("auto_start", False))
    data["auto_start"] = (not current)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 初期ロード
rebuild_registry()

# =========================
# Helpers (Project Create)
# =========================

_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]{1,63}$")


def parse_command(command_str: str) -> list[str]:
    """
    まずは「スペース区切り」の簡易版。
    将来的に quotes 対応や、list入力UIに拡張する。
    """
    command_str = (command_str or "").strip()
    if not command_str:
        return []
    return command_str.split()


def validate_new_project(form: dict) -> tuple[dict, str | None]:
    """
    formを正規化して dict(json保存用) を返す
    エラーがあれば (form, "error message") を返す
    """
    pid = (form.get("id") or "").strip()
    name = (form.get("name") or "").strip()
    cwd = (form.get("cwd") or "").strip()
    command_str = (form.get("command") or "").strip()

    auto_start = form.get("auto_start") == "on"

    wait_port_raw = (form.get("wait_port") or "").strip()
    timeout_raw = (form.get("startup_timeout_sec") or "").strip()

    if not pid:
        return form, "id is required"
    if not _ID_RE.match(pid):
        return form, "id must be 2-64 chars: [a-zA-Z0-9_-] (start with alnum)"

    if _project_json_path(pid).exists():
        return form, f"project id already exists: {pid}"

    if not name:
        return form, "name is required"
    if not cwd:
        return form, "cwd is required"

    cwd_path = Path(cwd)
    if not cwd_path.exists() or not cwd_path.is_dir():
        return form, f"cwd not found or not a directory: {cwd}"

    cmd = parse_command(command_str)
    if not cmd:
        return form, "command is required"

    wait_port = None
    if wait_port_raw:
        try:
            wait_port = int(wait_port_raw)
            if not (1 <= wait_port <= 65535):
                return form, "wait_port must be 1..65535"
        except ValueError:
            return form, "wait_port must be integer"

    startup_timeout_sec = 8.0
    if timeout_raw:
        try:
            startup_timeout_sec = float(timeout_raw)
            if startup_timeout_sec <= 0:
                return form, "startup_timeout_sec must be > 0"
        except ValueError:
            return form, "startup_timeout_sec must be number"

    payload = {
        "id": pid,
        "name": name,
        "cwd": cwd,
        "command": cmd,
        "auto_start": auto_start,
        "wait_port": wait_port,
        "startup_timeout_sec": startup_timeout_sec,
    }

    # JSONから None は消して見た目をきれいにする（後で差分も追いやすい）
    payload = {k: v for k, v in payload.items() if v is not None}

    return payload, None


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
            "auto_start": bool(getattr(cfg, "auto_start", False)),
        })
    return render_template("index.html", projects=projects_view)


@app.route("/projects/new", methods=["GET", "POST"])
def projects_new():
    if request.method == "GET":
        # 初期値
        form = {"startup_timeout_sec": "8", "auto_start": False}
        return render_template("projects_new.html", form=form, error=None)

    # POST
    raw_form = {
        "id": request.form.get("id", ""),
        "name": request.form.get("name", ""),
        "cwd": request.form.get("cwd", ""),
        "command": request.form.get("command", ""),
        "wait_port": request.form.get("wait_port", ""),
        "startup_timeout_sec": request.form.get("startup_timeout_sec", ""),
        "auto_start": request.form.get("auto_start", None),
    }

    payload, err = validate_new_project(raw_form)
    if err:
        # 入力保持して戻す
        form = dict(raw_form)
        form["auto_start"] = (raw_form.get("auto_start") == "on")
        return render_template("projects_new.html", form=form, error=err), 400

    # 保存
    projects_dir = Path(PROJECTS_DIR)
    projects_dir.mkdir(parents=True, exist_ok=True)

    path = _project_json_path(payload["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 即反映
    rebuild_registry()

    # auto_start=trueならここで起動するか？は将来設定にする。
    # いまは「作ったら一覧へ戻る」にする（UXが読みやすい）
    return redirect(url_for("index"))


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


def tail_lines(path: Path, n: int) -> str:
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-n:])


@app.route("/logs/<project_id>/<kind>", methods=["GET"])
def get_logs(project_id: str, kind: str):
    if project_id not in processes:
        abort(404)

    if kind not in ("stdout", "stderr", "manager"):
        abort(400)

    try:
        n = int(request.args.get("n", "200"))
    except ValueError:
        n = 200

    n = max(1, min(n, 2000))

    paths = get_log_paths(project_id)
    text = tail_lines(paths[kind], n)
    return Response(text, mimetype="text/plain; charset=utf-8")


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


@app.route("/toggle_autostart/<project_id>", methods=["POST"])
def toggle_autostart(project_id):
    cfg = find_config(project_id)
    if not cfg:
        return redirect(url_for("index"))

    toggle_autostart_in_json(cfg)
    rebuild_registry()
    return redirect(url_for("index"))


if __name__ == "__main__":
    auto_start_projects()
    app.run(debug=True, use_reloader=False)
