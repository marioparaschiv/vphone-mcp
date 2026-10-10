"""Install and remove .deb tweaks with dpkg."""

import shlex
from pathlib import Path

from .. import machine, shell


def install_tweak(path: str, respring: bool = True) -> dict:
    guest_path = shell.stage(path, ".deb")
    try:
        output = shell.run(f"dpkg -i {shell.guest_path(guest_path)}", root=True)
    finally:
        machine.rpc("files.remove", path=guest_path)

    return finish_dpkg(output, respring)


def remove_tweak(package: str, respring: bool = True) -> dict:
    output = shell.run(f"dpkg -r {shlex.quote(package)}", root=True)

    return finish_dpkg(output, respring)


def tweaks() -> list[str]:
    """Packages that ship a dylib into the ElleKit tweak directories."""
    lists = shell.run(
        "grep -l -E '(DynamicLibraries|TweakInject)/[^/]+\\.dylib$' /var/lib/dpkg/info/*.list || true"
    )

    return [Path(path).stem for path in lists.split()]


def finish_dpkg(output: str, respring: bool) -> dict:
    if respring:
        machine.rpc("system.respring", force=True)

    return {"dpkg": output, "resprung": respring}
