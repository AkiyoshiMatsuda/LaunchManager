import logging
from pathlib import Path

LOG_ROOT = Path("logs")

def get_process_logger(process_name: str) -> logging.Logger:
    log_dir = LOG_ROOT / process_name
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(process_name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # 二重登録防止

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.FileHandler(
        log_dir / "manager.log",
        encoding="utf-8"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
