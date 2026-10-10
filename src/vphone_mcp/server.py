"""One MCP tool, `vphone`, that dispatches app work in a vphone guest by action."""

import re
import sys
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import machine, shell
from .actions import ACTIONS

mcp = MCPServer("vphone")


@mcp.tool()
def vphone(action: Literal[tuple(ACTIONS)], args: dict[str, Any] | None = None) -> Any:
    """Drive the vphone guest. Guest paths are real-root paths; file transfers and tweaks use ssh. Actions and args:

    install_ipa {path}: host IPA; vphoned re-signs it, keeps entitlements
    install_tweak {path, respring=true}: host .deb via dpkg | remove_tweak {package, respring=true} | tweaks {}: installed tweak packages
    list_apps {system=false, query?}
    app_info {bundle_id}: bundle_path, data_path, documents_path, executable, entitlements
    launch {bundle_id, url?} | terminate {bundle_id} | uninstall {bundle_id}
    prefs {bundle_id}: the app's preferences plist
    ls {path} | pull {path, to: host path} | push {path: host path, to}
    logs {bundle_id? | process?, seconds=10 (max 60), include?, exclude?, ignore_case=true, level=all|error|fault, max_lines=500}: live capture; include/exclude are regexes over `HH:MM:SS process[pid] level subsystem:category message`
    crashes {bundle_id?} lists reports; {path} reads one
    screenshot {} | tap {x, y} | swipe {x1, y1, x2, y2, ms=300}: screen points (430x932), same as ui
    key {name}: home, power, volup, voldown, return, cmd+v, ...
    type {text}
    ui {}: describe the screen as text; prefer it to screenshot. ui, tap_text and wait need an app in front, not the home screen
    tap_text {text, match=contains|exact, index=0, identifier?, role?} | wait {same selector, timeout=10, gone=false}
    shell {command, root=false}: ssh into the bootstrap shell; the real root is under /rootfs
    rpc {method, params?}: any other vphoned method (ui.tree, ui.ocr, processes.list, apps.open_url, network.capture, ...)
    """
    try:
        return ACTIONS[action](**(args or {}))
    except (
        machine.MachineError,
        shell.ShellError,
        OSError,
        TypeError,
        re.error,
    ) as error:
        raise ToolError(f"{action}: {error}") from error


def main():
    if sys.argv[1:] == ["setup-ssh"]:
        shell.authorize_key()
        print(f"ssh ready: {shell.SSH_KEY} logs in as mobile and root")
        return

    mcp.run()
