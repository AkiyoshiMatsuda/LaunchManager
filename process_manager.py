import subprocess
import threading
import time
import socket

class ManagedProcess:
    def __init__(self, name, command, cwd, env=None):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env
        self.proc = None
        self.status = "STOPPED"

    def start(self):
        if self.proc and self.proc.poll() is None:
            return

        self.status = "STARTING"

        proc = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.proc = proc
        threading.Thread(
            target=self._watch,
            args=(proc,),
            daemon=True
        ).start()

    def _watch(self, proc):
        time.sleep(0.5)

        if proc.poll() is None:
            self.status = "RUNNING"

        proc.wait()

        # ★ この proc が「現在の proc」なら STOPPED にする
        if self.proc is proc:
            self.status = "STOPPED"
            self.proc = None

    def stop(self):
        if not self.proc:
            return

        proc = self.proc
        self.status = "STOPPING"

        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        if self.proc is proc:
            self.proc = None
            self.status = "STOPPED"

    def restart(self):
        self.stop()
        time.sleep(0.2)  # ★ Windowsでは重要
        self.start()

    @property
    def pid(self):
        if self.proc:
            return self.proc.pid
        return None
