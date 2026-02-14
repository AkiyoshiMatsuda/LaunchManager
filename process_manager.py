# # # import subprocess
# # # import threading
# # # import time
# # # from pathlib import Path
# # # from logging_config import get_process_logger


# # # class ManagedProcess:
# # #     def __init__(self, name, command, cwd, env=None):
# # #         """
# # #         name: ログ識別子（logs/{name}/ など）
# # #         command: list[str] 推奨（例: ["todoapp.exe"] / ["go","run","main.go"]）
# # #         cwd: 作業ディレクトリ（プロジェクトルート）
# # #         env: dict[str,str] or None
# # #         """
# # #         self.name = name
# # #         self.command = command
# # #         self.cwd = cwd
# # #         self.env = env

# # #         self.proc = None
# # #         self.status = "STOPPED"   # STOPPED / STARTING / RUNNING / STOPPING / ERROR
# # #         self.last_error = None    # ★ 追加：直近エラー内容
# # #         self.lock = threading.Lock()

# # #         self.logger = get_process_logger(name)

# # #     # =========================
# # #     # Process Control
# # #     # =========================

# # #     def start(self):
# # #         with self.lock:
# # #             if self.proc and self.proc.poll() is None:
# # #                 self.logger.warning("START ignored (already running)")
# # #                 return

# # #             self.logger.info("START requested")
# # #             self.status = "STARTING"
# # #             self.last_error = None

# # #             # command[0] を cwd 基準で解決
# # #             cmd = self._resolve_command(self.command)

# # #             try:
# # #                 self.proc = subprocess.Popen(
# # #                     cmd,
# # #                     cwd=self.cwd,
# # #                     env=self.env,
# # #                     stdout=subprocess.PIPE,
# # #                     stderr=subprocess.PIPE,
# # #                     text=True,
# # #                     bufsize=1
# # #                 )
# # #             except FileNotFoundError as e:
# # #                 # exe/コマンドが見つからない
# # #                 self.status = "ERROR"
# # #                 self.last_error = f"FileNotFoundError: {e}"
# # #                 self.logger.exception(
# # #                     "START failed (FileNotFoundError): cmd=%s cwd=%s",
# # #                     cmd, self.cwd
# # #                 )
# # #                 self.proc = None
# # #                 return
# # #             except Exception as e:
# # #                 # その他の起動失敗
# # #                 self.status = "ERROR"
# # #                 self.last_error = f"{type(e).__name__}: {e}"
# # #                 self.logger.exception(
# # #                     "START failed (Unexpected): cmd=%s cwd=%s",
# # #                     cmd, self.cwd
# # #                 )
# # #                 self.proc = None
# # #                 return

# # #             # 起動監視
# # #             threading.Thread(target=self._watch, daemon=True).start()

# # #             # stdout / stderr ログ取り
# # #             if self.proc.stdout:
# # #                 threading.Thread(
# # #                     target=self._pipe_logger,
# # #                     args=(self.proc.stdout, "STDOUT"),
# # #                     daemon=True
# # #                 ).start()

# # #             if self.proc.stderr:
# # #                 threading.Thread(
# # #                     target=self._pipe_logger,
# # #                     args=(self.proc.stderr, "STDERR"),
# # #                     daemon=True
# # #                 ).start()

# # #     def stop(self):
# # #         with self.lock:
# # #             if not self.proc or self.proc.poll() is not None:
# # #                 self.logger.warning("STOP ignored (not running)")
# # #                 self.status = "STOPPED"
# # #                 return

# # #             self.logger.info("STOP requested")
# # #             self.status = "STOPPING"

# # #             self.proc.terminate()

# # #             try:
# # #                 self.proc.wait(timeout=5)
# # #                 self.logger.info("Process terminated gracefully")
# # #             except subprocess.TimeoutExpired:
# # #                 self.logger.error("FORCE KILL")
# # #                 self.proc.kill()
# # #                 self.proc.wait()

