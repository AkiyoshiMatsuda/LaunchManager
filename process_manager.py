# import subprocess
# import threading
# import time
# import socket

# class ManagedProcess:
#     def __init__(self, name, command, cwd, env=None):
#         self.name = name
#         self.command = command
#         self.cwd = cwd
#         self.env = env
#         self.proc = None
#         self.status = "STOPPED"

#     def start(self):
#         if self.proc and self.proc.poll() is None:
#             return

#         self.status = "STARTING"

#         proc = subprocess.Popen(
#             self.command,
#             cwd=self.cwd,
#             env=self.env,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )

#         self.proc = proc
#         threading.Thread(
#             target=self._watch,
#             args=(proc,),
#             daemon=True
#         ).start()

#     def _watch(self, proc):
#         time.sleep(0.5)

#         if proc.poll() is None:
#             self.status = "RUNNING"

#         proc.wait()

#         # ★ この proc が「現在の proc」なら STOPPED にする
#         if self.proc is proc:
#             self.status = "STOPPED"
#             self.proc = None

#     def stop(self):
#         if not self.proc:
#             return

#         proc = self.proc
#         self.status = "STOPPING"

#         proc.terminate()
#         try:
#             proc.wait(timeout=2)
#         except subprocess.TimeoutExpired:
#             proc.kill()
#             proc.wait()

#         if self.proc is proc:
#             self.proc = None
#             self.status = "STOPPED"

#     def restart(self):
#         self.stop()
#         time.sleep(0.2)  # ★ Windowsでは重要
#         self.start()

#     @property
#     def pid(self):
#         if self.proc:
#             return self.proc.pid
#         return None

import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime

class ManagedProcess:
    def __init__(self, name, command, cwd, env=None, log_dir="logs"):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env
        self.proc = None
        self.status = "STOPPED"

        # ログディレクトリ
        self.log_path = Path(log_dir) / name
        self.log_path.mkdir(parents=True, exist_ok=True)

        self.stdout_log = open(self.log_path / "stdout.log", "a", encoding="utf-8")
        self.stderr_log = open(self.log_path / "stderr.log", "a", encoding="utf-8")
        self.manager_log = self.log_path / "manager.log"

        self.lock = threading.Lock()

    def _log(self, message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.manager_log, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")

    def start(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self._log("START ignored (already running)")
                return

            self._log("START requested")
            self.status = "STARTING"

            self.proc = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=self.stdout_log,
                stderr=self.stderr_log
            )

            threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        time.sleep(1)

        if self.proc.poll() is None:
            self.status = "RUNNING"
            self._log(f"RUNNING (pid={self.proc.pid})")
            self.proc.wait()

        self.status = "STOPPED"
        self._log("STOPPED")

    def stop(self):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                self.status = "STOPPED"
                self._log("STOP ignored (not running)")
                return

            self._log("STOP requested")
            self.status = "STOPPING"
            self.proc.terminate()

            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._log("FORCE KILL")
                self.proc.kill()

            self.status = "STOPPED"
            self._log("STOPPED")

    def restart(self):
        self._log("RESTART requested")
        self.stop()
        self.start()

    @property
    def pid(self):
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        return None
