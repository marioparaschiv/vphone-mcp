"""Live unified log capture with regex filtering, and crash reports."""

import re
from pathlib import Path
from typing import Literal

from .. import machine


def logs(
    bundle_id: str | None = None,
    process: str | None = None,
    seconds: float = 10,
    include: str | None = None,
    exclude: str | None = None,
    ignore_case: bool = True,
    level: Literal["all", "error", "fault"] = "all",
    max_lines: int = 500,
) -> dict:
    if bundle_id:
        executable = machine.rpc("apps.info", bundle_id=bundle_id)["executable"]
        process = Path(executable).name

    params = {"seconds": seconds, "level": level, "max_lines": max_lines}
    if process:
        params["process"] = process

    entries = machine.rpc("logs.syslog", **params)["entries"]
    flags = re.IGNORECASE if ignore_case else 0
    include_re = re.compile(include, flags) if include else None
    exclude_re = re.compile(exclude, flags) if exclude else None
    lines = [
        line
        for line in map(format_entry, entries)
        if (not include_re or include_re.search(line))
        and not (exclude_re and exclude_re.search(line))
    ]

    return {
        "process": process,
        "captured": len(entries),
        "matched": len(lines),
        "lines": lines,
    }


def format_entry(entry: dict) -> str:
    """`HH:MM:SS process[pid] level subsystem:category message`, so regexes can match any field."""
    scope = ":".join(part for part in (entry["subsystem"], entry["category"]) if part)
    fields = (
        entry["date"][11:19],
        f"{entry['process']}[{entry['pid']}]",
        entry["level"],
        scope,
        entry["message"],
    )

    return " ".join(field for field in fields if field)


def crashes(bundle_id: str | None = None, path: str | None = None) -> dict:
    if path:
        return machine.rpc("logs.crash", path=path)

    params = {"bundle_id": bundle_id} if bundle_id else {}

    return machine.rpc("logs.crashes", **params)
