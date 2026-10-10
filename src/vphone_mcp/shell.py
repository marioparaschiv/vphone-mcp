"""Commands in the guest's bootstrap shell over ssh."""

import os
import shlex
import subprocess
import uuid
from pathlib import Path

from . import machine

SSH_KEY = Path(os.environ.get("VPHONE_SSH_KEY", "~/.ssh/vphone")).expanduser()
SSH_PORT = os.environ.get("VPHONE_SSH_PORT", "22")
OPTIONS = (
    "-i",
    str(SSH_KEY),
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=accept-new",
)
STAGING_DIR = "/private/var/tmp"


class ShellError(Exception):
    pass


def guest_ip() -> str:
    for address in machine.rpc("device.network")["addresses"]:
        interface, ip = address.split(" ", 1)
        if interface == "en0" and "." in ip:
            return ip

    raise ShellError("the guest has no IPv4 address on en0")


def guest_path(real_path: str) -> str:
    """The ssh shell of a roothide bootstrap sees the real root under /rootfs."""
    return f"/rootfs{real_path}"


def run(command: str, root: bool = False) -> str:
    user = "root" if root else "mobile"

    return call(["ssh", *OPTIONS, "-p", SSH_PORT, f"{user}@{guest_ip()}", command])


def push(local_path: str, real_path: str) -> None:
    """Copy a host file to a guest real-root path, owned like its parent directory."""
    remote = guest_path(real_path)
    call(
        [
            "scp",
            *OPTIONS,
            "-P",
            SSH_PORT,
            str(Path(local_path).expanduser()),
            f"root@{guest_ip()}:{remote}",
        ]
    )
    run(
        f"chown --reference={shlex.quote(str(Path(remote).parent))} {shlex.quote(remote)}",
        root=True,
    )


def stage(local_path: str, suffix: str) -> str:
    """Copy a host file into the guest's temp folder and return its real-root path."""
    real_path = f"{STAGING_DIR}/vphone-mcp-{uuid.uuid4().hex}{suffix}"
    push(local_path, real_path)

    return real_path


def pull(real_path: str, local_path: str) -> None:
    call(
        [
            "scp",
            *OPTIONS,
            "-P",
            SSH_PORT,
            f"root@{guest_ip()}:{guest_path(real_path)}",
            str(Path(local_path).expanduser()),
        ]
    )


def call(command: list[str]) -> str:
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=machine.TIMEOUT_S, check=False
    )
    if result.returncode != 0:
        raise ShellError(
            f"exit {result.returncode}: {result.stderr.strip() or result.stdout.strip()}"
        )

    return result.stdout


def authorize_key() -> None:
    """Create SSH_KEY if needed and let it log in as mobile and root.

    sshd runs inside the bootstrap, so it reads the homes under the jbroot.
    """
    if not SSH_KEY.exists():
        call(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                "vphone-mcp",
                "-f",
                str(SSH_KEY),
            ]
        )

    public_key = SSH_KEY.with_suffix(".pub").read_text()
    jbroot = machine.rpc("bootstrap.inspect")["jbroot"]
    for home, owner in (("var/mobile", "mobile:mobile"), ("var/root", "root:wheel")):
        ssh_dir = f"{jbroot}/{home}/.ssh"
        keys = f"{ssh_dir}/authorized_keys"
        machine.rpc("files.mkdir", path=ssh_dir)
        machine.rpc("files.write", path=keys, content=public_key)
        machine.rpc("files.chmod", path=ssh_dir, mode="700")
        machine.rpc("files.chmod", path=keys, mode="600")
        machine.rpc("files.chown", path=ssh_dir, owner=owner)
        machine.rpc("files.chown", path=keys, owner=owner)

    run("true")
    run("true", root=True)
