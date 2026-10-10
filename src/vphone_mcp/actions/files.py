"""List guest directories and copy files between host and guest."""

from pathlib import Path

from .. import machine, shell


def ls(path: str) -> dict:
    return machine.rpc("files.list", path=path)


def pull(path: str, to: str) -> dict:
    destination = Path(to).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shell.pull(path, str(destination))

    return {"path": str(destination), "bytes": destination.stat().st_size}


def push(path: str, to: str) -> dict:
    shell.push(path, to)

    return {"path": to, "bytes": Path(path).expanduser().stat().st_size}
