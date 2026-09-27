"""Single-process sequential runner shared by Streamlit and the local API."""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass, field
from typing import Callable, ClassVar


class StopTask(Exception):
    """Raised when the task is stopped by user."""

    pass


@dataclass
class TaskRunner:
    """Manages a background thread that executes a sequence of steps with pause/stop control."""

    # Public read-only state
    state: str = "idle"  # idle | running | paused | stopping | stopped | completed | error
    current_step: int = -1  # 0-indexed, -1 = not started
    total_steps: int = 0
    current_label: str = ""
    error_msg: str = ""
    pause_message: str = ""  # why the task paused itself, empty when the user paused it

    # Internal
    _pause_event: threading.Event = field(default_factory=threading.Event)
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None
    _steps: list = field(default_factory=list)

    # Class-level pointer to the currently executing runner so that long-running
    # core functions can call ``TaskRunner.check_cancel()`` without needing a
    # direct reference. The pointer is only meaningful inside the background
    # thread that ``start()`` launches.
    _current: ClassVar["TaskRunner | None"] = None

    def __post_init__(self):
        self._pause_event.set()  # not paused initially

    # ------ Cancellation helpers (called from core code) ------

    @classmethod
    def check_cancel(cls) -> None:
        """Block while paused and raise :class:`StopTask` if a stop was requested.

        Safe to call from any thread; becomes a no-op when no runner is active
        (e.g. when core scripts are invoked from the CLI).
        """
        runner = cls._current
        if runner is None:
            return
        # Block while paused so long loops freeze on pause too.
        runner._pause_event.wait()
        if runner._stop_event.is_set():
            raise StopTask()

    # ------ Control API ------

    def start(self, steps: list[tuple[str, Callable]]):
        """Start executing steps in a background thread.

        Args:
            steps: list of (label, callable) — each callable takes no args.
        """
        if self.is_active:
            raise RuntimeError("A task is already active")

        self._steps = steps
        self.total_steps = len(steps)
        self.current_step = -1
        self.current_label = ""
        self.error_msg = ""
        self.pause_message = ""
        self.state = "running"

        self._pause_event.set()
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self, message: str = ""):
        if self.state == "running":
            self._pause_event.clear()
            self.pause_message = message
            self.state = "paused"

    def resume(self):
        if self.state == "paused":
            self.pause_message = ""
            self._pause_event.set()
            self.state = "running"

    def stop(self):
        """Request stop. The task will halt before the next step."""
        if self.state in ("running", "paused"):
            self.state = "stopping"
            self.pause_message = ""
            self._stop_event.set()
            self._pause_event.set()  # unblock if paused so thread can exit

    def reset(self):
        """Reset to idle state (only when not running)."""
        if not self.is_active:
            self.state = "idle"
            self.current_step = -1
            self.total_steps = 0
            self.current_label = ""
            self.error_msg = ""
            self.pause_message = ""
            self._steps = []

    @property
    def is_active(self) -> bool:
        return self.state in ("running", "paused", "stopping") or bool(self._thread and self._thread.is_alive())

    @property
    def is_done(self) -> bool:
        return self.state in ("completed", "stopped", "error")

    @property
    def progress(self) -> float:
        """0.0 to 1.0"""
        if self.total_steps == 0:
            return 0.0
        return 1.0 if self.state == "completed" else max(self.current_step, 0) / self.total_steps

    # ------ Internal ------

    def _run(self):
        """Execute steps sequentially in background thread."""
        type(self)._current = self
        try:
            for i, (label, func) in enumerate(self._steps):
                # Check stop before each step
                if self._stop_event.is_set():
                    self.state = "stopped"
                    return

                # Block if paused
                self._pause_event.wait()

                # Check stop again after resume
                if self._stop_event.is_set():
                    self.state = "stopped"
                    return

                self.current_step = i
                self.current_label = label
                func()
                self.check_cancel()

            self.state = "completed"
        except StopTask:
            self.state = "stopped"
        except Exception as e:
            self.error_msg = str(e)
            self.state = "error"
            traceback.print_exc()
        finally:
            if type(self)._current is self:
                type(self)._current = None
