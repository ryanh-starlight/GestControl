"""Convenience launcher: starts landmark_service + action_server as subprocesses.

Usage:
    python -m gestcontrol.run_all [--no-pip]
    python -m gestcontrol.run_all --dry-run
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="GestControl — launch all services")
    parser.add_argument("--pip",    dest="pip", action="store_true",  default=True)
    parser.add_argument("--no-pip", dest="pip", action="store_false")
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--config",   default="config/gestures.yaml")
    parser.add_argument("--camera",   type=int, default=0)
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    python = sys.executable

    lm_cmd = [
        python, "-m", "gestcontrol.landmark_service",
        "--settings", args.settings,
        "--camera", str(args.camera),
    ]
    if not args.pip:
        lm_cmd.append("--no-pip")

    as_cmd = [
        python, "-m", "gestcontrol.action_server",
        "--config",   args.config,
        "--settings", args.settings,
    ]

    if args.dry_run:
        print(f"[dry-run] Would launch: {' '.join(lm_cmd)}")
        print(f"[dry-run] Would launch: {' '.join(as_cmd)}")
        return

    procs: list[subprocess.Popen] = []

    def _cleanup(sig=None, frame=None) -> None:
        print("\n[run_all] shutting down...")
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    # Action server first so it is ready before landmark_service sends OSC
    procs.append(subprocess.Popen(as_cmd))
    time.sleep(0.4)
    procs.append(subprocess.Popen(lm_cmd))

    print("[run_all] services started — press Ctrl-C or 'q' in PIP window to stop")

    while True:
        for p in procs:
            code = p.poll()
            if code is not None:
                print(f"[run_all] PID {p.pid} exited with code {code}")
        time.sleep(2)


if __name__ == "__main__":
    main()
