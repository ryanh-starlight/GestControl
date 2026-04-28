"""Maps gesture events and cursor-move messages to OS-level actions.

Uses pynput for mouse control and media/modifier keys, pyautogui for
multi-key shortcuts.  The dispatcher is initialised with the gesture config
and a VirtualDesktop instance; it is called from the OSC server thread.
"""

from __future__ import annotations

import time
from typing import Any

import pyautogui
from pynput import keyboard as kb
from pynput import mouse as ms
from pynput.keyboard import Key, KeyCode

from .config_loader import load_gestures, load_settings
from .screen import VirtualDesktop

# pyautogui moves the cursor to (0, 0) on import unless FAILSAFE is disabled.
# Win+L is the safe panic-exit: it locks the screen without killing the process.
pyautogui.FAILSAFE = False

# Maps YAML key names → pynput Key objects
_KEY_MAP: dict[str, Key] = {
    "win": Key.cmd, "winleft": Key.cmd_l, "winright": Key.cmd_r,
    "shift": Key.shift, "lshift": Key.shift_l, "rshift": Key.shift_r,
    "ctrl": Key.ctrl,  "lctrl": Key.ctrl_l,  "rctrl": Key.ctrl_r,
    "alt": Key.alt,    "lalt": Key.alt_l,    "ralt": Key.alt_r,
    "tab": Key.tab, "enter": Key.enter, "esc": Key.esc,
    "space": Key.space, "backspace": Key.backspace, "delete": Key.delete,
    "left": Key.left,  "right": Key.right, "up": Key.up,   "down": Key.down,
    "home": Key.home,  "end": Key.end,
    "pageup": Key.page_up, "pagedown": Key.page_down,
    **{f"f{n}": getattr(Key, f"f{n}") for n in range(1, 13)},
    # Media
    "play_pause": Key.media_play_pause,
    "volume_up":  Key.media_volume_up,
    "volume_down": Key.media_volume_down,
    "mute": Key.media_volume_mute,
    "next_track": Key.media_next,
    "prev_track": Key.media_previous,
}


_BUTTON_MAP = {"left": ms.Button.left, "right": ms.Button.right, "middle": ms.Button.middle}


def _resolve_button(name: str) -> ms.Button:
    return _BUTTON_MAP.get(name, ms.Button.left)


def _resolve(name: str) -> Key | KeyCode:
    if name in _KEY_MAP:
        return _KEY_MAP[name]
    if len(name) == 1:
        return KeyCode.from_char(name)
    raise ValueError(f"Unknown key name in config: '{name}'")


class ActionDispatcher:
    def __init__(self, gestures_path: str, settings_path: str) -> None:
        self._config   = load_gestures(gestures_path)
        settings       = load_settings(settings_path)
        self._desktop  = VirtualDesktop()
        self._deadzone = settings.get("screen", {}).get("deadzone", 0.05)
        self._mouse    = ms.Controller()
        self._keyboard = kb.Controller()
        self._last_repeat: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API — called from OSC handlers
    # ------------------------------------------------------------------

    def on_gesture_event(self, name: str, phase: str) -> None:
        spec = self._config.get(name)
        if spec is None:
            return

        action = spec["action"]

        if action == "cursor_move":
            return

        # mouse_drag fires on both enter (press) and exit (release), bypassing
        # the normal trigger gate so the button stays held between the two events.
        if action == "mouse_drag":
            btn = _resolve_button(spec.get("button", "left"))
            if phase == "enter":
                self._mouse.press(btn)
            elif phase == "exit":
                self._mouse.release(btn)
            return

        on_phase = spec.get("trigger", "enter")
        if not self._should_fire(name, phase, on_phase, spec):
            return

        self._dispatch(action, spec)

    def on_cursor_move(self, norm_x: float, norm_y: float) -> None:
        x, y = self._desktop.to_screen(norm_x, norm_y, deadzone=self._deadzone)
        self._mouse.position = (x, y)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_fire(
        self, name: str, phase: str, on_phase: str, spec: dict[str, Any]
    ) -> bool:
        if phase == on_phase and phase in ("enter", "exit"):
            return True
        if phase == "hold" and on_phase == "hold":
            repeat_ms = spec.get("repeat_ms", 200)
            now_ms    = time.monotonic() * 1000
            last      = self._last_repeat.get(name, 0.0)
            if now_ms - last >= repeat_ms:
                self._last_repeat[name] = now_ms
                return True
        return False

    def _dispatch(self, action: str, spec: dict[str, Any]) -> None:
        if action == "mouse_click":
            btn = _resolve_button(spec.get("button", "left"))
            self._mouse.click(btn)

        elif action == "key_shortcut":
            keys = [_resolve(k) for k in spec.get("keys", [])]
            for key in keys:
                self._keyboard.press(key)
            for key in reversed(keys):
                self._keyboard.release(key)

        elif action == "media_key":
            key = _KEY_MAP.get(spec.get("key", ""))
            if key:
                self._keyboard.press(key)
                self._keyboard.release(key)
