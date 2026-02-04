# # project_registry.py
# import json
# from pathlib import Path

# from project_config import ProjectConfig


# def load_project_configs(projects_dir: str | Path = "projects") -> list[ProjectConfig]:
#     p = Path(projects_dir)
#     if not p.exists():
#         return []

#     configs: list[ProjectConfig] = []
#     for json_path in sorted(p.glob("*.json")):
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         cfg = ProjectConfig.from_dict(data, source=str(json_path))
#         configs.append(cfg)

#     # id重複チェック
#     ids = [c.id for c in configs]
#     dup = {x for x in ids if ids.count(x) > 1}
#     if dup:
#         raise ValueError(f"Duplicate project id found: {sorted(dup)}")

#     return configs

# project_loader.py
import json
from pathlib import Path

from project_config import ProjectConfig


def load_project_configs(projects_dir: str | Path = "projects") -> list[ProjectConfig]:
    p = Path(projects_dir)
    if not p.exists():
        return []

    configs: list[ProjectConfig] = []
    for json_path in sorted(p.glob("*.json")):  # projects/*.json を読む
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cfg = ProjectConfig.from_dict(data, source=str(json_path))
        configs.append(cfg)

    # id 重複チェック
    ids = [c.id for c in configs]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        raise ValueError(f"Duplicate project id found: {sorted(dup)}")

    return configs
