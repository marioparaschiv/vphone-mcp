"""Client for a running machine's vphone.sock: one JSON object in, one JSON line out."""

import json
import os
import socket
from pathlib import Path

LIBRARY = Path(os.environ.get("VPHONE_LIBRARY", "~/.vphone/machines")).expanduser()
MACHINE = os.environ.get("VPHONE_MACHINE", "vphone")
TIMEOUT_S = float(os.environ.get("VPHONE_TIMEOUT_S", "300"))


class MachineError(Exception):
    """vphone.sock or vphoned refused a request."""

    def __init__(self, message: str, guest_error: dict | None = None):
        super().__init__(message)
        self.guest_error = guest_error


def socket_path() -> Path:
    return LIBRARY / MACHINE / "vphone.sock"


def send(request: dict) -> dict:
    path = socket_path()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(TIMEOUT_S)
        try:
            sock.connect(str(path))
        except (FileNotFoundError, ConnectionRefusedError) as error:
            raise MachineError(
                f"{MACHINE} is not running ({path}: {error.strerror})"
            ) from error

        sock.sendall(json.dumps(request).encode() + b"\n")
        sock.shutdown(socket.SHUT_WR)

        chunks = []
        while chunk := sock.recv(1 << 16):
            chunks.append(chunk)

    raw = b"".join(chunks).strip()
    if not raw:
        raise MachineError(f"empty reply to {request.get('t')}")

    reply = json.loads(raw)
    if not reply.get("ok"):
        guest_error = reply.get("guest_error")
        message = guest_error.get("message") if guest_error else None
        raise MachineError(
            message or reply.get("error") or "request failed", guest_error
        )

    return reply


def rpc(method: str, **params) -> dict:
    return send({"t": "rpc", "method": method, "params": params})["result"]
