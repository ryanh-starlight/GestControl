"""Cursor-position smoothing via exponential moving average."""

from __future__ import annotations

from typing import Optional


class EMASmoother:
    """Exponential moving average: new_value = alpha * raw + (1-alpha) * prev.

    alpha=1.0 → no smoothing (raw passthrough).
    alpha=0.35 → good balance of lag vs jitter for 30 fps cursor control.
    """

    def __init__(self, alpha: float = 0.35) -> None:
        if not 0 < alpha <= 1.0:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        self.alpha = alpha
        self._value: Optional[float] = None

    def update(self, value: float) -> float:
        if self._value is None:
            self._value = value
        else:
            self._value = self.alpha * value + (1.0 - self.alpha) * self._value
        return self._value

    def reset(self) -> None:
        """Call when no hand is detected so the next seen position starts fresh."""
        self._value = None

    @property
    def current(self) -> Optional[float]:
        return self._value
