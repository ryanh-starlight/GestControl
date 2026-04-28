"""Shared test helpers."""

from __future__ import annotations

import json
from pathlib import Path

from gestcontrol.gesture_classifier import Landmark

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"


def load_fixture(name: str) -> tuple[list[Landmark], str]:
    """Load a landmark fixture JSON and return (landmarks, handedness)."""
    data = json.loads((FIXTURES / f"{name}.json").read_text())
    lms = [Landmark(**lm) for lm in data["landmarks"]]
    return lms, data["handedness"]