# # #             self.proc = None
# # #             self.status = "STOPPED"
# # #             self.last_error = None
# # #             self.logger.info("STOPPED")

# # #     def restart(self):
# # #         self.logger.info("RESTART requested")
# # #         self.stop()
# # #         self.start()

# # #     # =========================
# # #     # Internal
# # #     # =========================

# # #     def _resolve_command(self, command):
# # #         """
# # #         command[0] を cwd 基準で絶対パス化する（Windows対策）
# # #         """
# # #         if command is None:
# # #             return command

# # #         if isinstance(command, str):
# # #             return command

# # #         if not isinstance(command, (list, tuple)) or len(command) == 0:
# # #             return command

# # #         cmd = list(command)
# # #         exe = cmd[0]

# # #         if not isinstance(exe, str) or exe.strip() == "":
# # #             return cmd

# # #         exe = exe.strip()

# # #         # すでにパス指定ならそのまま
# # #         if "/" in exe or "\\" in exe:
# # #             return cmd

# # #         candidate = Path(self.cwd) / exe
# # #         if candidate.exists():
# # #             cmd[0] = str(candidate)
# # #             self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
# # #         else:
# # #             self.logger.warning(
# # #                 "Executable not found in cwd: %s (cwd=%s). Will try PATH.",
# # #                 exe, self.cwd
# # #             )

# # #         return cmd

# # #     def _watch(self):
# # #         time.sleep(1)

# # #         if not self.proc:
# # #             return

# # #         if self.proc.poll() is None:
# # #             self.status = "RUNNING"
# # #             self.logger.info("RUNNING (pid=%s)", self.proc.pid)
# # #             self.proc.wait()

# # #         self.proc = None
# # #         self.status = "STOPPED"
# # #         self.logger.info("PROCESS EXITED")

# # #     def _pipe_logger(self, pipe, label):
# # #         try:
# # #             for line in pipe:
# # #                 self.logger.info("%s | %s", label, line.rstrip())
# # #         except Exception as e:
# # #             self.logger.exception("Pipe logger error (%s): %s", label, e)

# # #     # =========================
# # #     # Info
# # #     # =========================

# # #     @property
# # #     def pid(self):
# # #         if self.proc and self.proc.poll() is None:
# # #             return self.proc.pid
# # #         return None

# # import subprocess
# # import threading
# # import time
# # from pathlib import Path
# # from logging_config import get_process_logger


# # class ManagedProcess:
# #     def __init__(self, name, command, cwd, env=None):
# #         """
# #         name: ログ識別子（logs/{name}/ など）
# #         command: list[str] 推奨（例: ["todoapp.exe"] / ["go","run","main.go"]）
# #         cwd: 作業ディレクトリ（プロジェクトルート）
# #         env: dict[str,str] or None
# #         """
# #         self.name = name
# #         self.command = command
# #         self.cwd = cwd
# #         self.env = env

# #         self.proc = None
# #         self.status = "STOPPED"   # STOPPED / STARTING / RUNNING / STOPPING / ERROR
# #         self.last_error = None    # 直近エラー内容
# #         self.lock = threading.Lock()

# #         self.logger = get_process_logger(name)

# #     # =========================
# #     # Process Control
# #     # =========================

# #     def start(self):
# #         with self.lock:
# #             if self.proc and self.proc.poll() is None:
# #                 self.logger.warning("START ignored (already running)")
# #                 return

# #             self.logger.info("START requested")
# #             self.status = "STARTING"
# #             self.last_error = None

# #             cmd = self._resolve_command(self.command)

