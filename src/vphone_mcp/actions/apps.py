"""Install, find, launch and inspect apps."""

from .. import machine, shell


def install_ipa(path: str) -> dict:
    return machine.rpc("apps.install", path=shell.stage(path, ".ipa"))


def list_apps(system: bool = False, query: str | None = None) -> list[dict]:
    apps = machine.rpc("apps.list", filter="all" if system else "user")["apps"]
    if query:
        needle = query.lower()
        apps = [
            app
            for app in apps
            if needle in app["name"].lower() or needle in app["bundle_id"].lower()
        ]

    return apps


def app_info(bundle_id: str) -> dict:
    info = machine.rpc("apps.info", bundle_id=bundle_id)
    if info.get("data_path"):
        info["documents_path"] = f"{info['data_path']}/Documents"

    return info


def launch(bundle_id: str, url: str | None = None) -> dict:
    params = {"bundle_id": bundle_id}
    if url:
        params["url"] = url

    machine.rpc("screen.unlock")

    return machine.rpc("apps.launch", **params)


def terminate(bundle_id: str) -> dict:
    return machine.rpc("apps.terminate", bundle_id=bundle_id)


def uninstall(bundle_id: str) -> dict:
    return machine.rpc("apps.uninstall", bundle_id=bundle_id, force=True)


def prefs(bundle_id: str) -> dict:
    data_path = machine.rpc("apps.data_dir", bundle_id=bundle_id)["data_path"]

    return machine.rpc(
        "files.plist", path=f"{data_path}/Library/Preferences/{bundle_id}.plist"
    )
