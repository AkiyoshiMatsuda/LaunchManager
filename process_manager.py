# import os
# import re
# import shutil
# import socket
# import subprocess
# import threading
# import time
# from pathlib import Path
# from logging_config import get_process_logger


# # 「致命的」になりやすいワード（言語/ツール混在でもある程度効く）
# FATAL_PATTERNS = [
#     re.compile(r"\bEADDRINUSE\b", re.IGNORECASE),
#     re.compile(r"address already in use", re.IGNORECASE),
#     re.compile(r"port.*already.*in use", re.IGNORECASE),
#     re.compile(r"bind\(\).*failed", re.IGNORECASE),
#     re.compile(r"failed to listen", re.IGNORECASE),
#     re.compile(r"cannot\s+bind", re.IGNORECASE),
#     re.compile(r"permission denied", re.IGNORECASE),
# ]


# def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.settimeout(timeout)
#             return s.connect_ex((host, port)) == 0
#     except Exception:
#         return False



# class ManagedProcess:
#     """
#     Status:
#       STOPPED / STARTING / RUNNING / STOPPING / ERROR
#     """
#     def _wait_stopped(self, timeout=10):
#         if self.process is None:
#             return

#         end = time.time() + timeout
#         while time.time() < end:
#             if self.process.poll() is not None:
#                 return
#             time.sleep(0.1)

#         # ここに来るなら「まだ死んでない」＝stopが不完全 or 反映待ち
#         # もう一段強く落とす（保険）
#         self._force_kill_tree()
#     def __init__(
#         self,
#         name: str,
#         command,
#         cwd: str,
#         env=None,
#         wait_port: int | None = None,
#         startup_timeout_sec: float = 8.0,
#     ):
#         self.name = name
#         self.command = command
#         self.cwd = cwd
#         self.env = env

#         # healthcheck
#         self.wait_port = wait_port
#         self.startup_timeout_sec = float(startup_timeout_sec) if startup_timeout_sec else 8.0

#         self.proc: subprocess.Popen | None = None
#         self.status = "STOPPED"
#         self.last_error: str | None = None

#         self.lock = threading.Lock()
#         self.logger = get_process_logger(name)

#         # 世代管理（古いスレッドが新しい起動を上書きしない）
#         self._gen = 0

#     # =========================
#     # Public
#     # =========================

#     def start(self):
#         with self.lock:
#             if self.proc and self.proc.poll() is None:
#                 self.logger.warning("START ignored (already running)")
#                 return

#             self._gen += 1
#             gen = self._gen

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
#                     bufsize=1,
#                 )
#             except FileNotFoundError as e:
#                 self.proc = None
#                 self.status = "ERROR"
#                 self.last_error = f"FileNotFoundError: {e}"
#                 self.logger.exception("START failed (FileNotFoundError): cmd=%s cwd=%s", cmd, self.cwd)
#                 return
#             except Exception as e:
#                 self.proc = None
#                 self.status = "ERROR"
#                 self.last_error = f"{type(e).__name__}: {e}"
#                 self.logger.exception("START failed (Unexpected): cmd=%s cwd=%s", cmd, self.cwd)
#                 return

#             # 出力ログ取り（stderrでも即ERRORにしない）
#             if self.proc.stdout:
#                 threading.Thread(target=self._pipe_logger, args=(self.proc.stdout, "STDOUT", gen), daemon=True).start()
#             if self.proc.stderr:
#                 threading.Thread(target=self._pipe_logger, args=(self.proc.stderr, "STDERR", gen), daemon=True).start()

#             # 終了監視（exit codeでERROR判定）
#             threading.Thread(target=self._watch_exit, args=(gen,), daemon=True).start()

