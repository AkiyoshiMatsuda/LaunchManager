# import subprocess
# import threading
# import time
# from pathlib import Path
# from logging_config import get_process_logger


# class ManagedProcess:
#     def __init__(self, name, command, cwd, env=None):
#         """
#         name: ログ識別子（logs/{name}/ など）
#         command: list[str] 推奨（例: ["todoapp.exe"] / ["go","run","main.go"]）
#         cwd: 作業ディレクトリ（プロジェクトルート）
#         env: dict[str,str] or None
#         """
#         self.name = name
#         self.command = command
#         self.cwd = cwd
#         self.env = env

#         self.proc = None
#         self.status = "STOPPED"
#         self.lock = threading.Lock()

#         self.logger = get_process_logger(name)

#     # =========================
#     # Process Control
#     # =========================

#     def start(self):
#         with self.lock:
#             if self.proc and self.proc.poll() is None:
#                 self.logger.warning("START ignored (already running)")
#                 return

#             self.logger.info("START requested")
#             self.status = "STARTING"

#             # ✅ command[0] を cwd 基準で確実に解決する
#             cmd = self._resolve_command(self.command)

#             try:
#                 self.proc = subprocess.Popen(
#                     cmd,
#                     cwd=self.cwd,
#                     env=self.env,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     text=True,
#                     bufsize=1
#                 )
#             except FileNotFoundError as e:
#                 # exe/コマンドが見つからない（WinError 2）
#                 self.status = "STOPPED"
#                 self.logger.exception(
#                     "START failed (FileNotFoundError): %s | cmd=%s | cwd=%s",
#                     e, cmd, self.cwd
#                 )
#                 return
#             except Exception as e:
#                 # その他の例外もログに残す
#                 self.status = "STOPPED"
#                 self.logger.exception(
#                     "START failed (Unexpected): %s | cmd=%s | cwd=%s",
#                     e, cmd, self.cwd
#                 )
#                 return

#             # 起動監視
#             threading.Thread(target=self._watch, daemon=True).start()

#             # stdout/stderr ログ取り
#             if self.proc.stdout:
#                 threading.Thread(
#                     target=self._pipe_logger,
#                     args=(self.proc.stdout, "STDOUT"),
#                     daemon=True
#                 ).start()

#             if self.proc.stderr:
#                 threading.Thread(
#                     target=self._pipe_logger,
#                     args=(self.proc.stderr, "STDERR"),
#                     daemon=True
#                 ).start()

#     def stop(self):
#         with self.lock:
#             if not self.proc or self.proc.poll() is not None:
#                 self.logger.warning("STOP ignored (not running)")
#                 self.status = "STOPPED"
#                 return

#             self.logger.info("STOP requested")
#             self.status = "STOPPING"

#             self.proc.terminate()

#             try:
#                 self.proc.wait(timeout=5)
#                 self.logger.info("Process terminated gracefully")
#             except subprocess.TimeoutExpired:
#                 self.logger.error("FORCE KILL")
#                 self.proc.kill()
#                 self.proc.wait()

#             self.status = "STOPPED"
#             self.logger.info("STOPPED")

#     def restart(self):
#         self.logger.info("RESTART requested")
#         self.stop()
#         self.start()

#     # =========================
#     # Internal
#     # =========================

#     def _resolve_command(self, command):
#         """
#         Windowsで `["todoapp.exe"]` のような相対指定でも確実に起動できるように
#         command[0] を cwd 基準で絶対パス化する。

#         - command が文字列の場合も許容（ただし list 推奨）
#         - すでにパス（/ or \\ を含む）ならそのまま
#         - cwd/command[0] が存在するなら置き換え
#         """
#         if command is None:
#             return command

#         # list[str] 推奨だが、念のため str も許容
#         if isinstance(command, str):
#             # 文字列で来たら「そのまま」扱う（shell=Falseなので基本は非推奨）
#             return command

#         if not isinstance(command, (list, tuple)) or len(command) == 0:
#             return command

#         cmd = list(command)
#         exe = cmd[0]

#         if not isinstance(exe, str) or exe.strip() == "":
#             return cmd

#         exe = exe.strip()

#         # すでにパスっぽい（絶対/相対問わず区切りが入っている）ならそのまま
#         if ("/" in exe) or ("\\" in exe):
#             return cmd

#         # cwd 基準で解決
#         candidate = Path(self.cwd) / exe
#         if candidate.exists():
#             cmd[0] = str(candidate)
#             self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
#         else:
#             # ここで見つからない場合は PATH に期待するしかないのでログだけ出す
#             self.logger.warning("Executable not found in cwd: %s (cwd=%s). Will try PATH.", exe, self.cwd)

