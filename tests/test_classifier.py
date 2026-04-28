"""Integration tests: fixture landmarks → RuleBasedClassifier → gesture name."""

from __future__ import annotations

import pytest
from conftest import load_fixture

from gestcontrol.gesture_classifier import RuleBasedClassifier


@pytest.fixture
def clf():
    return RuleBasedClassifier()


@pytest.mark.parametrize("fixture,expected", [
    ("index_point",  "index_point"),
    ("pinch",        "pinch"),
    ("fist",         "fist"),
    ("open_palm",    "open_palm"),
    ("three_fingers", "three_fingers"),
    ("four_fingers",  "four_fingers"),
    ("curl_click",   "curl_click"),
])
def test_gesture_classification(clf, fixture, expected):
    lms, handedness = load_fixture(fixture)
    result = clf.classify(lms, handedness)
    assert result is not None, f"No gesture returned for fixture '{fixture}'"
    assert result.name == expected, (
        f"Fixture '{fixture}': expected '{expected}', got '{result.name}'"
    )


def test_returns_none_for_wrong_landmark_count(clf):
    from gestcontrol.gesture_classifier import Landmark
    assert clf.classify([], "Right") is None
    assert clf.classify([Landmark(0, 0, 0)] * 10, "Right") is None


def test_gesture_has_confidence(clf):
    lms, hand = load_fixture("pinch")
    g = clf.classify(lms, hand)
    assert 0.0 <= g.confidence <= 1.0


def test_pinch_payload_contains_distance(clf):
    lms, hand = load_fixture("pinch")
    g = clf.classify(lms, hand)
    assert "distance" in g.payload
    assert g.payload["distance"] < 0.07


def test_four_fingers_not_confused_with_three(clf):
    lms, hand = load_fixture("four_fingers")
    g = clf.classify(lms, hand)
    assert g is not None and g.name == "four_fingers"


def test_three_fingers_not_confused_with_four(clf):
    lms, hand = load_fixture("three_fingers")
    g = clf.classify(lms, hand)
    assert g is not None and g.name == "three_fingers"
