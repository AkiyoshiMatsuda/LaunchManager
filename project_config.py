# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any


# @dataclass(frozen=True)
# class ProjectConfig:
#     id: str
#     name: str
#     cwd: str
#     command: list[str]
#     env: dict[str, str] | None = None
#     auto_start: bool = False

#     # ★ 追加：この設定が読み込まれた元ファイルパス（projects/xxx.json）
#     source: str = ""

#     @staticmethod
#     def from_dict(data: dict[str, Any], *, source: str = "") -> "ProjectConfig":
#         # 必須キー
#         required = ["id", "name", "cwd", "command"]
#         missing = [k for k in required if k not in data]
#         if missing:
#             raise ValueError(f"Missing keys {missing} in {source}")

#         pid = str(data["id"]).strip()
#         name = str(data["name"]).strip()
#         cwd = str(data["cwd"]).strip()
#         command = data["command"]

#         if not pid:
#             raise ValueError(f"id is empty in {source}")
#         if not name:
#             raise ValueError(f"name is empty in {source}")

#         if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
#             raise ValueError(f"command must be list[str] in {source}")

#         cwd_path = Path(cwd)
#         if not cwd_path.exists() or not cwd_path.is_dir():
#             raise ValueError(f"cwd not found or not a directory: {cwd} in {source}")

#         env = data.get("env")
#         if env is not None:
#             if not isinstance(env, dict) or not all(
#                 isinstance(k, str) and isinstance(v, str) for k, v in env.items()
#             ):
#                 raise ValueError(f"env must be dict[str,str] in {source}")

#         auto_start = bool(data.get("auto_start", False))

#         return ProjectConfig(
#             id=pid,
#             name=name,
#             cwd=cwd,
#             command=command,
#             env=env,
#             auto_start=auto_start,
#             source=source,  # ★ ここ
#         )

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectConfig:
    id: str
    name: str
    cwd: str
    command: list[str]
    env: dict[str, str] | None = None
    auto_start: bool = False

    # ★ 追加
    wait_port: int | None = None
    startup_timeout_sec: float = 8.0

    @staticmethod
    def from_dict(data: dict[str, Any], *, source: str = "") -> "ProjectConfig":
        required = ["id", "name", "cwd", "command"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing keys {missing} in {source}")

        pid = str(data["id"]).strip()
        name = str(data["name"]).strip()
        cwd = str(data["cwd"]).strip()
        command = data["command"]

        if not pid:
            raise ValueError(f"id is empty in {source}")
        if not name:
            raise ValueError(f"name is empty in {source}")

        if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
            raise ValueError(f"command must be list[str] in {source}")

        cwd_path = Path(cwd)
        if not cwd_path.exists() or not cwd_path.is_dir():
            raise ValueError(f"cwd not found or not a directory: {cwd} in {source}")

        env = data.get("env")
        if env is not None:
            if not isinstance(env, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in env.items()
            ):
                raise ValueError(f"env must be dict[str,str] in {source}")

        auto_start = bool(data.get("auto_start", False))

        # ★ 追加: wait_port / timeout
        wait_port = data.get("wait_port", None)
        if wait_port is not None:
            if not isinstance(wait_port, int) or not (1 <= wait_port <= 65535):
                raise ValueError(f"wait_port must be int(1..65535) in {source}")

        startup_timeout_sec = data.get("startup_timeout_sec", 8.0)
        try:
            startup_timeout_sec = float(startup_timeout_sec)
        except Exception:
            raise ValueError(f"startup_timeout_sec must be number in {source}")

        if startup_timeout_sec <= 0:
            raise ValueError(f"startup_timeout_sec must be > 0 in {source}")

        return ProjectConfig(
            id=pid,
            name=name,
            cwd=cwd,
            command=command,
            env=env,
            auto_start=auto_start,
            wait_port=wait_port,
            startup_timeout_sec=startup_timeout_sec,
        )
