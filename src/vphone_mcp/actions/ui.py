"""See and drive the guest screen. Coordinates are screen points throughout."""

import base64
import functools
import subprocess
from pathlib import Path

from mcp.server.mcpserver import Image

from .. import machine

SCREENSHOT_PATH = Path("/tmp/vphone-mcp-screenshot.jpg")


def screenshot() -> Image:
    """Taken in the guest (the host capture can lag) and scaled to screen points."""
    result = machine.rpc("screen.screenshot")
    SCREENSHOT_PATH.write_bytes(base64.b64decode(result["data"]))
    points_height = result["height"] // result["coordinate_scale"]
    subprocess.run(
        ["sips", "-Z", str(points_height), str(SCREENSHOT_PATH)],
        check=True,
        capture_output=True,
    )

    return Image(path=SCREENSHOT_PATH)


@functools.cache
def screen_scale() -> int:
    return machine.rpc("device.screen")["scale"]


def tap(x: float, y: float) -> str:
    """Host HID input: vphoned's input.tap misses some controls, such as navigation bar buttons."""
    scale = screen_scale()
    machine.send(
        {"t": "tap", "x": round(x * scale), "y": round(y * scale), "screen": False}
    )

    return "ok"


def swipe(x1: float, y1: float, x2: float, y2: float, ms: int = 300) -> str:
    scale = screen_scale()
    machine.send(
        {
            "t": "swipe",
            "x1": round(x1 * scale),
            "y1": round(y1 * scale),
            "x2": round(x2 * scale),
            "y2": round(y2 * scale),
            "ms": ms,
            "screen": False,
        }
    )

    return "ok"


def key(name: str) -> str:
    machine.send({"t": "key", "name": name, "screen": False})

    return "ok"


def type_text(text: str) -> dict:
    return machine.rpc("input.type", text=text)


def ui() -> dict:
    description = machine.rpc("ui.describe")
    description.pop("screenshot", None)

    return description


def tap_text(**selector) -> dict:
    return machine.rpc("ui.tap_element", **selector)


def wait(timeout: float = 10, gone: bool = False, **selector) -> dict:
    method = "ui.wait_gone" if gone else "ui.wait"

    return machine.rpc(method, timeout=timeout, **selector)
