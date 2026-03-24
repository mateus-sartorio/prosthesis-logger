from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from queue import Queue
from typing import Callable

from mqtt_logger.models import EventLevel


@dataclass(slots=True)
class ControlAction:
    kind: str
    value: str | None = None


class RuntimeController:
    def __init__(
        self,
        action_queue: Queue[ControlAction],
        prompt_text: Callable[[str], str],
    ) -> None:
        self._action_queue = action_queue
        self._prompt_text = prompt_text
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="runtime-controls")

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            key = _read_single_key_nonblocking()
            if key is None:
                time.sleep(0.05)
                continue

            if key == "h":
                self._action_queue.put(ControlAction(kind="help"))
            elif key == "q":
                self._action_queue.put(ControlAction(kind="quit"))
            elif key == "c":
                self._action_queue.put(ControlAction(kind="clear"))
            elif key == "0":
                self._action_queue.put(ControlAction(kind="set_min_level", value=""))
            elif key == "1":
                self._action_queue.put(ControlAction(kind="set_min_level", value=EventLevel.NORMAL.value))
            elif key == "2":
                self._action_queue.put(ControlAction(kind="set_min_level", value=EventLevel.WARNING.value))
            elif key == "3":
                self._action_queue.put(ControlAction(kind="set_min_level", value=EventLevel.ERROR.value))
            elif key == "t":
                values = self._prompt_text("sensor_type filter (comma separated, empty to clear): ").strip()
                self._action_queue.put(ControlAction(kind="set_sensor_types", value=values))
            elif key == "n":
                values = self._prompt_text("sensor_name filter (comma separated, empty to clear): ").strip()
                self._action_queue.put(ControlAction(kind="set_sensor_names", value=values))


def _read_single_key_nonblocking() -> str | None:
    if sys.platform.startswith("win"):
        import msvcrt

        if msvcrt.kbhit():
            key = msvcrt.getwch()
            return key.lower()
        return None

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        readable, _, _ = select.select([sys.stdin], [], [], 0)
        if readable:
            key = sys.stdin.read(1)
            return key.lower()
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
