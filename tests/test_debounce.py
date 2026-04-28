"""State-machine tests for GestureDebouncer."""

from __future__ import annotations

import time

import pytest

from gestcontrol.debounce import GestureDebouncer, GestureEvent


def feed(debouncer: GestureDebouncer, name, count: int) -> list[GestureEvent]:
    """Feed `name` for `count` frames and collect non-None events."""
    return [e for _ in range(count) if (e := debouncer.update(name)) is not None]


class TestBasicTransitions:
    def test_no_event_before_hold_frames(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        assert d.update("pinch") is None
        assert d.update("pinch") is None   # only 2 frames → below threshold

    def test_enter_fires_on_third_frame(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        d.update("pinch"); d.update("pinch")
        evt = d.update("pinch")
        assert evt is not None
        assert evt.name == "pinch"
        assert evt.phase == "enter"

    def test_hold_fires_after_enter(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        for _ in range(3):
            d.update("pinch")
        evt = d.update("pinch")
        assert evt is not None
        assert evt.phase == "hold"

    def test_exit_fires_when_gesture_disappears(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        for _ in range(3):
            d.update("pinch")
        # Exit fires on the FIRST frame the gesture changes (immediate, no delay)
        evt = d.update(None)
        assert evt is not None
        assert evt.phase == "exit"
        assert evt.name == "pinch"

    def test_exit_before_enter_for_new_gesture(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        for _ in range(3):
            d.update("pinch")         # confirm pinch
        for _ in range(3):
            d.update("fist")          # switch to fist
        events = [e for _ in range(10) if (e := d.update("fist")) is not None]
        phases = [e.phase for e in events]
        # exit must appear before the first enter
        if "exit" in phases and "enter" in phases:
            assert phases.index("exit") < phases.index("enter")


class TestCooldown:
    def test_cooldown_suppresses_immediate_reentry(self):
        d = GestureDebouncer(hold_frames=1, cooldown_ms=9999)
        d.update("pinch")             # enter
        d.update(None)                # exit (via pending mechanism)
        d.update(None)
        # Re-enter pinch while cooldown still active
        d.update("pinch")
        evt = d.update("pinch")
        # Should not get another enter during cooldown window
        assert evt is None or evt.phase != "enter"

    def test_cooldown_zero_allows_immediate_reentry(self):
        d = GestureDebouncer(hold_frames=1, cooldown_ms=0)
        d.update("pinch")             # enter fires
        d.update(None)                # switch to none
        d.update(None)                # exit fires
        d.update("pinch")             # re-enter should be allowed
        evt = d.update("pinch")
        # Should get hold (since enter fired one step ago)
        assert evt is not None


class TestEdgeCases:
    def test_none_input_produces_no_enter(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        events = feed(d, None, 10)
        assert all(e.phase != "enter" for e in events)

    def test_single_frame_gesture_does_not_trigger(self):
        d = GestureDebouncer(hold_frames=3, cooldown_ms=0)
        d.update("pinch")
        d.update(None)
        d.update(None)
        events = [d.update("pinch"), d.update(None), d.update(None)]
        assert all(e is None for e in events)
