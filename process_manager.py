import subprocess
import threading
import time
from logging_config import get_process_logger


class ManagedProcess:
    def __init__(self, name, command, cwd, env=None):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env

        self.proc = None
        self.status = "STOPPED"
        self.lock = threading.Lock()

        # ★ ロガー取得（設計は logging_config.py）
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

            self.proc = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            threading.Thread(
                target=self._watch,
                daemon=True
            ).start()

            threading.Thread(
                target=self._pipe_logger,
                args=(self.proc.stdout, "STDOUT"),
                daemon=True
            ).start()

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

            self.status = "STOPPED"
            self.logger.info("STOPPED")

    def restart(self):
        self.logger.info("RESTART requested")
        self.stop()
        self.start()

    # =========================
    # Internal
    # =========================

    def _watch(self):
        time.sleep(1)

        if self.proc.poll() is None:
            self.status = "RUNNING"
            self.logger.info("RUNNING (pid=%s)", self.proc.pid)
            self.proc.wait()

        self.status = "STOPPED"
        self.logger.info("PROCESS EXITED")

    def _pipe_logger(self, pipe, label):
        for line in pipe:
            self.logger.info("%s | %s", label, line.rstrip())

    # =========================
    # Info
    # =========================

    @property
    def pid(self):
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        return None
