# Reproducible multi-alias font supplement bundles — 2026-10-19

## Purpose and evidence level

**Verified offline:** `tools/build_font_supplement.py` assembles every explicitly
planned Font alias, a matching disc-specific font-only TOC, retained original
controls, guarded backup-restoration checks and machine-readable reports.
It reuses the append-only font/atlas implementation in supplement_font.py.
It never launches a game, installs files, edits configuration, rewrites an ISO,
changes text resources or chooses a runtime-loaded font instance. Game rendering,
raw/stored-LZX compatibility and Chinese display remain unverified.

The current locale plans only request the two existing technical glyphs. They
are not a complete Chinese font, final translation data or an installer.
Version-locked sources and namespace research are in FONT_BINDING_AUDIT.md.
The generic builder accepts other locale plans without language-specific code.

## Required inputs

- Python3.12+, optional raster dependencies pinned in requirements-font.txt.
- Locally supplied original resource root for the selected disc. Only the three
  Font packages and MC2Game/Xbox360TOC.txt are required; no XEX or emulator.
- Explicit native LZX decoder, reproducibly built as in LZX_RESEARCH.md.
- Local source font matching the plan's full SHA256. Source/license lock:
  references/font-sources.lock.json and licenses/Noto-Sans-CJK-OFL.txt.
- Checked-in locale glyph plan and disc-specific assembly plan under locales/.

The D1/D2 input Font hashes match, but TOCs do not. The two assembly plans must
not be interchanged. The tool verifies resource hashes, package profile,
canonical Font identity, known namespace GUID, full original semantic fingerprint,
glyph-plan bytes and font source before building. All planned aliases must pass;
there is no missing-alias skip or unknown-version fallback. This does not
rediscover aliases automatically; source completeness comes from the separately
verified whole-disc inventories, not the assembly tool's source count alone.

For a clean extraction into a new directory, select these four resources with
`tools/disc_inventory.py --extract PATH` (repeatable), `--extract-dir NEW_ROOT`
and a fresh `--output NEW_INVENTORY.json`:

```text
MC2Game/CookedXenon/font.xxx
MC2Game/CookedXenon/MC2Game.xxx
MC2Game/CookedXenon/Startup_int.xxx
MC2Game/Xbox360TOC.txt
```

## Commands (repository root; new output directory each time)

```powershell
python -m pip install -r requirements-font.txt
python tools/build_font_supplement.py --plan locales/zh-Hans/font-build-disc1.json --game-root build/poc-game/disc1 --project-root . --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW-disc1-font-bundle
python tools/build_font_supplement.py --plan locales/zh-Hans/font-build-disc2.json --game-root build/style-inheritance-verification/disc2-inputs --project-root . --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW-disc2-font-bundle
```

`--game-root` is the selected original extraction, not an installation target.
`--project-root` confines the relative glyph-plan reference. `--font-file` and
the decoder path are explicit local inputs. Output must be new and outside the
selected game root. No existing output is overwritten. The builder computes and
validates all candidates/TOC in memory before creating output. Publication I/O
failures may leave an incomplete new directory; absent manifest means incomplete,
and retry uses a different new directory. This is not an atomic directory rename.

## Output contract

```text
controls/<label>.xxx          original physical source bytes, not raw conversion
candidates/<label>.xxx        append-only supplemented container
reports/<label>.json          per-package preservation/atlas/remap checks
rollback-check/<label>.xxx    restored independent candidate copy
rollback-check/Xbox360TOC.txt original TOC reproduced after inverse verification
Xbox360TOC.txt                font-only size candidate for this disc
manifest.json                emitted last, all outputs reopened
```

Labels are portable validated package identifiers. For non-forced exports the
label supplies the original package namespace; do not rename it as an arbitrary
display label. Manifest source_path retains the
original resource spelling; label filenames are not installation paths.
Raw-atlas mode is deliberately not enabled. For compressed packages the existing
first-header-chunk/final-append algorithm preserves all other original chunks
and trailing bytes. Full logical bytes, unaffected exports, original glyph
records/pixels, outside-cell pixels/BC3 blocks and original maximum glyph height
are verified by supplement_package. No blanket atlas replacement occurs.

The shared raster is generated once per bundle. Original and output fingerprints
cover complete glyph metrics/remap plus all six decoded tiled atlases. The
plan's expected output fingerprint rejects raster/dependency drift, rather than
silently accepting a new result. Manifest records dependency versions and actual
alpha raster hashes. Dependency changes require deliberate investigation and
updated evidence; do not replace an expected hash just to make a build pass.

Every input is rehashed before and after publication. Controls, candidates,
per-source reports, restored files, TOC and manifest are reopened. Independent
restoration copies the candidate into a new check file, verifies its candidate
hash, then restores a separately hash-checked original backup and compares every
byte. This proves **backup restoration**, not mathematical reconstruction of the
original compressed package from appended data, and not in-game restoration.
TOC inverse first-size updates must reproduce its original bytes exactly.

## Assembly plan schema1

Shared fields with the geometry diagnostic: sources (label/path/sha256/
font_object), required_source_count, toc(path/sha256), canonical_font_path,
expected_namespace_guid, expected_semantic_sha256 and game_rendering_verified=false.
The shared validator lives in tools/font_binding_plan.py; the geometry builder's
existing CLI remains unchanged. Bool-as-schema-version, wrong metadata types,
duplicate case-insensitive labels/paths, reserved Windows labels, escaping paths,
invalid hashes and unknown namespace GUIDs are rejected.

Supplement fields: supplement(path/sha256), font_source_sha256 and
expected_supplement_semantic_sha256. The supplement path is relative to
project-root. Geometry donor/codepoint fields are not needed. Locale-specific
characters/positions remain in the separately hash-locked glyph plan. This is
assembly metadata, not another UE3 binary format.

## Reproduction evidence

Both real disc builds under build/font-bundle-verification/disc1 and disc2
reproduced all three earlier individual candidate hashes exactly. All six
backup-restored originals matched complete original physical source hashes.
Both TOCs matched the earlier independently generated font-only candidates and
passed inverse first-size updates. Original source/plan/font hashes were rechecked.
Each complete normalized output fingerprint is
`3e720fef59fc0a0e1a545555a517369e1d55c68f32ec019f2c143e45658d87f7`,
with 2610 glyphs and remap entries. Actual raster dependencies: Pillow12.2.0,
fonttools4.63.0 (matching the pinned requirements).

Baseline327 -> modified337 -> independent source rollback327; native-enabled337.
Ten new self-authored tests cover mixed package/atlas compression, all-three
assembly, source/locale/font/namespace/semantic guards, late source mutation,
publication readback failure, restoration input hashes and destination guards,
malformed plan types, both locked disc plans and CLI. The default suite needs
no original game, font raster dependencies, decoder DLL or game execution.

All complete game resources and generated reports remain ignored under build/;
Git contains only source, synthetic tests, locale plans and documentation.

A Windows-only CI fault-injection path mismatch was reproduced independently
with a junction-backed temporary root (old test fails; corrected test passes).
The injector now resolves both path identities and asserts a single injected
read. This fixes the test's short/long temporary-path mismatch; it does not
weaken the builder's readback or change candidate bytes. See PITFALLS.md.