# #             try:
# #                 self.proc = subprocess.Popen(
# #                     cmd,
# #                     cwd=self.cwd,
# #                     env=self.env,
# #                     stdout=subprocess.PIPE,
# #                     stderr=subprocess.PIPE,
# #                     text=True,
# #                     bufsize=1
# #                 )
# #             except FileNotFoundError as e:
# #                 self.status = "ERROR"
# #                 self.last_error = f"FileNotFoundError: {e}"
# #                 self.logger.exception(
# #                     "START failed (FileNotFoundError): cmd=%s cwd=%s",
# #                     cmd, self.cwd
# #                 )
# #                 self.proc = None
# #                 return
# #             except Exception as e:
# #                 self.status = "ERROR"
# #                 self.last_error = f"{type(e).__name__}: {e}"
# #                 self.logger.exception(
# #                     "START failed (Unexpected): cmd=%s cwd=%s",
# #                     cmd, self.cwd
# #                 )
# #                 self.proc = None
# #                 return

# #             threading.Thread(target=self._watch, daemon=True).start()

# #             if self.proc.stdout:
# #                 threading.Thread(
# #                     target=self._pipe_logger,
# #                     args=(self.proc.stdout, "STDOUT"),
# #                     daemon=True
# #                 ).start()

# #             if self.proc.stderr:
# #                 threading.Thread(
# #                     target=self._pipe_logger,
# #                     args=(self.proc.stderr, "STDERR"),
# #                     daemon=True
# #                 ).start()

# #     def stop(self):
# #         with self.lock:
# #             if not self.proc or self.proc.poll() is not None:
# #                 self.logger.warning("STOP ignored (not running)")
# #                 # ERROR中でも stop で STOPPED に戻せるようにする
# #                 self.status = "STOPPED"
# #                 self.proc = None
# #                 self.last_error = None
# #                 return

# #             self.logger.info("STOP requested")
# #             self.status = "STOPPING"

# #             try:
# #                 self.proc.terminate()
# #             except Exception as e:
# #                 # terminate 自体が失敗したら強制終了へ
# #                 self.logger.exception("terminate() failed: %s", e)

# #             try:
# #                 self.proc.wait(timeout=5)
# #                 self.logger.info("Process terminated gracefully")
# #             except subprocess.TimeoutExpired:
# #                 self.logger.error("FORCE KILL")
# #                 try:
# #                     self.proc.kill()
# #                 except Exception as e:
# #                     self.logger.exception("kill() failed: %s", e)
# #                 self.proc.wait()

# #             self.proc = None
# #             self.status = "STOPPED"
# #             self.last_error = None
# #             self.logger.info("STOPPED")

# #     def restart(self):
# #         self.logger.info("RESTART requested")
# #         self.stop()
# #         self.start()

# #     # =========================
# #     # Internal
# #     # =========================

# #     def _resolve_command(self, command):
# #         """
# #         command[0] を cwd 基準で絶対パス化する（Windows対策）
# #         """
# #         if command is None:
# #             return command

# #         if isinstance(command, str):
# #             return command

# #         if not isinstance(command, (list, tuple)) or len(command) == 0:
# #             return command

# #         cmd = list(command)
# #         exe = cmd[0]

# #         if not isinstance(exe, str) or exe.strip() == "":
# #             return cmd

# #         exe = exe.strip()

# #         # すでにパス指定ならそのまま
# #         if "/" in exe or "\\" in exe:
# #             return cmd

# #         candidate = Path(self.cwd) / exe
# #         if candidate.exists():
# #             cmd[0] = str(candidate)
# #             self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
# #         else:
# #             self.logger.warning(
# #                 "Executable not found in cwd: %s (cwd=%s). Will try PATH.",
# #                 exe, self.cwd
# #             )

# #         return cmd

# #     def _watch(self):
# #         time.sleep(1)

# #         # start() が失敗して proc が None の可能性
# #         if not self.proc:
# #             # status は start() 側で ERROR/STOPPED をセットしているので触らない
# #             return

# #         if self.proc.poll() is None:
# #             self.status = "RUNNING"
# #             self.logger.info("RUNNING (pid=%s)", self.proc.pid)
# #             self.proc.wait()

# #         # プロセス終了
# #         self.proc = None

# #         # すでに ERROR 判定されていたら STOPPED で上書きしない
# #         if self.status != "ERROR":
# #             self.status = "STOPPED"

# #         self.logger.info("PROCESS EXITED (final_status=%s)", self.status)

