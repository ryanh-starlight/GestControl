"""Tests for EMASmoother."""

from __future__ import annotations

import pytest

from gestcontrol.smoothing import EMASmoother


class TestEMASmoother:
    def test_first_update_returns_raw_value(self):
        s = EMASmoother(alpha=0.5)
        assert s.update(0.8) == pytest.approx(0.8)

    def test_convergence_to_constant_input(self):
        s = EMASmoother(alpha=0.5)
        for _ in range(50):
            s.update(1.0)
        assert s.current == pytest.approx(1.0, abs=0.001)

    def test_smoothing_damps_step_input(self):
        s = EMASmoother(alpha=0.35)
        s.update(0.0)
        # One step to 1.0 should land between 0 and 1
        v = s.update(1.0)
        assert 0.0 < v < 1.0

    def test_reset_clears_state(self):
        s = EMASmoother(alpha=0.5)
        s.update(0.5)
        s.reset()
        assert s.current is None
        # After reset, next value is accepted as-is
        assert s.update(0.9) == pytest.approx(0.9)

    def test_invalid_alpha_raises(self):
        with pytest.raises((ValueError, AssertionError)):
            EMASmoother(alpha=0.0)
        with pytest.raises((ValueError, AssertionError)):
            EMASmoother(alpha=1.5)

    def test_alpha_one_is_passthrough(self):
        s = EMASmoother(alpha=1.0)
        for v in [0.1, 0.5, 0.9, 0.3]:
            assert s.update(v) == pytest.approx(v)
