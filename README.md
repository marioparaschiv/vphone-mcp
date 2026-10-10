# vphone-mcp

```sh
claude mcp add vphone -- uvx vphone-mcp
```

One MCP tool that lets an agent install IPAs and tweaks, read app containers, and filter app logs inside a jailbroken [vphone](https://github.com/Lakr233/vphone-cli) iOS VM.

- **One tool, 25 actions.** About 530 tokens of context in total.
- **Built for jailbreak work.** Installs `.deb` tweaks with dpkg and lists what is injected.
- **Lean replies.** Logs are filtered by regex in the server, and screenshots come back at screen-point size.

---

## Quick start (about 40 minutes, mostly downloads)

You need an Apple silicon Mac set up for vphone. Steps 1 to 6 happen once.

1. **Create a VM** (25 to 40 minutes): install [vphone-launchpad](https://github.com/Lakr233/vphone-cli/releases), finish Host Setup, then run `vphone-launchpad-cli vm create vphone`.
2. **Install Irisin** (1 minute): in the VM window, choose **Apps > Install Bootstrap…** and select **roothide**.
3. **Add repos in Irisin** (2 minutes):
   - `https://apt.owngoal.dev`
   - `https://roothide.github.io/`
   - Procursus, through **Add Advanced Source**: URL `https://roothide.github.io/procursus`, suite `iphoneos-arm64e/1900`, component `main`
4. **Install the base system** (about 3 minutes): queue *OwnGoal Bootstrap for vphone*, tap **Execute**, then tap **Bootstrap Install**. This brings in apt, dpkg, sudo and openssh.
5. **Install ElleKit** (1 minute): install **ElleKit** in Irisin. Without it, tweaks install but never load.
6. **Set up ssh** (10 seconds): `uvx vphone-mcp setup-ssh`
7. **Add the server to your agent**: run the command at the top of this README.

Check that it works: ask your agent to "list user apps on the vphone".

---

## Actions

Every call has the form `vphone(action, args)`.

### Apps

| Action | Args | Does |
| --- | --- | --- |
| `install_ipa` | `path` | Installs an IPA from the host. vphoned re-signs it and keeps its entitlements |
| `list_apps` | `system=false`, `query?` | Name, bundle id, bundle path, data path |
| `app_info` | `bundle_id` | Adds `documents_path`, the executable and entitlements |
| `launch` / `terminate` / `uninstall` | `bundle_id` | `launch` unlocks the screen first and also accepts `url` |
| `prefs` | `bundle_id` | The app's preferences plist |

### Tweaks

| Action | Args | Does |
| --- | --- | --- |
| `install_tweak` | `path`, `respring=true` | Runs `dpkg -i` on a `.deb` from the host |
| `remove_tweak` | `package`, `respring=true` | Runs `dpkg -r` |
| `tweaks` | none | Packages that ship a tweak dylib |

### Files and logs

| Action | Args | Does |
| --- | --- | --- |
| `ls` | `path` | Lists a guest directory |
| `pull` / `push` | `path`, `to` | Copies a file between host and guest over scp, at any size |
| `logs` | `bundle_id?` or `process?`, `seconds`, `include?`, `exclude?` | Live capture with regex filters |
| `crashes` | `bundle_id?` or `path?` | Lists crash reports, or reads one |

### Screen

| Action | Args | Does |
| --- | --- | --- |
| `ui` | none | The screen as text. Cheaper than a screenshot |
| `tap_text` / `wait` | `text`, `match`, `timeout` | Taps or waits by label instead of coordinates |
| `screenshot` / `tap` / `swipe` | screen points (430x932) | Coordinates match `ui` |
| `key` / `type` | `name` / `text` | `home`, `power`, `return`, `cmd+v`, … |

### Escape hatches

| Action | Args | Does |
| --- | --- | --- |
| `shell` | `command`, `root=false` | Runs a command over ssh in the bootstrap shell |
| `rpc` | `method`, `params?` | Calls any of vphoned's ~150 methods |

---

## Example: did my tweak load?

```text
vphone("install_tweak", {"path": "~/Downloads/MyTweak.deb"})
vphone("launch",        {"bundle_id": "com.apple.Preferences"})
vphone("logs",          {"bundle_id": "com.apple.Preferences", "seconds": 10, "include": "MyTweak"})
```

Each log line looks like `HH:MM:SS process[pid] level subsystem:category message`, so `include` and `exclude` can match any of those fields.

---

## Paths to know

- **Action args take real-root paths**, for example `/private/var/mobile/Containers/Data/Application/<UUID>/Documents`.
- **In `shell`, the real root is under `/rootfs`.** roothide puts the bootstrap's own `/` somewhere else.
- **`app_info` returns the container paths**, so you never have to guess a UUID.

---

## Configuration

All settings are optional environment variables.

| Variable | Default | What it sets |
| --- | --- | --- |
| `VPHONE_MACHINE` | `vphone` | Machine name |
| `VPHONE_LIBRARY` | `~/.vphone/machines` | Folder that holds the machines |
| `VPHONE_SSH_KEY` | `~/.ssh/vphone` | Key that `setup-ssh` creates and that ssh uses |
| `VPHONE_SSH_PORT` | `22` | Guest sshd port |
| `VPHONE_TIMEOUT_S` | `300` | Timeout for each call |

---

## When something fails

| Error | Cause | Fix |
| --- | --- | --- |
| `vphone is not running` | No `vphone.sock` | `vphone-launchpad-cli vm start vphone` |
| `frontmost application could not be verified` | `ui`, `tap_text` and `wait` need an app in front | `launch` an app first, or use `screenshot` and `tap` |
| `device is locked or screen is off` | The guest auto-locked | Call `launch` (it unlocks), or `rpc` `screen.unlock` |
| `Permission denied (publickey…)` | No key in the bootstrap | `uvx vphone-mcp setup-ssh` |
| A tweak installs but nothing happens | ElleKit is missing | Quick start, step 3 |

---

## How it works

```text
agent ──MCP──▶ vphone-mcp ──▶ vphone.sock ──▶ vphoned (in the guest)   apps, files, logs, UI
                         └──▶ ssh / scp ────▶ bootstrap sshd           dpkg, file transfer
```

`vphone.sock` refuses requests over 1 MiB, so files travel over scp.

```text
src/vphone_mcp/
├── server.py        the `vphone` tool and the setup-ssh command
├── machine.py       vphone.sock client
├── shell.py         ssh, scp, key setup
└── actions/
    ├── apps.py      install_ipa, list_apps, app_info, launch, terminate, uninstall, prefs
    ├── tweaks.py    install_tweak, remove_tweak, tweaks
    ├── files.py     ls, pull, push
    ├── logs.py      logs, crashes
    ├── ui.py        screenshot, tap, swipe, key, type, ui, tap_text, wait
    └── raw.py       shell, rpc
```

---

## Develop

```sh
git clone https://github.com/marioparaschiv/vphone-mcp && cd vphone-mcp
uv sync
claude mcp add vphone -- uv --directory "$PWD" run vphone-mcp
```

Licensed under GPL-3.0-or-later. See [LICENSE](LICENSE).
