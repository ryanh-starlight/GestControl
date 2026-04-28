# GestControl

Real-time hand gesture OS control — Windows 11, Python 3.10, MediaPipe, TouchDesigner 2023+.

## How it works

```
Webcam → TouchDesigner (Spout Out) → landmark_service.py (MediaPipe + classifier)
      → action_server.py (pynput / pyautogui) → mouse, keyboard, media keys
      → TouchDesigner OSC In (landmark overlay, gesture label)
```

A small always-on-top PIP window shows the live webcam feed with skeleton overlay
and active gesture label for real-time feedback.

---

## Quick start

### 1 — Install

```bash
# Python 3.10 only (MediaPipe wheel requirement)
python -m venv .venv
.venv\Scripts\activate

pip install -e .
```

### 2 — Test without camera or TouchDesigner

```bash
pytest
```

All tests run offline (no camera, no TD, no OSC).

### 3 — Test with webcam only (no TD needed)

```bash
python -m gestcontrol.run_all --source opencv
```

The PIP window opens top-right.  Gesture with your hand — the cursor should
follow your index finger and click on pinch.  Press `q` in the PIP window or
`Ctrl-C` in the terminal to stop.

### 4 — Full setup with TouchDesigner

1. Follow the step-by-step guide in `td/td_setup.md`.
2. Run the Python services first, then open the `.toe` project:

```bash
python -m gestcontrol.run_all --source spout
```

---

## Supported gestures (default mapping)

| Gesture | Action |
|---|---|
| Index finger point | Move mouse cursor |
| Pinch (thumb + index) | Left click (on gesture enter) |
| Fist | Right click |
| Peace sign (✌) | Win + Shift + S (Snip & Sketch screenshot) |
| Open palm | Play / pause media |
| Thumbs up | Volume up (held) |
| Thumbs down | Volume down (held) |

Edit `config/gestures.yaml` to remap any gesture — no Python edits required.

---

## Config files

| File | What to change |
|---|---|
| `config/gestures.yaml` | Gesture → OS action mapping |
| `config/settings.yaml` | Smoothing, debounce thresholds, OSC ports, PIP size/position |

### Adding a new gesture

1. Implement the geometry rule in `src/gestcontrol/gestures_rules.py`.
2. Add the priority branch in `RuleBasedClassifier.classify()` in `gesture_classifier.py`.
3. Add the mapping entry in `config/gestures.yaml`.
4. Add a fixture JSON in `tests/fixtures/landmarks/` and a test case.

---

## Troubleshooting

### Webcam already in use
> `Cannot open camera index 0`

Another app (Teams, Zoom, OBS) has grabbed the webcam.  Either close it or pass
`--camera 1` to use a second device index.

### Spout receiver not connecting
> Spout Out TOP in TD shows "No receivers"

Verify:
- Python is running (`run_all.py` started before TD was opened)
- Sender name in TD's Spout Out TOP is exactly `GestControl_Frames`
- Both apps are on the same physical machine (Spout is GPU shared memory, not network)

### Cursor stops moving after releasing index_point
This is expected — the EMA smoother resets when no hand is detected.  The cursor
stays at the last smoothed position.

### pyautogui / pynput blocked by UAC-elevated window
OS-level input injection cannot target a window running at higher UAC level.
Run `action_server.py` as Administrator, or lower the target app's UAC level.

### Panic exit (cursor stuck)
Press **Win + L** to lock the screen — this terminates focus on any gesture-controlled
window and lets you unlock normally.  `FAILSAFE = False` is intentional; moving
the cursor to a corner with `FAILSAFE = True` would crash the action server.

---

## Platform

**Windows 11 only.**  Spout (GPU shared memory) is Windows-exclusive.  A Mac port
would require swapping Spout → Syphon and granting `pynput` Accessibility
permissions in System Settings.  Linux is not supported.

---

## Future: ML gesture classifier

Run `python -m gestcontrol.record_dataset --gesture pinch --frames 200` to collect
labeled landmark snapshots into `data/samples.csv`.  A scikit-learn classifier
(install with `pip install -e ".[ml]"`) can replace `RuleBasedClassifier` behind
the `Classifier` ABC without touching the service loop.