# #     def _pipe_logger(self, pipe, label):
# #         try:
# #             for raw_line in pipe:
# #                 line = raw_line.rstrip("\n")
# #                 if line.endswith("\r"):
# #                     line = line[:-1]

# #                 # ログ出力（STDOUT/STDERR は manager.log に集約）
# #                 self.logger.info("%s | %s", label, line)

# #                 # =========================
# #                 # ERROR検知（ここが今回の核心）
# #                 # =========================
# #                 lower = line.lower()

# #                 is_error_hint = (
# #                     "error" in lower
# #                     or "panic" in lower
# #                     or "exception" in lower
# #                     or "fatal" in lower
# #                 )

# #                 # STDERR は原則「異常寄り」なので、空行以外はエラー候補にする
# #                 is_stderr_signal = (label == "STDERR" and line.strip() != "")

# #                 if is_error_hint or is_stderr_signal:
# #                     # 競合防止：STOPPING中はエラー扱いにしない（停止中の stderr が紛れることがある）
# #                     if self.status != "STOPPING":
# #                         self.last_error = line
# #                         self.status = "ERROR"
# #                         self.logger.warning("ERROR detected (label=%s): %s", label, line)

# #         except Exception as e:
# #             self.logger.exception("Pipe logger error (%s): %s", label, e)

# #     # =========================
# #     # Info
# #     # =========================

# #     @property
# #     def pid(self):
# #         if self.proc and self.proc.poll() is None:
# #             return self.proc.pid
# #         return None


# import subprocess
# import threading
# import time
# import socket
# from pathlib import Path
# from logging_config import get_process_logger


# class ManagedProcess:
#     def __init__(self, name, command, cwd, env=None, wait_port=None, startup_timeout_sec=8.0):
#         """
#         wait_port: 起動完了判定に使うポート（Noneなら待たない）
#         startup_timeout_sec: 起動完了待ちのタイムアウト秒
#         """
#         self.name = name
#         self.command = command
#         self.cwd = cwd
#         self.env = env

#         self.wait_port = wait_port
#         self.startup_timeout_sec = float(startup_timeout_sec)

#         self.proc = None
#         self.status = "STOPPED"   # STOPPED / STARTING / RUNNING / STOPPING / ERROR
#         self.last_error = None
#         self.lock = threading.Lock()

#         self.logger = get_process_logger(name)

#         # start() の世代管理（連打やrestartで古い監視が状態を上書きしないため）
#         self._start_gen = 0

#     # =========================
#     # Process Control
#     # =========================

#     def start(self):
#         with self.lock:
#             if self.proc and self.proc.poll() is None:
#                 self.logger.warning("START ignored (already running)")
#                 return

#             self._start_gen += 1
#             gen = self._start_gen

#             self.logger.info("START requested (gen=%s)", gen)
#             self.status = "STARTING"
#             self.last_error = None

#             cmd = self._resolve_command(self.command)

#             try:
#                 self.proc = subprocess.Popen(
#                     cmd,
#                     cwd=self.cwd,
#                     env=self.env,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     text=True,
#                     encoding="utf-8",
#                     errors="replace",
#                     bufsize=1
#                 )
#             except FileNotFoundError as e:
#                 self.status = "ERROR"
#                 self.last_error = f"FileNotFoundError: {e}"
#                 self.logger.exception("START failed (FileNotFoundError): cmd=%s cwd=%s", cmd, self.cwd)
#                 self.proc = None
#                 return
#             except Exception as e:
#                 self.status = "ERROR"
#                 self.last_error = f"{type(e).__name__}: {e}"
#                 self.logger.exception("START failed (Unexpected): cmd=%s cwd=%s", cmd, self.cwd)
#                 self.proc = None
#                 return

#             # 起動監視（プロセス終了検知）
#             threading.Thread(target=self._watch, args=(gen,), daemon=True).start()

