# Xenia experiment configuration

## Required baseline

Use the user's existing `xenia/xenia-canary.config.toml` for future experiments.
Do not substitute defaults or silently tune graphics, resolution, timing, audio,
language or input. This configuration stays local. User edits start a new recorded
baseline; do not force an old hash onto a later configuration.

Verified on 2026-10-18: source SHA-256
`7c89cfb8c2a0435cbe2e0764581b032cf17c0bb50fc4d721459b5b7b2508962b`.
GPU is `d3d12`, resolution scale **2 x 1**, VSYNC true, HID `any`, keyboard mode
**0**. These are observed inputs, not recommended settings. Disabled keyboard
controller emulation means injected keyboard keys are not proven controller input;
do not mistake an idle movie for controlled gameplay.

## Reproducible launcher

`tools/launch_xenia.py` copies the selected configuration byte-for-byte into a
fresh run directory and explicitly passes the snapshot via `--config`. It does
not generate substitute settings or add tuning arguments by default. Only storage, content,
cache and log paths are isolated. Original saves are not imported. A record keeps
config/executable/game hashes, full argv, cwd and PID. Inputs are rechecked before
process creation. Existing runs, invalid TOML, optional hash mismatch and runs
inside the game tree are rejected. Preparation alone never starts a process.

```powershell
python tools/launch_xenia.py --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --game build/poc-game/disc1/default.xex --run-dir build/user-config-runtime --config-sha256 7c89cfb8c2a0435cbe2e0764581b032cf17c0bb50fc4d721459b5b7b2508962b --launch
python tools/launch_xenia.py --verify build/user-config-runtime
```

Use a fresh run directory each time. Omit `--launch` to inspect the prepared
command only. Launch failure may leave a prepared record. `started` means process
creation, not successful loading, stability or localization.

The verifier compares parsed TOML from exactly one complete runtime CONFIG DUMP
with the snapshot and checks that snapshot/source hashes remain original.
Missing, incomplete, multiple or differing dumps fail. Multiple dumps may mean a
title override and require review. This is configuration-loading evidence, **not
a full effective-runtime audit**: defaults migration and internal runtime choices
are separate. The verifier does not inspect pixels, input response, resource
binding or saves. It never marks game rendering verified.

Upstream `50e9c715d` defines `--config`, loads an existing explicit file, and falls
back to defaults when it is absent. The launcher checks existence first, preventing
that fallback. Source: [Xenia config.cc](https://github.com/xenia-canary/xenia-canary/blob/50e9c715d/src/xenia/config.cc#L257-L283).
No upstream code is copied into the launcher.

## Current real run and remaining gate

The launcher actually started Canary `50e9c715d` using the unchanged extracted
Disc 1 `default.xex` and this configuration. Evidence stays local in
`build/user-config-runtime/run.json`, `config.snapshot.toml`, `runtime.log`.
Verification returned `config-dump-matches`, source unchanged, no tuning
overrides, exit **0**. Game files and the user configuration were not edited.

## Explicit keyboard test control (2026-10-18)

`--keyboard-test-input` is opt-in; normal launches still have no tuning overrides.
It adds exactly these CLI arguments, recorded in run.json:

```text
--hid=keyboard --keyboard_mode=1 --keybind_start=0x0D
--keybind_a=0x20 --keybind_b=0x08 --keybind_guide=0x87
```

Return is Start, Space is A, Backspace is B. No graphics settings change. Original
TOML and snapshot remain byte-identical; the config-dump check alone does not
prove effective input settings because CLI overrides are recorded separately.
Use the SAME override list for compared baseline/candidate/recovery runs.
Keyboard/IME/focus and short taps can be unreliable; inspect an actual interactive
state change instead of counting sent keys as accepted input. Do not mistake the
opening/idle movie for a playable scene. User Esc exits the game, not development.

The latest controlled experiment established real `TST` warning text binding.
Chinese glyphs remain absent; see [runtime matrix](RUNTIME_TEXT_BINDING.md).
Earlier physical-Escape/occluded-window observations are historical failed
observations, not current control status or game acceptance.

## Function-key control used for paired warnings

For the exact non-debug Canary executable SHA256
`e5e197f50a7ed1b6f94a927613d0510f31b528eacbec5b7dea4e5fa99c49ac0e`, the following
explicit local control avoids letter/Return input-method interference. It has
produced real warning captures; individual sent taps still need state checks.
The ordinary launcher CLI and its default input policy remain unchanged.

```python
from pathlib import Path
from tools.launch_xenia import prepare, save, launch
run = Path('build/UNIQUE_F7_RUN')
r = prepare('xenia/xenia_canary.exe', 'xenia/xenia-canary.config.toml',
            'build/poc-game/disc1/default.xex', run)
assert r['exe_sha256'] == 'e5e197f50a7ed1b6f94a927613d0510f31b528eacbec5b7dea4e5fa99c49ac0e'
keys = ['--hid=keyboard', '--keyboard_mode=1', '--keybind_start=0x76',
        '--keybind_a=0x77', '--keybind_b=0x2E', '--keybind_guide=0x87']
r['command'] += keys
r['tuning_overrides'] = keys
save(run, r)
launch(run, r)
```

F7=Start, F8=A, Delete=B. Do not press A to advance the no-save warning during
binding probes. Compare baseline/candidate/recovery under this SAME input list.
The source TOML remains byte-identical and no graphics/timing values are added.
F23 was rejected by the computer-use input API, so that trial is inconclusive.

This profile is deliberately pinned: upstream handles F7/F8 as state operations
in debug builds, not in this non-debug build. See the pinned
[OnKeyDown implementation](https://github.com/xenia-canary/xenia-canary/blob/50e9c715d/src/xenia/app/emulator_window.cc#L979-L1064).
An input profile proven with this binary is not automatically valid for another
emulator build. Screenshots and configuration verification remain local.
