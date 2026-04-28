"""YAML config loader with fail-loud schema validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

VALID_ACTIONS = {"cursor_move", "mouse_drag", "mouse_click", "key_shortcut", "media_key"}
REQUIRED_FIELDS: dict[str, list[str]] = {
    "cursor_move": [],
    "mouse_drag": ["button"],
    "mouse_click": ["button"],
    "key_shortcut": ["keys"],
    "media_key": ["key"],
}
VALID_BUTTONS     = {"left", "right", "middle"}
VALID_PHASES      = {"enter", "hold", "exit"}
VALID_MEDIA_KEYS  = {"play_pause", "volume_up", "volume_down", "mute", "next_track", "prev_track"}


def load_gestures(path: str | Path) -> dict[str, Any]:
    data = _read(path)
    gestures = data.get("gestures") or {}
    for name, spec in gestures.items():
        _validate(name, spec, path)
    return gestures


def load_settings(path: str | Path) -> dict[str, Any]:
    return _read(path)


def _read(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p.resolve()}")
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _validate(name: str, spec: dict, source: str | Path) -> None:
    def err(msg: str) -> ValueError:
        return ValueError(f"[{source}] gesture '{name}': {msg}")

    action = spec.get("action")
    if action not in VALID_ACTIONS:
        raise err(f"unknown action '{action}'. Valid: {sorted(VALID_ACTIONS)}")

    for field in REQUIRED_FIELDS[action]:
        if field not in spec:
            raise err(f"action '{action}' requires field '{field}'")

    if "trigger" in spec and spec["trigger"] not in VALID_PHASES:
        raise err(f"'trigger' must be one of {VALID_PHASES}, got '{spec['trigger']}'")

    if action in ("mouse_click", "mouse_drag") and spec.get("button") not in VALID_BUTTONS:
        raise err(f"'button' must be 'left', 'right', or 'middle', got '{spec.get('button')}'")

    if action == "media_key" and spec.get("key") not in VALID_MEDIA_KEYS:
        raise err(f"'key' must be one of {sorted(VALID_MEDIA_KEYS)}")
