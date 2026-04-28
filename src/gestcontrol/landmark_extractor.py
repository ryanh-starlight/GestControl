"""MediaPipe Hands wrapper — Tasks API (mediapipe >= 0.10).

mp.solutions was removed in mediapipe 0.10+.  This module uses the Tasks API
with a downloaded hand_landmarker.task model file (see settings.yaml for path).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from .gesture_classifier import Landmark

_vision     = mp.tasks.vision
_du         = _vision.drawing_utils
_HAND_CONN  = _vision.HandLandmarksConnections.HAND_CONNECTIONS


class LandmarkExtractor:
    def __init__(
        self,
        model_path: str = "models/hand_landmarker.task",
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Hand landmarker model not found: {model_path}\n"
                "Download it with:\n"
                "  python -c \"import urllib.request; urllib.request.urlretrieve("
                "'https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                "hand_landmarker/float16/1/hand_landmarker.task', 'models/hand_landmarker.task')\""
            )

        base_opts = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = _vision.HandLandmarkerOptions(
            base_options=base_opts,
            running_mode=_vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = _vision.HandLandmarker.create_from_options(options)
        self._start_ms   = int(time.monotonic() * 1000)

        # Expose drawing utilities so pip_window stays decoupled from mp imports
        self.drawing_utils   = _du
        self.hand_connections = _HAND_CONN

    def process(
        self, frame: np.ndarray
    ) -> Optional[tuple[list[Landmark], str, list]]:
        """Process one BGR frame.

        Returns (landmarks, handedness, raw_landmark_list) or None.
        raw_landmark_list is the Tasks API list[NormalizedLandmark] used by
        drawing_utils.draw_landmarks for the PIP overlay.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image   = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp  = int(time.monotonic() * 1000) - self._start_ms
        result     = self._landmarker.detect_for_video(mp_image, timestamp)

        if not result.hand_landmarks:
            return None

        raw       = result.hand_landmarks[0]          # list[NormalizedLandmark]
        handedness = result.handedness[0][0].category_name  # "Left" | "Right"
        landmarks  = [Landmark(lm.x, lm.y, lm.z) for lm in raw]
        return landmarks, handedness, raw

    def close(self) -> None:
        self._landmarker.close()
