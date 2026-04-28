"""Gesture classifier: ABC + rule-based implementation.

The Classifier ABC decouples the rule engine from the service loop so a
scikit-learn classifier can replace RuleBasedClassifier without touching
landmark_service.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from . import gestures_rules as rules


@dataclass
class Landmark:
    x: float
    y: float
    z: float


@dataclass
class Gesture:
    name: str
    confidence: float = 1.0
    payload: dict[str, Any] = field(default_factory=dict)


class Classifier(ABC):
    @abstractmethod
    def classify(
        self, landmarks: list[Landmark], handedness: str
    ) -> Optional[Gesture]:
        """Return the best matching Gesture or None."""


class RuleBasedClassifier(Classifier):
    """Geometric rule engine operating on raw MediaPipe landmark lists."""

    PINCH_THRESHOLD = 0.07        # normalised distance, thumb-tip ↔ index-tip

    def classify(
        self, landmarks: list[Landmark], handedness: str
    ) -> Optional[Gesture]:
        if len(landmarks) != 21:
            return None

        idx_ext  = rules.finger_extended(landmarks, tip=8,  pip=6)
        mid_ext  = rules.finger_extended(landmarks, tip=12, pip=10)
        rng_ext  = rules.finger_extended(landmarks, tip=16, pip=14)
        pnk_ext  = rules.finger_extended(landmarks, tip=20, pip=18)
        pinch_d  = rules.pinch_distance(landmarks)
        thm_ext  = rules.thumb_extended(landmarks)

        fingers_up = sum([idx_ext, mid_ext, rng_ext, pnk_ext])
        all_curled = fingers_up == 0

        # Priority order — more specific gestures first
        if pinch_d < self.PINCH_THRESHOLD and not mid_ext:
            return Gesture("pinch", payload={"distance": round(pinch_d, 3)})

        # open_palm before four_fingers: thumb extension decides which wins,
        # preventing a spurious four_fingers flash while the palm is opening.
        if fingers_up >= 4 and thm_ext:
            return Gesture("open_palm")

        if idx_ext and mid_ext and rng_ext and pnk_ext and not thm_ext:
            return Gesture("four_fingers")

        if idx_ext and mid_ext and rng_ext and not pnk_ext and not thm_ext:
            return Gesture("three_fingers")

        # curl_click: index + pinky extended (horns shape), middle + ring curled.
        # Distinct from index_point — no overlap, no flicker risk on cursor movement.
        if idx_ext and pnk_ext and not mid_ext and not rng_ext:
            return Gesture("curl_click")

        if idx_ext and not mid_ext and not rng_ext and not pnk_ext:
            return Gesture("index_point")

        if all_curled:
            return Gesture("fist")

        return None
