# # project_config.py
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

#         # cwdの存在チェック（β版では強めにチェックしてOK）
#         cwd_path = Path(cwd)
#         if not cwd_path.exists() or not cwd_path.is_dir():
#             raise ValueError(f"cwd not found or not a directory: {cwd} in {source}")

#         env = data.get("env")
#         if env is not None:
#             if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
#                 raise ValueError(f"env must be dict[str,str] in {source}")

#         auto_start = bool(data.get("auto_start", False))

#         return ProjectConfig(
#             id=pid,
#             name=name,
#             cwd=cwd,
#             command=command,
#             env=env,
#             auto_start=auto_start,
#         )

# project_config.py
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

    @staticmethod
    def from_dict(data: dict[str, Any], *, source: str = "") -> "ProjectConfig":
        # 必須キー
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

        return ProjectConfig(
            id=pid,
            name=name,
            cwd=cwd,
            command=command,
            env=env,
            auto_start=auto_start,
        )