#             # healthcheck（指定がある場合のみ：これが「起動成功」の根拠）
#             if self.wait_port:
#                 threading.Thread(target=self._wait_health, args=(self.wait_port, gen), daemon=True).start()
#             else:
#                 # ポート待ちがない場合は「プロセスが生きてる」＝RUNNING とみなす
#                 # （ただし直後に落ちたら _watch_exit が ERROR/STOPPED にする）
#                 self._set_status_if_current(gen, "RUNNING")
#                 self.logger.info("PROCESS alive (pid=%s gen=%s)", self.proc.pid if self.proc else None, gen)

#     def stop(self):
#         with self.lock:
#             if not self.proc or self.proc.poll() is not None:
#                 self.logger.warning("STOP ignored (not running)")
#                 self.status = "STOPPED"
#                 self.proc = None
#                 return

#             self._gen += 1
#             gen = self._gen

#             self.logger.info("STOP requested (gen=%s)", gen)
#             self.status = "STOPPING"

#             p = self.proc
#             pid = p.pid

#             try:
#                 if os.name == "nt":
#                     self.logger.info("taskkill /PID %s /T /F", pid)
#                     r = subprocess.run(
#                         ["taskkill", "/PID", str(pid), "/T", "/F"],
#                         capture_output=True,
#                         text=True,
#                     )
#                     self.logger.info(
#                         "taskkill done rc=%s stdout=%s stderr=%s",
#                         r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
#                     )

#                     # ★ここが重要：落ち切るのを少し待つ
#                     try:
#                         p.wait(timeout=5)
#                     except subprocess.TimeoutExpired:
#                         # 念のためもう一回
#                         self.logger.warning("process still alive after taskkill (pid=%s). retry taskkill.", pid)
#                         subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
#                         try:
#                             p.wait(timeout=5)
#                         except subprocess.TimeoutExpired:
#                             self.logger.error("process did not exit after retry (pid=%s)", pid)

#                 else:
#                     p.terminate()
#                     try:
#                         p.wait(timeout=5)
#                     except subprocess.TimeoutExpired:
#                         p.kill()
#                         p.wait(timeout=5)

#             finally:
#                 self.proc = None
#                 self.status = "STOPPED"
#                 self.last_error = None
#                 self.logger.info("STOPPED")

#     # def restart(self):
#     #     self.logger.info("RESTART requested")
#     #     self.stop()
#     #     self._wait_stopped(timeout=10)
#     #     self.start()
#     def restart(self):
#         self.logger.info("RESTART requested")
#         p = self.proc
#         self.stop()
#         self._wait_stopped(p, timeout=10)
#         self.start()

#     @property
#     def pid(self):
#         if self.proc and self.proc.poll() is None:
#             return self.proc.pid
#         return None

#     # =========================
#     # Internal
#     # =========================

#     def _resolve_command(self, command):
#         """
#         Windowsで npm/npx/pnpm/yarn などを確実に起動できるように補強。
#         """
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

#         # すでにパス指定ならそのまま
#         if "/" in exe or "\\" in exe:
#             return cmd

#         # Windows: cmd/powershell は cwd に無いのが普通なので警告しない
#         if os.name == "nt" and exe.lower() in {"cmd", "powershell", "pwsh"}:
#             return cmd

#         # Windows: PATH 解決を強化（npm.cmd問題など）
#         if os.name == "nt":
#             base = exe.lower()
#             if not base.endswith((".exe", ".cmd", ".bat")):
#                 candidates = [exe + ".cmd", exe + ".bat", exe + ".exe", exe]
#             else:
#                 candidates = [exe]

#             found = None
#             for c in candidates:
#                 found = shutil.which(c)
#                 if found:
#                     cmd[0] = found
#                     self.logger.info("Resolved PATH executable: %s -> %s", exe, cmd[0])
#                     return cmd

#         # cwd にある実行ファイルを解決（Goのexe等）
#         candidate = Path(self.cwd) / exe
#         if candidate.exists():
#             cmd[0] = str(candidate)
#             self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
#             return cmd

