"""Thin wrappers around python-osc so the rest of the codebase stays import-clean."""

from __future__ import annotations

from typing import Any, Callable

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


class OSCSender:
    def __init__(self, host: str, port: int) -> None:
        self._client = SimpleUDPClient(host, port)

    def send(self, address: str, *args: Any) -> None:
        """Send an OSC message.  Pass args as positional arguments."""
        payload = list(args) if len(args) != 1 else args[0]
        self._client.send_message(address, payload)


class OSCServer:
    def __init__(self, host: str, port: int) -> None:
        self._dispatcher = Dispatcher()
        self._host = host
        self._port = port
        self._server: ThreadingOSCUDPServer | None = None

    def map(self, address: str, handler: Callable) -> None:
        """Register handler(address, *osc_args) for a specific OSC address."""
        self._dispatcher.map(address, handler)

    def map_default(self, handler: Callable) -> None:
        self._dispatcher.set_default_handler(handler)

    def start(self) -> None:
        """Block forever, serving OSC packets on the configured host:port."""
        self._server = ThreadingOSCUDPServer(
            (self._host, self._port), self._dispatcher
        )
        self._server.serve_forever()

    def shutdown(self) -> None:
        if self._server:
            self._server.shutdown()