#             # stdout / stderr ログ取り
#             if self.proc.stdout:
#                 threading.Thread(target=self._pipe_logger, args=(self.proc.stdout, "STDOUT", gen), daemon=True).start()
#             if self.proc.stderr:
#                 threading.Thread(target=self._pipe_logger, args=(self.proc.stderr, "STDERR", gen), daemon=True).start()

#             # ★ 起動完了判定（wait_portがある場合）
#             if self.wait_port is not None:
#                 threading.Thread(target=self._wait_startup, args=(gen,), daemon=True).start()
#             else:
#                 # wait_portが無いなら「プロセスが生きてる＝RUNNING」扱い
#                 self.status = "RUNNING"

#     def stop(self):
#         with self.lock:
#             # stop() した時点で世代を進める（古い監視が上書きしない）
#             self._start_gen += 1

#             if not self.proc or self.proc.poll() is not None:
#                 self.logger.warning("STOP ignored (not running)")
#                 self.status = "STOPPED"
#                 self.proc = None
#                 self.last_error = None
#                 return

#             self.logger.info("STOP requested")
#             self.status = "STOPPING"

#             try:
#                 self.proc.terminate()
#             except Exception as e:
#                 self.logger.exception("terminate() failed: %s", e)

#             try:
#                 self.proc.wait(timeout=5)
#                 self.logger.info("Process terminated gracefully")
#             except subprocess.TimeoutExpired:
#                 self.logger.error("FORCE KILL")
#                 try:
#                     self.proc.kill()
#                 except Exception as e:
#                     self.logger.exception("kill() failed: %s", e)
#                 self.proc.wait()

#             self.proc = None
#             self.status = "STOPPED"
#             self.last_error = None
#             self.logger.info("STOPPED")

#     def restart(self):
#         self.logger.info("RESTART requested")
#         self.stop()
#         self.start()

#     # =========================
#     # Internal
#     # =========================

#     def _resolve_command(self, command):
#         if command is None:
#             return command
#         if isinstance(command, str):
#             return command
#         if not isinstance(command, (list, tuple)) or len(command) == 0:
#             return command

#         cmd = list(command)
#         exe = cmd[0]
#         if not isinstance(exe, str) or exe.strip() == "":
#             return cmd

#         exe = exe.strip()

#         if "/" in exe or "\\" in exe:
#             return cmd

#         candidate = Path(self.cwd) / exe
#         if candidate.exists():
#             cmd[0] = str(candidate)
#             self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
#         else:
#             self.logger.warning("Executable not found in cwd: %s (cwd=%s). Will try PATH.", exe, self.cwd)

#         return cmd

#     def _is_port_open(self, host: str, port: int) -> bool:
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.settimeout(0.3)
#                 return s.connect_ex((host, port)) == 0
#         except Exception:
#             return False

#     def _wait_startup(self, gen: int):
#         """STARTING -> (ポートOpen) -> RUNNING / (timeout) -> ERROR"""
#         port = int(self.wait_port)
#         timeout = float(self.startup_timeout_sec)
#         host = "127.0.0.1"

#         self.logger.info("Startup wait begin: port=%s timeout=%ss (gen=%s)", port, timeout, gen)

#         start = time.time()
#         while time.time() - start < timeout:
#             # 世代が変わっていたら監視終了
#             if gen != self._start_gen:
#                 return

#             # プロセスが死んでたら失敗
#             if not self.proc or self.proc.poll() is not None:
#                 if self.status != "ERROR":
#                     self.status = "ERROR"
#                     self.last_error = "Process exited during startup wait"
#                 self.logger.warning("Startup failed: process exited (gen=%s)", gen)
#                 return

#             if self._is_port_open(host, port):
#                 # まだERRORじゃないならRUNNINGへ
#                 if self.status != "ERROR":
#                     self.status = "RUNNING"
#                 self.logger.info("Startup success: port opened (port=%s gen=%s)", port, gen)
#                 return

#             time.sleep(0.2)

