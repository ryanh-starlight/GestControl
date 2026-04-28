"""Tests for config_loader validation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from gestcontrol.config_loader import load_gestures, load_settings


def write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.yaml"
    p.write_text(textwrap.dedent(content))
    return str(p)


class TestLoadGestures:
    def test_loads_valid_gesture_file(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              pinch:
                action: mouse_click
                button: left
                on: enter
        """)
        cfg = load_gestures(p)
        assert "pinch" in cfg
        assert cfg["pinch"]["action"] == "mouse_click"

    def test_unknown_action_raises(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              weird:
                action: teleport
        """)
        with pytest.raises(ValueError, match="unknown action"):
            load_gestures(p)

    def test_missing_required_field_raises(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              click:
                action: mouse_click
        """)
        with pytest.raises(ValueError, match="requires field 'button'"):
            load_gestures(p)

    def test_invalid_phase_raises(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              pinch:
                action: mouse_click
                button: left
                trigger: whenever
        """)
        with pytest.raises(ValueError, match="'trigger' must be"):
            load_gestures(p)

    def test_invalid_button_raises(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              pinch:
                action: mouse_click
                button: scroll
        """)
        with pytest.raises(ValueError, match="'button' must be"):
            load_gestures(p)

    def test_invalid_media_key_raises(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              palm:
                action: media_key
                key: rewind
        """)
        with pytest.raises(ValueError, match="'key' must be"):
            load_gestures(p)

    def test_mouse_drag_valid(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              pinch:
                action: mouse_drag
                button: left
        """)
        cfg = load_gestures(p)
        assert cfg["pinch"]["action"] == "mouse_drag"

    def test_mouse_drag_requires_button(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              pinch:
                action: mouse_drag
        """)
        with pytest.raises(ValueError, match="requires field 'button'"):
            load_gestures(p)

    def test_win_tab_shortcut_valid(self, tmp_path):
        p = write_yaml(tmp_path, """\
            gestures:
              three_fingers:
                action: key_shortcut
                keys: [win, tab]
                trigger: enter
        """)
        cfg = load_gestures(p)
        assert cfg["three_fingers"]["keys"] == ["win", "tab"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_gestures(str(tmp_path / "nonexistent.yaml"))

    def test_empty_gestures_block(self, tmp_path):
        p = write_yaml(tmp_path, "gestures:\n")
        cfg = load_gestures(p)
        assert cfg == {}


class TestLoadSettings:
    def test_loads_nested_settings(self, tmp_path):
        p = write_yaml(tmp_path, """\
            smoothing:
              alpha: 0.4
            osc:
              action_port: 9000
        """)
        s = load_settings(p)
        assert s["smoothing"]["alpha"] == pytest.approx(0.4)
        assert s["osc"]["action_port"] == 9000
