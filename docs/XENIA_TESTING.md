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
not generate substitute settings or add tuning arguments. Only storage, content,
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

Window control again reported a physical-Escape stop. This run therefore has
**no new reliable game capture or text-binding result**. Earlier observations
included possible movie/demo content and an occluded-window capture; they prove
neither controller input nor UI resource binding. Preserve failed observations,
but do not classify them as game QA.

Next: get a fresh targetable window, prove actual input/state change under this
baseline, and record an original same-scene UI. Necessary input-setting changes
must be explicit, separately recorded deviations, never silent edits to the
supplied file. Then verify ASCII binding and original recovery before deploying
the four Chinese candidates. Chinese rendering, game-side rollback, saves and full
progression remain unverified. Esc stops window control, not development.