#         return cmd

#     def _watch(self):
#         time.sleep(1)

#         # start() が失敗して proc が None の可能性に備える
#         if not self.proc:
#             self.status = "STOPPED"
#             return

#         if self.proc.poll() is None:
#             self.status = "RUNNING"
#             self.logger.info("RUNNING (pid=%s)", self.proc.pid)
#             self.proc.wait()

#         self.status = "STOPPED"
#         self.logger.info("PROCESS EXITED")

#     def _pipe_logger(self, pipe, label):
#         try:
#             for line in pipe:
#                 self.logger.info("%s | %s", label, line.rstrip())
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


import subprocess
import threading
import time
from pathlib import Path
from logging_config import get_process_logger


class ManagedProcess:
    def __init__(self, name, command, cwd, env=None):
        """
        name: ログ識別子（logs/{name}/ など）
        command: list[str] 推奨（例: ["todoapp.exe"] / ["go","run","main.go"]）
        cwd: 作業ディレクトリ（プロジェクトルート）
        env: dict[str,str] or None
        """
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env

        self.proc = None
        self.status = "STOPPED"   # STOPPED / STARTING / RUNNING / STOPPING / ERROR
        self.last_error = None    # ★ 追加：直近エラー内容
        self.lock = threading.Lock()

        self.logger = get_process_logger(name)

    # =========================
    # Process Control
    # =========================

    def start(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self.logger.warning("START ignored (already running)")
                return

            self.logger.info("START requested")
            self.status = "STARTING"
            self.last_error = None

            # command[0] を cwd 基準で解決
            cmd = self._resolve_command(self.command)

            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            except FileNotFoundError as e:
                # exe/コマンドが見つからない
                self.status = "ERROR"
                self.last_error = f"FileNotFoundError: {e}"
                self.logger.exception(
                    "START failed (FileNotFoundError): cmd=%s cwd=%s",
                    cmd, self.cwd
                )
                self.proc = None
                return
            except Exception as e:
                # その他の起動失敗
                self.status = "ERROR"
                self.last_error = f"{type(e).__name__}: {e}"
                self.logger.exception(
                    "START failed (Unexpected): cmd=%s cwd=%s",
                    cmd, self.cwd
                )
                self.proc = None
                return

            # 起動監視
            threading.Thread(target=self._watch, daemon=True).start()

            # stdout / stderr ログ取り
            if self.proc.stdout:
                threading.Thread(
                    target=self._pipe_logger,
                    args=(self.proc.stdout, "STDOUT"),
                    daemon=True
                ).start()

            if self.proc.stderr:
                threading.Thread(
                    target=self._pipe_logger,
                    args=(self.proc.stderr, "STDERR"),
                    daemon=True
                ).start()

    def stop(self):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                self.logger.warning("STOP ignored (not running)")
                self.status = "STOPPED"
                return

            self.logger.info("STOP requested")
            self.status = "STOPPING"

            self.proc.terminate()

            try:
                self.proc.wait(timeout=5)
                self.logger.info("Process terminated gracefully")
            except subprocess.TimeoutExpired:
                self.logger.error("FORCE KILL")
                self.proc.kill()
                self.proc.wait()

            self.proc = None
            self.status = "STOPPED"
            self.last_error = None
            self.logger.info("STOPPED")

    def restart(self):
        self.logger.info("RESTART requested")
        self.stop()
        self.start()

    # =========================
    # Internal
    # =========================

    def _resolve_command(self, command):
        """
        command[0] を cwd 基準で絶対パス化する（Windows対策）
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

        candidate = Path(self.cwd) / exe
        if candidate.exists():
            cmd[0] = str(candidate)
            self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
        else:
            self.logger.warning(
                "Executable not found in cwd: %s (cwd=%s). Will try PATH.",
                exe, self.cwd
            )

        return cmd

    def _watch(self):
        time.sleep(1)

        if not self.proc:
            return

        if self.proc.poll() is None:
            self.status = "RUNNING"
            self.logger.info("RUNNING (pid=%s)", self.proc.pid)
            self.proc.wait()

        self.proc = None
        self.status = "STOPPED"
        self.logger.info("PROCESS EXITED")

    def _pipe_logger(self, pipe, label):
        try:
            for line in pipe:
                self.logger.info("%s | %s", label, line.rstrip())
        except Exception as e:
            self.logger.exception("Pipe logger error (%s): %s", label, e)

    # =========================
    # Info
    # =========================

    @property
    def pid(self):
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        return None
