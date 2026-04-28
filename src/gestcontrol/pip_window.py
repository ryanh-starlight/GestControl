"""Always-on-top picture-in-picture overlay window using OpenCV.

Renders the live webcam frame with the MediaPipe skeleton overlay and active
gesture label.  Works with the Tasks API (mediapipe >= 0.10) drawing utils.

IMPORTANT: OpenCV imshow/waitKey must be called from the *same thread* that
created the window.  Run everything in the main loop — do not move to a thread.
"""

from __future__ import annotations

import ctypes
import sys
import time
from typing import Any, Optional

import cv2
import numpy as np


class PIPWindow:
    _NAME = "GestControl PIP"

    def __init__(
        self,
        width: int = 320,
        height: int = 240,
        corner: str = "top_right",
        margin: int = 16,
        drawing_utils: Any = None,       # mp.tasks.vision.drawing_utils
        hand_connections: Any = None,    # HandLandmarksConnections.HAND_CONNECTIONS
    ) -> None:
        self.width  = width
        self.height = height
        self._corner  = corner
        self._margin  = margin
        self._du      = drawing_utils
        self._conns   = hand_connections
        self._fps     = _FPSCounter()

        cv2.namedWindow(self._NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._NAME, width, height)
        cv2.setWindowProperty(self._NAME, cv2.WND_PROP_TOPMOST, 1)
        self._position_window()

    def _position_window(self) -> None:
        if sys.platform != "win32":
            return
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        m  = self._margin
        positions = {
            "top_right":    (sw - self.width  - m, m),
            "top_left":     (m, m),
            "bottom_right": (sw - self.width  - m, sh - self.height - m),
            "bottom_left":  (m, sh - self.height - m),
        }
        x, y = positions.get(self._corner, positions["top_right"])
        cv2.moveWindow(self._NAME, x, y)

    def update(
        self,
        frame: np.ndarray,
        raw_landmarks: Optional[list],   # Tasks API list[NormalizedLandmark] or None
        gesture_name: str,
    ) -> bool:
        """Draw frame with overlay and display.  Returns False when user presses 'q'."""
        display = cv2.resize(frame, (self.width, self.height))

        if raw_landmarks is not None and self._du is not None:
            self._du.draw_landmarks(
                display,
                raw_landmarks,
                self._conns,
            )

        fps   = self._fps.tick()
        label = f"{gesture_name or 'none'}  {fps:.0f}fps"
        cv2.putText(
            display, label, (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
        )

        cv2.imshow(self._NAME, display)
        return cv2.waitKey(1) & 0xFF != ord("q")

    def close(self) -> None:
        cv2.destroyWindow(self._NAME)


class _FPSCounter:
    def __init__(self, smoothing: float = 0.9) -> None:
        self._last  = time.monotonic()
        self._fps   = 0.0
        self._alpha = smoothing

    def tick(self) -> float:
        now = time.monotonic()
        dt  = now - self._last
        self._last = now
        if dt > 0:
            self._fps = self._alpha * self._fps + (1 - self._alpha) / dt
        return self._fps
