"""Tests for the active-region cursor coordinate mapping formula."""

from __future__ import annotations

import pytest


def _map(val: float, lo: float, hi: float) -> float:
    """Same formula as in landmark_service.run()."""
    return max(0.0, min(1.0, (val - lo) / (hi - lo)))


@pytest.mark.parametrize("val,lo,hi,expected", [
    (0.20, 0.20, 0.80, 0.0),    # at lower edge → 0
    (0.80, 0.20, 0.80, 1.0),    # at upper edge → 1
    (0.50, 0.20, 0.80, 0.5),    # midpoint → 0.5
    (0.10, 0.20, 0.80, 0.0),    # below range → clipped to 0
    (0.90, 0.20, 0.80, 1.0),    # above range → clipped to 1
    (0.35, 0.20, 0.80, 0.25),   # quarter way in
    (0.65, 0.20, 0.80, 0.75),   # three-quarters in
])
def test_map_region(val, lo, hi, expected):
    assert _map(val, lo, hi) == pytest.approx(expected, abs=1e-6)


def test_full_range_is_identity():
    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        assert _map(v, 0.0, 1.0) == pytest.approx(v)


def test_narrow_active_region_amplifies_movement():
    # A 10% region (0.45–0.55) maps to full [0, 1].
    # Hand moves 0.05 units → cursor moves 0.5 units = 10x gain.
    assert _map(0.45, 0.45, 0.55) == pytest.approx(0.0)
    assert _map(0.55, 0.45, 0.55) == pytest.approx(1.0)
    assert _map(0.50, 0.45, 0.55) == pytest.approx(0.5)
