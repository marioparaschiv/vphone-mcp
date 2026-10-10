"""Escape hatches: a guest shell and any vphoned method."""

from .. import machine, shell


def run_shell(command: str, root: bool = False) -> str:
    return shell.run(command, root=root)


def rpc(method: str, params: dict | None = None) -> dict:
    return machine.rpc(method, **(params or {}))
