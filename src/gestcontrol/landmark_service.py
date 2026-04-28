"""Landmark extraction + gesture classification process entry point.

Grabs frames from the webcam via OpenCV, runs MediaPipe Hands, classifies
gestures, and forwards events over OSC to the action server.

Run as:  python -m gestcontrol.landmark_service [--no-pip]

Press 'q' in the PIP window (or Ctrl-C in the terminal) to exit cleanly.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from typing import Optional

import cv2
import numpy as np

from .config_loader import load_settings
from .debounce import GestureDebouncer
from .gesture_classifier import RuleBasedClassifier
from .landmark_extractor import LandmarkExtractor
from .osc_io import OSCSender
from .pip_window import PIPWindow
from .smoothing import EMASmoother


def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.settings)

    mp_cfg   = settings.get("mediapipe", {})
    extractor = LandmarkExtractor(
        model_path=mp_cfg.get("model_path", "models/hand_landmarker.task"),
        min_detection_confidence=mp_cfg.get("min_detection_confidence", 0.7),
        min_tracking_confidence=mp_cfg.get("min_tracking_confidence", 0.5),
    )

    classifier = RuleBasedClassifier()

    dbc_cfg   = settings.get("debounce", {})
    debouncer = GestureDebouncer(
        hold_frames=dbc_cfg.get("hold_frames", 3),
        cooldown_ms=dbc_cfg.get("cooldown_ms", 300),
    )

    smt_cfg  = settings.get("smoothing", {})
    alpha    = smt_cfg.get("alpha", 0.35)
    flip_x   = smt_cfg.get("flip_x", True)
    smoother_x = EMASmoother(alpha)
    smoother_y = EMASmoother(alpha)

    # Active region — hand only needs to move in this normalised box to span
    # the full screen.  Coordinates are in the flip-corrected space (0=left-of-screen).
    ar      = settings.get("cursor", {}).get("active_region", {})
    ar_xmin = ar.get("x_min", 0.0)
    ar_xmax = ar.get("x_max", 1.0)
    ar_ymin = ar.get("y_min", 0.0)
    ar_ymax = ar.get("y_max", 1.0)

    osc_cfg  = settings.get("osc", {})
    action_osc = OSCSender(
        osc_cfg.get("action_host", "127.0.0.1"),
        osc_cfg.get("action_port", 9000),
    )

    pip_cfg = settings.get("pip", {})
    pip: Optional[PIPWindow] = None
    if args.pip and pip_cfg.get("enabled", True):
        pip = PIPWindow(
            width=pip_cfg.get("width", 320),
            height=pip_cfg.get("height", 240),
            corner=pip_cfg.get("corner", "top_right"),
            margin=pip_cfg.get("margin", 16),
            drawing_utils=extractor.drawing_utils,
            hand_connections=extractor.hand_connections,
        )

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {args.camera}")

    last_hb  = 0.0
    running  = True

    def _stop(sig=None, frame=None):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    print(f"[landmark_service] camera={args.camera}  pip={'on' if pip else 'off'}")

    try:
        while running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.005)
                continue

            result      = extractor.process(frame)
            raw_lms     = None
            gesture_name: Optional[str] = None

            if result is not None:
                landmarks, handedness, raw_lms = result
                gesture = classifier.classify(landmarks, handedness)
                gesture_name = gesture.name if gesture else None

                # Cursor movement: tracks during index_point AND pinch so
                # click-drag works while the mouse button is held.
                if gesture_name in ("index_point", "pinch"):
                    nx_raw = (1.0 - landmarks[8].x) if flip_x else landmarks[8].x
                    ny_raw = landmarks[8].y
                    # Map active region to [0, 1] — hand only needs to cross
                    # the configured box to drive the cursor edge-to-edge.
                    nx = max(0.0, min(1.0, (nx_raw - ar_xmin) / (ar_xmax - ar_xmin)))
                    ny = max(0.0, min(1.0, (ny_raw - ar_ymin) / (ar_ymax - ar_ymin)))
                    action_osc.send("/cursor/move", smoother_x.update(nx), smoother_y.update(ny))
                else:
                    smoother_x.reset()
                    smoother_y.reset()
            else:
                smoother_x.reset()
                smoother_y.reset()

            # Debounce → gesture events
            event = debouncer.update(gesture_name)
            if event:
                action_osc.send("/gesture/event", event.name, event.phase)

            # Heartbeat
            now = time.monotonic()
            if now - last_hb >= 1.0:
                action_osc.send("/heartbeat", now)
                last_hb = now

            # PIP overlay
            if pip is not None:
                if not pip.update(frame, raw_lms, gesture_name or ""):
                    break

    finally:
        if pip:
            pip.close()
        cap.release()
        extractor.close()
        print("[landmark_service] exited")


def main() -> None:
    if sys.platform != "win32":
        sys.exit("GestControl is Windows-only (see README for Mac notes).")

    parser = argparse.ArgumentParser(description="GestControl landmark service")
    parser.add_argument(
        "--settings", default="config/settings.yaml",
    )
    parser.add_argument("--pip",    dest="pip", action="store_true",  default=True)
    parser.add_argument("--no-pip", dest="pip", action="store_false")
    parser.add_argument("--camera", type=int, default=0,
                        help="Camera index")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