#         self.logger.warning("Executable not found in cwd: %s (cwd=%s). Will try PATH.", exe, self.cwd)
#         return cmd

#     def _pipe_logger(self, pipe, label: str, gen: int):
#         """
#         stderrでも即ERRORにしない。
#         ただし「致命ワード」を見つけたら last_error を更新しておく（表示用）。
#         """
#         try:
#             for line in pipe:
#                 if not self._is_current_gen(gen):
#                     return
#                 line = line.rstrip("\r\n")
#                 self.logger.info("%s | %s", label, line)

#                 # 致命ワードは拾う（ただし status は healthcheck/exit で決める）
#                 if label == "STDERR":
#                     if any(p.search(line) for p in FATAL_PATTERNS):
#                         self.last_error = line
#         except Exception as e:
#             self.logger.exception("Pipe logger error (%s): %s", label, e)

#     def _watch_exit(self, gen: int):
#         """
#         プロセス終了を監視し、exit code で ERROR/STOPPED を決める。
#         """
#         # 少し待ってから監視（起動直後の揺れ抑制）
#         time.sleep(0.2)

#         p = self.proc
#         if not p:
#             return

#         rc = p.wait()
#         if not self._is_current_gen(gen):
#             return

#         # ここで proc は終わったので None にする
#         self.proc = None

#         if rc == 0:
#             self.status = "STOPPED"
#             # last_error は残さない（成功終了）
#             self.last_error = None
#             self.logger.info("PROCESS EXITED (rc=0)")
#         else:
#             # 非0終了＝致命的
#             self.status = "ERROR"
#             if not self.last_error:
#                 self.last_error = f"Process exited with code {rc}"
#             self.logger.error("PROCESS EXITED (rc=%s) => ERROR", rc)

#     def _wait_health(self, port: int, gen: int):
#         """
#         STARTING中に指定portが開くのを待つ。
#         - 開けば RUNNING
#         - タイムアウトなら ERROR（=起動失敗/ポート競合）として止める
#         """
#         deadline = time.time() + max(0.5, self.startup_timeout_sec)

#         while time.time() < deadline:
#             if not self._is_current_gen(gen):
#                 return

#             # プロセスが落ちたなら _watch_exit が処理するのでここは終了
#             if not self.proc or self.proc.poll() is not None:
#                 return

#             if is_port_open(port):
#                 self._set_status_if_current(gen, "RUNNING")
#                 self.logger.info("HEALTH OK (port=%s) => RUNNING (pid=%s gen=%s)", port, self.proc.pid, gen)
#                 return

#             time.sleep(0.2)

#         # # タイムアウト：致命的（起動できてない or 競合）
#         # if not self._is_current_gen(gen):
#         #     return

#         # self.status = "ERROR"
#         # if not self.last_error:
#         #     self.last_error = f"Healthcheck timeout: port {port} not open within {self.startup_timeout_sec}s"
#         # self.logger.error("HEALTH FAILED: %s", self.last_error)

#         # # 起動失敗扱いなので止める（残り続けると混乱する）
#         # try:
#         #     if self.proc and self.proc.poll() is None:
#         #         self.proc.terminate()
#         #         try:
#         #             self.proc.wait(timeout=3)
#         #         except subprocess.TimeoutExpired:
#         #             self.proc.kill()
#         #             self.proc.wait(timeout=3)
#         # finally:
#         #     self.proc = None
#         # タイムアウト：致命的
#         if not self._is_current_gen(gen):
#             return

#         self._set_status_if_current(gen, "ERROR")
#         if not self.last_error:
#             self.last_error = f"Healthcheck timeout: port {port} not open within {self.startup_timeout_sec}s"
#         self.logger.error("HEALTH FAILED: %s", self.last_error)

#         p = self.proc
#         pid = p.pid if p else None

