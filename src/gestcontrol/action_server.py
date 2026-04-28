"""OS-action process entry point.

Listens on OSC UDP port 9000 (configurable in settings.yaml) and routes
/gesture/event and /cursor/move messages to ActionDispatcher.

Run as:  python -m gestcontrol.action_server
"""

from __future__ import annotations

import argparse
import signal
import sys

from .action_dispatcher import ActionDispatcher
from .config_loader import load_settings
from .osc_io import OSCServer


def main() -> None:
    if sys.platform != "win32":
        sys.exit("GestControl is Windows-only (see README for Mac notes).")

    parser = argparse.ArgumentParser(description="GestControl action server")
    parser.add_argument("--config",   default="config/gestures.yaml")
    parser.add_argument("--settings", default="config/settings.yaml")
    args = parser.parse_args()

    settings   = load_settings(args.settings)
    dispatcher = ActionDispatcher(args.config, args.settings)

    host = settings["osc"]["action_host"]
    port = settings["osc"]["action_port"]
    server = OSCServer(host, port)

    server.map(
        "/gesture/event",
        lambda addr, *a: dispatcher.on_gesture_event(a[0], a[1]),
    )
    server.map(
        "/cursor/move",
        lambda addr, *a: dispatcher.on_cursor_move(a[0], a[1]),
    )
    server.map("/heartbeat", lambda *_: None)

    def _stop(sig, frame):
        print("\n[action_server] shutting down")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    print(f"[action_server] listening on {host}:{port}")
    server.start()   # blocks


if __name__ == "__main__":
    main()
