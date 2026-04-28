"""Pure geometric primitives for the rule-based classifier.

All functions accept the raw list[Landmark] produced by LandmarkExtractor and
return plain Python scalars so tests can run without importing MediaPipe.

MediaPipe normalised coordinate system:
  - x grows right, y grows DOWN (image space), z is depth (smaller = closer)
  - Landmark indices: 0=WRIST, 1-4=THUMB, 5-8=INDEX, 9-12=MIDDLE,
    13-16=RING, 17-20=PINKY
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gesture_classifier import Landmark


def finger_extended(landmarks: list, *, tip: int, pip: int) -> bool:
    """True when the fingertip is above (y <) its PIP joint — finger is up."""
    return landmarks[tip].y < landmarks[pip].y


def pinch_distance(landmarks: list) -> float:
    """Euclidean distance (normalised) between thumb tip (4) and index tip (8)."""
    t = landmarks[4]
    i = landmarks[8]
    return math.hypot(t.x - i.x, t.y - i.y)


def thumb_extended(landmarks: list) -> float:
    """True when the thumb tip is far enough from the index MCP.

    Handedness-agnostic: measures distance rather than a directional comparison,
    so it works for both hands without flipping logic.
    """
    tip      = landmarks[4]   # THUMB_TIP
    idx_mcp  = landmarks[5]   # INDEX_FINGER_MCP
    return math.hypot(tip.x - idx_mcp.x, tip.y - idx_mcp.y) > 0.15


def palm_facing_camera(landmarks: list) -> bool:
    """Rough palm-orientation check using the wrist→index_mcp→pinky_mcp triangle.

    Positive cross-product Z component means the vertices are in
    counter-clockwise order, which corresponds to palm-toward-camera.
    """
    w = landmarks[0]
    i = landmarks[5]
    p = landmarks[17]
    cross_z = (i.x - w.x) * (p.y - w.y) - (i.y - w.y) * (p.x - w.x)
    return cross_z > 0