#         try:
#             if p and p.poll() is None:
#                 if os.name == "nt" and pid:
#                     r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
#                     self.logger.info("taskkill (health timeout) rc=%s stdout=%s stderr=%s",
#                                     r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip())
#                     try:
#                         p.wait(timeout=5)
#                     except subprocess.TimeoutExpired:
#                         pass
#                 else:
#                     p.terminate()
#                     try:
#                         p.wait(timeout=3)
#                     except subprocess.TimeoutExpired:
#                         p.kill()
#                         p.wait(timeout=3)
#         finally:
#             self.proc = None


#     def _is_current_gen(self, gen: int) -> bool:
#         return gen == self._gen

#     def _set_status_if_current(self, gen: int, status: str):
#         if self._is_current_gen(gen):
#             self.status = status


import os
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from logging_config import get_process_logger


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


def wait_port_closed(port: int, host: str = "127.0.0.1", timeout: float = 10.0, interval: float = 0.2) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if not is_port_open(port, host=host, timeout=0.2):
            return True
        time.sleep(interval)
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
        stop_timeout_sec: float = 10.0,
        port_release_timeout_sec: float = 10.0,
    ):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env

        self.wait_port = wait_port
        self.startup_timeout_sec = float(startup_timeout_sec) if startup_timeout_sec else 8.0
        self.stop_timeout_sec = float(stop_timeout_sec) if stop_timeout_sec else 10.0
        self.port_release_timeout_sec = (
            float(port_release_timeout_sec) if port_release_timeout_sec else 10.0
        )

        self.proc: subprocess.Popen | None = None
        self.status = "STOPPED"
        self.last_error: str | None = None

        self.lock = threading.Lock()
        self.logger = get_process_logger(name)

        # 世代管理
        self._gen = 0

    # =========================
    # Public
    # =========================

    # def start(self):
    #     with self.lock:
    #         if self.proc and self.proc.poll() is None:
    #             self.logger.warning("START ignored (already running)")
    #             return

    #         self._gen += 1
    #         gen = self._gen

    #         self.logger.info("START requested (gen=%s)", gen)
    #         self.status = "STARTING"
    #         self.last_error = None

    #         # 念のため、同じポートがまだ掴まれているなら少し待つ
    #         if self.wait_port:
    #             if is_port_open(self.wait_port):
    #                 self.logger.warning(
    #                     "Port %s is still open before start. waiting for release...",
    #                     self.wait_port,
    #                 )
    #                 released = wait_port_closed(
    #                     self.wait_port,
    #                     timeout=self.port_release_timeout_sec,
    #                 )
    #                 if not released:
    #                     self.status = "ERROR"
    #                     self.last_error = (
    #                         f"Start aborted: port {self.wait_port} is still in use "
    #                         f"after waiting {self.port_release_timeout_sec}s"
    #                     )
    #                     self.logger.error(self.last_error)
    #                     return

    #         cmd = self._resolve_command(self.command)

    #         try:
    #             self.proc = subprocess.Popen(
    #                 cmd,
    #                 cwd=self.cwd,
    #                 env=self.env,
    #                 stdout=subprocess.PIPE,
    #                 stderr=subprocess.PIPE,
    #                 text=True,
    #                 encoding="utf-8",
    #                 errors="replace",
    #                 bufsize=1,
    #             )
    #         except FileNotFoundError as e:
    #             self.proc = None
    #             self.status = "ERROR"
    #             self.last_error = f"FileNotFoundError: {e}"
    #             self.logger.exception("START failed (FileNotFoundError): cmd=%s cwd=%s", cmd, self.cwd)
    #             return
    #         except Exception as e:
    #             self.proc = None
    #             self.status = "ERROR"
    #             self.last_error = f"{type(e).__name__}: {e}"
    #             self.logger.exception("START failed (Unexpected): cmd=%s cwd=%s", cmd, self.cwd)
    #             return

    #         if self.proc.stdout:
    #             threading.Thread(
    #                 target=self._pipe_logger,
    #                 args=(self.proc.stdout, "STDOUT", gen),
    #                 daemon=True,
    #             ).start()

    #         if self.proc.stderr:
    #             threading.Thread(
    #                 target=self._pipe_logger,
    #                 args=(self.proc.stderr, "STDERR", gen),
    #                 daemon=True,
    #             ).start()

    #         threading.Thread(target=self._watch_exit, args=(self.proc, gen), daemon=True).start()

    #         if self.wait_port:
    #             threading.Thread(
    #                 target=self._wait_health,
    #                 args=(self.proc, self.wait_port, gen),
    #                 daemon=True,
    #             ).start()
    #         else:
    #             self._set_status_if_current(gen, "RUNNING")
    #             self.logger.info(
    #                 "PROCESS alive (pid=%s gen=%s)",
    #                 self.proc.pid if self.proc else None,
    #                 gen,
    #             )
    def start(self):
    # ---------- 事前確認 ----------
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self.logger.warning("START ignored (already running)")
                return

            self._gen += 1
            gen = self._gen
            self.status = "STARTING"
            self.last_error = None

        self.logger.info("START requested (gen=%s)", gen)

        # ---------- ポート解放待ち（lock外） ----------
        if self.wait_port and is_port_open(self.wait_port):
            self.logger.warning(
                "Port %s still open before start. waiting...",
                self.wait_port
            )

            released = wait_port_closed(
                self.wait_port,
                timeout=self.port_release_timeout_sec,
            )

            if not released:
                with self.lock:
                    if self._is_current_gen(gen):
                        self.status = "ERROR"
                        self.last_error = (
                            f"Start aborted: port {self.wait_port} still in use"
                        )
                return

        cmd = self._resolve_command(self.command)

        # ---------- 起動 ----------
        try:
            proc = subprocess.Popen(
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
        except Exception as e:
            with self.lock:
                if self._is_current_gen(gen):
                    self.status = "ERROR"
                    self.last_error = f"{type(e).__name__}: {e}"
            self.logger.exception("START failed")
            return

        with self.lock:
            if not self._is_current_gen(gen):
                self._terminate_process(proc)
                return

            self.proc = proc

        # ログ監視
        if proc.stdout:
            threading.Thread(
                target=self._pipe_logger,
                args=(proc.stdout, "STDOUT", gen),
                daemon=True,
            ).start()

        if proc.stderr:
            threading.Thread(
                target=self._pipe_logger,
                args=(proc.stderr, "STDERR", gen),
                daemon=True,
            ).start()

        threading.Thread(
            target=self._watch_exit,
            args=(proc, gen),
            daemon=True,
        ).start()

        if self.wait_port:
            threading.Thread(
                target=self._wait_health,
                args=(proc, self.wait_port, gen),
                daemon=True,
            ).start()
        else:
            self._set_status_if_current(gen, "RUNNING")

    # def stop(self):
    #     with self.lock:
    #         p = self.proc

    #         if not p or p.poll() is not None:
    #             self.logger.warning("STOP ignored (not running)")
    #             self.proc = None
    #             self.status = "STOPPED"
    #             return

    #         self._gen += 1
    #         gen = self._gen

    #         self.logger.info("STOP requested (gen=%s)", gen)
    #         self.status = "STOPPING"

    #     # 実処理は lock の外でやる
    #     try:
    #         self._terminate_process(p)
    #         self._wait_stopped(proc=p, timeout=self.stop_timeout_sec)

    #         if self.wait_port:
    #             released = wait_port_closed(
    #                 self.wait_port,
    #                 timeout=self.port_release_timeout_sec,
    #             )
    #             if not released:
    #                 self.logger.warning(
    #                     "Port %s was not released within %.1fs after stop",
    #                     self.wait_port,
    #                     self.port_release_timeout_sec,
    #                 )
    #     finally:
    #         with self.lock:
    #             if self.proc is p:
    #                 self.proc = None
    #             self.status = "STOPPED"
    #             self.last_error = None
    #             self.logger.info("STOPPED")
    def stop(self):
        with self.lock:
            p = self.proc

            if not p or p.poll() is not None:
                self.logger.warning("STOP ignored (not running)")
                self.proc = None
                self.status = "STOPPED"
                return

            self._gen += 1
            gen = self._gen

            self.logger.info("STOP requested (gen=%s)", gen)
            self.status = "STOPPING"

        stop_ok = True
        port_ok = True

        try:
            # -------------------
            # プロセス終了
            # -------------------
            self._terminate_process(p)

            stopped = self._wait_stopped(
                proc=p,
                timeout=self.stop_timeout_sec
            )

            if not stopped:
                stop_ok = False
                self.logger.error(
                    "Failed to stop process within %.1fs",
                    self.stop_timeout_sec
                )

            # -------------------
            # ポート解放待ち
            # -------------------
            if self.wait_port:
                released = wait_port_closed(
                    self.wait_port,
                    timeout=self.port_release_timeout_sec,
                )

                if not released:
                    port_ok = False
                    self.logger.error(
                        "Port %s not released within %.1fs",
                        self.wait_port,
                        self.port_release_timeout_sec
                    )

            # Go向け安定待ち
            time.sleep(0.5)

        finally:
            with self.lock:
                if self.proc is p:
                    self.proc = None

                if stop_ok and port_ok:
                    self.status = "STOPPED"
                    self.last_error = None
                    self.logger.info("STOPPED")
                else:
                    self.status = "ERROR"
                    self.last_error = "Stop incomplete"
                    self.logger.error("STOP FAILED")

    # def restart(self):
    #     self.logger.info("RESTART requested")
    #     self.stop()
    #     self.start()
    # def restart(self):
    #     self.logger.info("RESTART requested")

    #     self.stop()

    #     # Go系(port監視あり)は少し待つ
    #     if self.wait_port:
    #         released = wait_port_closed(
    #             self.wait_port,
    #             timeout=self.port_release_timeout_sec
    #         )

    #         if not released:
    #             self.logger.warning("Port release wait timeout before restart")

    #         time.sleep(1.0)   # ← 超重要

    #     self.start()
    def restart(self):
        self.logger.info("RESTART requested")

        # まず停止
        self.stop()

        # 停止失敗なら再起動しない
        if self.status != "STOPPED":
            self.logger.error(
                "RESTART aborted: stop phase failed (status=%s)",
                self.status
            )
            return

        # 少しだけクールダウン（任意）
        time.sleep(0.2)

        # 起動
        self.start()

    @property
    def pid(self):
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        return None

    # =========================
    # Internal
    # =========================

    def _wait_stopped(self, *, proc: subprocess.Popen | None, timeout: float = 10.0):
        if proc is None:
            return True

        end = time.time() + timeout
        while time.time() < end:
            if proc.poll() is not None:
                return True
            time.sleep(0.1)

        self.logger.warning("Process still alive after %.1fs. forcing kill tree.", timeout)
        self._force_kill_tree(proc)
        return proc.poll() is not None

    def _terminate_process(self, proc: subprocess.Popen):
        pid = proc.pid
        try:
            if os.name == "nt":
                self.logger.info("taskkill /PID %s /T /F", pid)
                r = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                )
                self.logger.info(
                    "taskkill done rc=%s stdout=%s stderr=%s",
                    r.returncode,
                    (r.stdout or "").strip(),
                    (r.stderr or "").strip(),
                )
            else:
                proc.terminate()
        except Exception as e:
            self.logger.exception("Terminate failed for pid=%s: %s", pid, e)

    def _force_kill_tree(self, proc: subprocess.Popen | None):
        if proc is None:
            return

        pid = proc.pid
        try:
            if proc.poll() is not None:
                return

            if os.name == "nt":
                self.logger.warning("force taskkill /PID %s /T /F", pid)
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                )
            else:
                proc.kill()
        except Exception as e:
            self.logger.exception("Force kill failed for pid=%s: %s", pid, e)

    def _resolve_command(self, command):
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

        if "/" in exe or "\\" in exe:
            return cmd

        if os.name == "nt" and exe.lower() in {"cmd", "powershell", "pwsh"}:
            return cmd

        if os.name == "nt":
            base = exe.lower()
            if not base.endswith((".exe", ".cmd", ".bat")):
                candidates = [exe + ".cmd", exe + ".bat", exe + ".exe", exe]
            else:
                candidates = [exe]

            for c in candidates:
                found = shutil.which(c)
                if found:
                    cmd[0] = found
                    self.logger.info("Resolved PATH executable: %s -> %s", exe, cmd[0])
                    return cmd

        candidate = Path(self.cwd) / exe
        if candidate.exists():
            cmd[0] = str(candidate)
            self.logger.info("Resolved executable: %s -> %s", exe, cmd[0])
            return cmd

        self.logger.warning("Executable not found in cwd: %s (cwd=%s). Will try PATH.", exe, self.cwd)
        return cmd

    def _pipe_logger(self, pipe, label: str, gen: int):
        try:
            for line in pipe:
                if not self._is_current_gen(gen):
                    return

                line = line.rstrip("\r\n")
                self.logger.info("%s | %s", label, line)

                if label == "STDERR":
                    if any(p.search(line) for p in FATAL_PATTERNS):
                        self.last_error = line
        except Exception as e:
            self.logger.exception("Pipe logger error (%s): %s", label, e)

    def _watch_exit(self, proc: subprocess.Popen, gen: int):
        time.sleep(0.2)

        try:
            rc = proc.wait()
        except Exception as e:
            self.logger.exception("watch_exit wait failed: %s", e)
            return

        if not self._is_current_gen(gen):
            return

        with self.lock:
            if self.proc is proc:
                self.proc = None

            # STOPPING中に意図通り落ちたなら STOPPED 扱い
            if self.status == "STOPPING":
                self.status = "STOPPED"
                self.last_error = None
                self.logger.info("PROCESS EXITED during STOPPING (rc=%s)", rc)
                return

            if rc == 0:
                self.status = "STOPPED"
                self.last_error = None
                self.logger.info("PROCESS EXITED (rc=0)")
            else:
                self.status = "ERROR"
                if not self.last_error:
                    self.last_error = f"Process exited with code {rc}"
                self.logger.error("PROCESS EXITED (rc=%s) => ERROR", rc)

    def _wait_health(self, proc: subprocess.Popen, port: int, gen: int):
        deadline = time.time() + max(0.5, self.startup_timeout_sec)

        while time.time() < deadline:
            if not self._is_current_gen(gen):
                return

            if proc.poll() is not None:
                return

            if is_port_open(port):
                self._set_status_if_current(gen, "RUNNING")
                self.logger.info(
                    "HEALTH OK (port=%s) => RUNNING (pid=%s gen=%s)",
                    port,
                    proc.pid,
                    gen,
                )
                return

            time.sleep(0.2)

        if not self._is_current_gen(gen):
            return

        self._set_status_if_current(gen, "ERROR")
        if not self.last_error:
            self.last_error = f"Healthcheck timeout: port {port} not open within {self.startup_timeout_sec}s"
        self.logger.error("HEALTH FAILED: %s", self.last_error)

        try:
            if proc.poll() is None:
                self._terminate_process(proc)
                self._wait_stopped(proc=proc, timeout=5.0)
        finally:
            with self.lock:
                if self.proc is proc:
                    self.proc = None

    def _is_current_gen(self, gen: int) -> bool:
        return gen == self._gen

    def _set_status_if_current(self, gen: int, status: str):
        if self._is_current_gen(gen):
            self.status = status