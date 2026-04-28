"""Gesture debouncer: converts a stream of per-frame classifier outputs into
discrete enter / hold / exit events with configurable stability requirements.

Timeline for a pinch gesture:
  frames: --- pinch pinch pinch pinch pinch pinch none none ---
  events:             [enter]  [hold] [hold]       [exit]

The debouncer requires `hold_frames` consecutive frames of the same gesture
before firing `enter`, then emits `hold` on every subsequent frame while the
gesture persists.  After the gesture disappears for `hold_frames` frames it
fires `exit`.  A `cooldown_ms` gate prevents the same gesture immediately
re-triggering `enter` (useful for click suppression on held pinch).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class GestureEvent:
    name: str
    phase: str  # "enter" | "hold" | "exit"


class GestureDebouncer:
    def __init__(self, hold_frames: int = 3, cooldown_ms: float = 300) -> None:
        self.hold_frames = hold_frames
        self.cooldown_ms = cooldown_ms

        self._confirmed: Optional[str] = None   # currently active gesture
        self._candidate: Optional[str] = None   # gesture being observed
        self._count: int = 0                    # consecutive frames of candidate
        self._last_enter_ms: float = 0.0

    def update(self, name: Optional[str]) -> Optional[GestureEvent]:
        """Feed one frame's classifier output.  Returns at most one event.

        Exit fires on the first frame the gesture changes — no hold-frames delay
        for release (fast response).  Enter still requires hold_frames stability.
        """
        now_ms = time.monotonic() * 1000

        # Update candidate streak
        if name == self._candidate:
            self._count += 1
        else:
            self._candidate = name
            self._count = 1

        # Active gesture ended → exit immediately on the first change frame
        if self._confirmed is not None and self._candidate != self._confirmed:
            old = self._confirmed
            self._confirmed = None
            return GestureEvent(old, "exit")

        # Active gesture still held → hold
        if self._confirmed is not None:
            return GestureEvent(self._confirmed, "hold")

        # No active gesture — try to confirm the candidate once it stabilises
        if self._candidate is not None and self._count >= self.hold_frames:
            if now_ms - self._last_enter_ms < self.cooldown_ms:
                return None
            self._confirmed = self._candidate
            self._last_enter_ms = now_ms
            return GestureEvent(self._confirmed, "enter")

        return None
