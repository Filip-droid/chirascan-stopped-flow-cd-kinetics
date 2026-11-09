# src/modules/utils/session_files.py
"""Automatic saving and crash recovery - the files (Qt-free; the timer, menu
and questions are in src/controllers/autosave_controller.py). The same design
as in SpecAnalytiXBase.

Where: %LOCALAPPDATA%\\StoppedFlowKinetiX\\autosave\\ (~/.stoppedflowkinetix/autosave
elsewhere); the environment variable STOPPEDFLOWKINETIX_DATA_DIR overrides
the base folder (tests).

Crash detection
---------------
Each running instance holds an OS file lock on session-<id>.lock as long as
it runs and removes its files (lock, info, automatic save) when it is closed
normally. The operating system releases a lock when its process ends in any
way, so a session whose lock can be taken by someone else belongs to an
instance that ended abnormally (crash, power cut, killed); its automatic save
can be offered for restoring. Several instances can run side by side, and
reused process ids cannot confuse it."""

import json
import os
import sys
import time
import uuid

from src.modules.utils.app_logger import app_data_dir, get_logger

logger = get_logger(__name__)

AUTOSAVE_CHOICES = (0, 2, 5, 10, 20)        # minutes; 0 = off
DEFAULT_AUTOSAVE_MINUTES = 5
AUTOSAVE_EXTENSION = ".sfkx"


def data_dir():
    return os.environ.get("STOPPEDFLOWKINETIX_DATA_DIR") or app_data_dir()


def _try_lock(fh):
    """Exclusive, non-blocking lock on an open file. True if acquired."""
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(fh):
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def session_is_alive(lock_path):
    """True if the instance owning `lock_path` is still running (it holds the lock)."""
    if not os.path.exists(lock_path):
        return False
    try:
        fh = open(lock_path, "a+b")
    except OSError:
        return True                       # cannot even open it: assume it is in use
    try:
        if _try_lock(fh):
            _unlock(fh)
            return False
        return True
    finally:
        fh.close()


def _remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning("Could not remove %s: %s", path, exc)


class AutosaveManager:
    """Session lock + automatic save of one running instance.

    Files (in self.folder), for a session id like "1234-a1b2c3d4":
        session-<id>.lock     held locked while the instance runs
        session-<id>.json     when it started, which version
        autosave-<id>.sfkx    the latest automatic save (a project file)
    """

    def __init__(self, folder=None, session_id=None, is_alive=None):
        self.folder = folder or os.path.join(data_dir(), "autosave")
        self.session_id = session_id or f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._is_alive = is_alive or (lambda sid: session_is_alive(self.lock_path(sid)))
        self._lock_handle = None

    def lock_path(self, sid=None):
        return os.path.join(self.folder, f"session-{sid or self.session_id}.lock")

    def info_path(self, sid=None):
        return os.path.join(self.folder, f"session-{sid or self.session_id}.json")

    def autosave_path(self, sid=None):
        return os.path.join(self.folder, f"autosave-{sid or self.session_id}{AUTOSAVE_EXTENSION}")

    def start_session(self, app_version=""):
        os.makedirs(self.folder, exist_ok=True)
        fh = open(self.lock_path(), "a+b")
        if not _try_lock(fh):
            fh.close()
            raise OSError(f"could not lock {self.lock_path()}")
        self._lock_handle = fh
        with open(self.info_path(), "w", encoding="utf-8") as f:
            json.dump({"session": self.session_id, "pid": os.getpid(), "started": time.time(),
                       "app_version": app_version}, f)

    def remove_autosave(self):
        _remove(self.autosave_path())

    def end_session(self):
        """Normal exit: nothing to recover from this session."""
        _remove(self.autosave_path())
        _remove(self.info_path())
        if self._lock_handle is not None:
            _unlock(self._lock_handle)
            self._lock_handle.close()
            self._lock_handle = None
        _remove(self.lock_path())

    def _other_session_ids(self):
        ids = set()
        if not os.path.isdir(self.folder):
            return ids
        for name in os.listdir(self.folder):
            for prefix, suffix in (("session-", ".lock"), ("session-", ".json"), ("autosave-", AUTOSAVE_EXTENSION)):
                if name.startswith(prefix) and name.endswith(suffix):
                    sid = name[len(prefix):-len(suffix)]
                    if sid and sid != self.session_id:
                        ids.add(sid)
        return ids

    def find_recoverable(self):
        """Sessions that ended abnormally and left an automatic save, newest first:
        [{'session', 'saved_at', 'size', 'path', 'app_version'}]. Leftovers of ended sessions
        without an automatic save are removed on the way."""
        found = []
        for sid in self._other_session_ids():
            if self._is_alive(sid):
                continue
            path = self.autosave_path(sid)
            if not os.path.exists(path):
                self._remove_session_files(sid)
                continue
            info = {}
            try:
                with open(self.info_path(sid), encoding="utf-8") as f:
                    info = json.load(f)
            except (OSError, ValueError):
                pass
            st = os.stat(path)
            found.append({"session": sid, "saved_at": st.st_mtime, "size": st.st_size, "path": path,
                          "app_version": info.get("app_version", "")})
        found.sort(key=lambda f: f["saved_at"], reverse=True)
        return found

    def discard(self, session):
        self._remove_session_files(session["session"])

    def _remove_session_files(self, sid):
        for path in (self.autosave_path(sid), self.info_path(sid), self.lock_path(sid)):
            _remove(path)