#         # timeout
#         if gen == self._start_gen and self.status != "ERROR":
#             self.status = "ERROR"
#             self.last_error = f"Startup timeout: port {port} did not open within {timeout}s"
#             self.logger.warning("Startup timeout (port=%s timeout=%ss gen=%s)", port, timeout, gen)

#     def _watch(self, gen: int):
#         time.sleep(0.5)

#         if not self.proc:
#             return

#         if self.proc.poll() is None:
#             self.logger.info("PROCESS alive (pid=%s gen=%s)", self.proc.pid, gen)
#             self.proc.wait()

#         # 終了した
#         self.proc = None

#         # 世代が一致していて、ERRORじゃなければSTOPPEDへ
#         if gen == self._start_gen and self.status != "ERROR":
#             self.status = "STOPPED"

#         self.logger.info("PROCESS EXITED (final_status=%s gen=%s)", self.status, gen)

#     def _pipe_logger(self, pipe, label, gen: int):
#         try:
#             for raw_line in pipe:
#                 # 世代が変わったら終了（古いプロセスのログで上書きしない）
#                 if gen != self._start_gen:
#                     return

#                 line = raw_line.rstrip("\n")
#                 if line.endswith("\r"):
#                     line = line[:-1]

#                 self.logger.info("%s | %s", label, line)

#                 lower = line.lower()
#                 is_error_hint = ("error" in lower) or ("panic" in lower) or ("exception" in lower) or ("fatal" in lower)
#                 is_stderr_signal = (label == "STDERR" and line.strip() != "")

#                 if (is_error_hint or is_stderr_signal) and self.status != "STOPPING":
#                     self.last_error = line
#                     self.status = "ERROR"
#                     self.logger.warning("ERROR detected (label=%s): %s", label, line)

#         except Exception as e:
#             self.logger.exception("Pipe logger error (%s): %s", label, e)

#     # =========================
#     # Info
#     # =========================

#     @property
#     def pid(self):
#         if self.proc and self.proc.poll() is None:
#             return self.proc.pid
#         return None

import os
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from logging_config import get_process_logger


# 「致命的」になりやすいワード（言語/ツール混在でもある程度効く）
FATAL_PATTERNS = [
    re.compile(r"\bEADDRINUSE\b", re.IGNORECASE),
    re.compile(r"address already in use", re.IGNORECASE),
    re.compile(r"port.*already.*in use", re.IGNORECASE),
    re.compile(r"bind\(\).*failed", re.IGNORECASE),
    re.compile(r"failed to listen", re.IGNORECASE),
    re.compile(r"cannot\s+bind", re.IGNORECASE),
    re.compile(r"permission denied", re.IGNORECASE),
]


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


class ManagedProcess:
    """
    Status:
      STOPPED / STARTING / RUNNING / STOPPING / ERROR
    """

    def __init__(
        self,
        name: str,
        command,
        cwd: str,
        env=None,
        wait_port: int | None = None,
        startup_timeout_sec: float = 8.0,
    ):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env

        # healthcheck
        self.wait_port = wait_port
        self.startup_timeout_sec = float(startup_timeout_sec) if startup_timeout_sec else 8.0

        self.proc: subprocess.Popen | None = None
        self.status = "STOPPED"
        self.last_error: str | None = None

        self.lock = threading.Lock()
        self.logger = get_process_logger(name)

        # 世代管理（古いスレッドが新しい起動を上書きしない）
        self._gen = 0

    # =========================
    # Public
    # =========================

    def start(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self.logger.warning("START ignored (already running)")
                return

            self._gen += 1
            gen = self._gen

            self.logger.info("START requested (gen=%s)", gen)
            self.status = "STARTING"
            self.last_error = None

            cmd = self._resolve_command(self.command)

            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
            except FileNotFoundError as e:
                self.proc = None
                self.status = "ERROR"
                self.last_error = f"FileNotFoundError: {e}"
                self.logger.exception("START failed (FileNotFoundError): cmd=%s cwd=%s", cmd, self.cwd)
                return
            except Exception as e:
                self.proc = None
                self.status = "ERROR"
                self.last_error = f"{type(e).__name__}: {e}"
                self.logger.exception("START failed (Unexpected): cmd=%s cwd=%s", cmd, self.cwd)
                return

            # 出力ログ取り（stderrでも即ERRORにしない）
            if self.proc.stdout:
                threading.Thread(target=self._pipe_logger, args=(self.proc.stdout, "STDOUT", gen), daemon=True).start()
            if self.proc.stderr:
                threading.Thread(target=self._pipe_logger, args=(self.proc.stderr, "STDERR", gen), daemon=True).start()

            # 終了監視（exit codeでERROR判定）
            threading.Thread(target=self._watch_exit, args=(gen,), daemon=True).start()

            # healthcheck（指定がある場合のみ：これが「起動成功」の根拠）
            if self.wait_port:
                threading.Thread(target=self._wait_health, args=(self.wait_port, gen), daemon=True).start()
            else:
                # ポート待ちがない場合は「プロセスが生きてる」＝RUNNING とみなす
                # （ただし直後に落ちたら _watch_exit が ERROR/STOPPED にする）
                self._set_status_if_current(gen, "RUNNING")
                self.logger.info("PROCESS alive (pid=%s gen=%s)", self.proc.pid if self.proc else None, gen)

    # def stop(self):
    #     with self.lock:
    #         if not self.proc or self.proc.poll() is not None:
    #             self.status = "STOPPED"
    #             self.logger.warning("STOP ignored (not running)")
    #             self.proc = None
    #             return

    #         self._gen += 1
    #         gen = self._gen

    #         self.logger.info("STOP requested (gen=%s)", gen)
    #         self.status = "STOPPING"

    #         p = self.proc
    #         try:
    #             p.terminate()
    #             try:
    #                 p.wait(timeout=5)
    #                 self.logger.info("Process terminated gracefully")
    #             except subprocess.TimeoutExpired:
    #                 self.logger.warning("FORCE KILL")
    #                 p.kill()
    #                 p.wait(timeout=5)
    #         finally:
    #             self.proc = None
    #             self.status = "STOPPED"
    #             self.last_error = None
    #             self.logger.info("STOPPED")
    def stop(self):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                self.logger.warning("STOP ignored (not running)")
                self.status = "STOPPED"
                self.proc = None
                return

            self._gen += 1
            gen = self._gen

            self.logger.info("STOP requested (gen=%s)", gen)
            self.status = "STOPPING"

            p = self.proc
            pid = p.pid

            try:
                if os.name == "nt":
                    # ★ Windows: 子プロセス含めてツリーごと終了
                    self.logger.info("taskkill /PID %s /T /F", pid)
                    r = subprocess.run(
                        ["taskkill", "/PID", str(pid), "/T", "/F"],
                        capture_output=True,
                        text=True,
                    )
                    if r.returncode != 0:
                        self.logger.warning("taskkill failed rc=%s stdout=%s stderr=%s", r.returncode, r.stdout, r.stderr)
                else:
                    # 非Windowsは通常 terminate → kill fallback
                    p.terminate()
                    try:
                        p.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=5)

            finally:
                self.proc = None
                self.status = "STOPPED"
                self.last_error = None
                self.logger.info("STOPPED")
    def restart(self):
        self.logger.info("RESTART requested")
        self.stop()
        self.start()

    @property
    def pid(self):
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        return None

    # =========================
    # Internal
    # =========================

    def _resolve_command(self, command):
        """
        Windowsで npm/npx/pnpm/yarn などを確実に起動できるように補強。
        """
        if command is None:
            return command

        if isinstance(command, str):
            return command

        if not isinstance(command, (list, tuple)) or len(command) == 0:
            return command

        cmd = list(command)
        exe = cmd[0]

        if not isinstance(exe, str) or exe.strip() == "":
            return cmd

        exe = exe.strip()

        # すでにパス指定ならそのまま
        if "/" in exe or "\\" in exe:
            return cmd

        # Windows: cmd/powershell は cwd に無いのが普通なので警告しない
        if os.name == "nt" and exe.lower() in {"cmd", "powershell", "pwsh"}:
            return cmd

        # Windows: PATH 解決を強化（npm.cmd問題など）
        if os.name == "nt":
            base = exe.lower()
            if not base.endswith((".exe", ".cmd", ".bat")):
                candidates = [exe + ".cmd", exe + ".bat", exe + ".exe", exe]
            else:
                candidates = [exe]

            found = None
            for c in candidates:
                found = shutil.which(c)
                if found:
                    cmd[0] = found
                    self.logger.info("Resolved PATH executable: %s -> %s", exe, cmd[0])
                    return cmd

        # cwd にある実行ファイルを解決（Goのexe等）
        candidate = Path(self.cwd) / exe
        if candidate.exists():
            cmd[0] = str(candidate)
            self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
            return cmd

        self.logger.warning("Executable not found in cwd: %s (cwd=%s). Will try PATH.", exe, self.cwd)
        return cmd

    def _pipe_logger(self, pipe, label: str, gen: int):
        """
        stderrでも即ERRORにしない。
        ただし「致命ワード」を見つけたら last_error を更新しておく（表示用）。
        """
        try:
            for line in pipe:
                if not self._is_current_gen(gen):
                    return
                line = line.rstrip("\r\n")
                self.logger.info("%s | %s", label, line)

                # 致命ワードは拾う（ただし status は healthcheck/exit で決める）
                if label == "STDERR":
                    if any(p.search(line) for p in FATAL_PATTERNS):
                        self.last_error = line
        except Exception as e:
            self.logger.exception("Pipe logger error (%s): %s", label, e)

    def _watch_exit(self, gen: int):
        """
        プロセス終了を監視し、exit code で ERROR/STOPPED を決める。
        """
        # 少し待ってから監視（起動直後の揺れ抑制）
        time.sleep(0.2)

        p = self.proc
        if not p:
            return

        rc = p.wait()
        if not self._is_current_gen(gen):
            return

        # ここで proc は終わったので None にする
        self.proc = None

        if rc == 0:
            self.status = "STOPPED"
            # last_error は残さない（成功終了）
            self.last_error = None
            self.logger.info("PROCESS EXITED (rc=0)")
        else:
            # 非0終了＝致命的
            self.status = "ERROR"
            if not self.last_error:
                self.last_error = f"Process exited with code {rc}"
            self.logger.error("PROCESS EXITED (rc=%s) => ERROR", rc)

    def _wait_health(self, port: int, gen: int):
        """
        STARTING中に指定portが開くのを待つ。
        - 開けば RUNNING
        - タイムアウトなら ERROR（=起動失敗/ポート競合）として止める
        """
        deadline = time.time() + max(0.5, self.startup_timeout_sec)

        while time.time() < deadline:
            if not self._is_current_gen(gen):
                return

            # プロセスが落ちたなら _watch_exit が処理するのでここは終了
            if not self.proc or self.proc.poll() is not None:
                return

            if is_port_open(port):
                self._set_status_if_current(gen, "RUNNING")
                self.logger.info("HEALTH OK (port=%s) => RUNNING (pid=%s gen=%s)", port, self.proc.pid, gen)
                return

            time.sleep(0.2)

        # タイムアウト：致命的（起動できてない or 競合）
        if not self._is_current_gen(gen):
            return

        self.status = "ERROR"
        if not self.last_error:
            self.last_error = f"Healthcheck timeout: port {port} not open within {self.startup_timeout_sec}s"
        self.logger.error("HEALTH FAILED: %s", self.last_error)

        # 起動失敗扱いなので止める（残り続けると混乱する）
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=3)
        finally:
            self.proc = None

    def _is_current_gen(self, gen: int) -> bool:
        return gen == self._gen

    def _set_status_if_current(self, gen: int, status: str):
        if self._is_current_gen(gen):
            self.status = status
