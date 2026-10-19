# One warning, two font families, one Chinese candidate — 2026-10-19

## Concrete change

The previous packet supplemented the three General_15 namespace candidates,
but left the two SmallFont default-plane candidates unchanged. This experiment
targets **both known serialized routes together**, not another isolated native
helper. It does not claim that these are every possible runtime font.

Five Font objects occupy four resource packages. Startup_int contains one Font
from each family, so its edits must be sequentially composed rather than copied
over one another. After all five edits, the builder checks every complete font
fingerprint again, checks the full warning probe's literal coverage, updates
four physical package sizes in each disc's own TOC, and exercises retained-
original backup restoration for all six resources. No game is started and no
resource is deployed.

| Family | Physical candidates | Original -> candidate |
|---|---|---|
| Font.General_15 | font, MC2Game, Startup_int |2608 ->2610 glyphs, remapped throughout|
| EngineFonts.SmallFont | Engine, Startup_int |256 ->258 glyphs, explicit identity-remap conversion|

SmallFont namespace GUID:4e4a869b4312dd29ee4b9cbc3baa8a72.
Original complete semantic SHA256:
289ea3f9da29f70ae727b7ff886f003a7b87f3d9fa65d67618b9119ec22edf68.
Candidate complete semantic SHA256:
c5dff21e21cb6477d34b8212e60b3c87c50875cfa84e0b25dcade617baade381.

## Explicit mode conversion, not assumed runtime equivalence

The normal supplement path still rejects non-remapped Fonts. The new,
locale-neutral **identity-256** option accepts only exactly256 non-remapped
glyphs with an empty remap. It retains every original tagged/native glyph
record and texture reference, sets/inserts the existing IsRemapped IntProperty,
sets the trailing native mode word, introduces all256 `(codepoint,index)=(i,i)`
pairs, then appends the two technical Chinese glyphs. Required FNames must
already exist uniquely; no name/import table surgery or executable patch occurs.

**Verified offline:** both representations agree, all original glyph/atlas
pixels remain outside the selected cells, the new alpha raster passes existing
BC3 roundtrip bounds, both SmallFont aliases have the same final fingerprint,
and all five final Font candidates cover this probe. SmallFont uses two16x16
cells at(108,172)/(124,172), font size15, metric height16; maximum glyph height
does not increase. Only exact local Font/Texture2D Class definitions are accepted
in Engine, not similarly named arbitrary classes.

**High-confidence experiment rationale:** the selected metric routine has a
direct-index mode and a remap mode. An identity map retains the numeric mapping
for existing8-bit keys and supplies the two new keys.

**Unverified:** equivalence for zero-height/control glyphs, actual draw-path
use, native field/loading state, font selection, raw-package compatibility,
layout and Chinese pixels. No runtime/coverage claim is upgraded from the
conversion alone. This remains a diagnostic candidate, not a release font.

## Probe text and raw control

The exact LogIn_NewGame record now contains a66-UTF16-unit diagnostic panel:
`踢击! FONT CHECK` followed by ASCII labels and the same three protected literal
`\n` tokens; trailing periods preserve length. This is deliberately not a
translation of the warning. The full original is source-hash checked, not copied
into locale data. Other18175 records remain identical. The two Chinese glyphs
are the retained technical marker, not a terminology decision.

Coalesced candidate SHA256:
9f5cea2c629c4b638be6e20796162166bcaf9088a7fbc16ed0fad29e91fc4b2b.

The active route plans explicitly request uncompressed package outputs and raw
new atlas bulk, avoiding the already recorded LZX re-encoding compatibility
trap. Each packet includes **raw-controls** with only outer-package
decompression and its own size-correct TOC, plus original text. This is a
separate comparison, not a claim of compatibility. `controls` always retains
exact original compressed files; do not confuse it with raw-controls.

## Rebuild and independently replay

Supply the original disc resource tree, the locked Noto font from
references/font-sources.lock.json, and the explicitly built optional LZX decoder.
All final packet paths are relative and the replay can use a relocated packet:

```powershell
python tools/build_font_route_probe.py --plan locales/zh-Hans/font-routes-disc1.json --game-root ORIGINAL_DISC1_ROOT --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW-route-disc1
python tools/build_font_route_probe.py --plan locales/zh-Hans/font-routes-disc1.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/NEW-route-disc1
```

Disc2 uses font-routes-disc2.json and its original resources/TOC. Replay rebuilds
every candidate from the retained originals, trusted source/glyph/text plans and
locked raster source; it compares every output byte and the exact member set,
not upstream success flags. It neither writes the packet nor launches anything.
The file is a six-resource packet, not a bootable game or installer. Proprietary
resources remain ignored under build/. The deferred auxiliary-array draft is
retained locally and excluded from this work.

## User-operated acceptance only

1. Retain an original baseline and the packet's controls. Test the same warning
   with the raw-controls resource subtree first. A failure here is a container
   compatibility failure, not evidence about which font draws the warning.
2. Manually use the candidate subtree for the same disc and warning. Record
   whether the ASCII panel appears and whether both Chinese glyphs are visible.
   No observation is recorded as positive before the user supplies it.
3. Restore all six resources from controls, including that disc's TOC, and
   confirm original hashes/behavior. rollback-check is offline restoration
   evidence only, not proof of an actual game-folder restoration.

If the raw control works and the panel changes but Chinese does not appear,
the next investigation is driven by that specific result. It does not justify
another unrelated infrastructure expansion or bulk story translation.

## Check the six resource bytes before interpreting a game result

`tools/verify_resource_phase.py` is a standalone Python-standard-library checker,
also copied into the manual packet as `Verify-Resources.py`. It reads only the
declared six resources beneath an explicit resource root. It does not enumerate
the rest of the directory, install/copy resources, launch anything or read user
configuration. A trusted manifest SHA256 is mandatory; it first checks that
manifest and the selected packet-phase bytes, then compares the resource root.

```powershell
python Verify-Resources.py --packet-root Disc1 --manifest-sha256 MANIFEST_SHA256 --resource-root YOUR_TEST_RESOURCE_ROOT --phase candidate --output OUTSIDE_INPUT_ROOTS/new-candidate-check.json
```

Use `controls` for original/restored resource bytes, `raw-controls` for the
outer-decompression comparison, or `candidate` for the composed font/text probe.
The current Disc1/Disc2 manifest SHA256 values are printed in the packet's manual
guide. Do not calculate a new trusted hash merely to admit a changed manifest.
The phase report must be a new path outside both input roots. The tool checks
input stability and reopens its output; it removes only its own unchanged report
after a late input mutation. External output changes are preserved.

- exit0: every declared resource size/hash matches the selected phase;
- exit1: a complete report lists mismatching/missing resources;
- exit2: invalid/untrusted/changing inputs or an invalid output destination.

Both discs intentionally share five candidate resources but have different
TOCs. A Disc2 candidate checked against the Disc1 packet must report the TOC
mismatch, not a positive result. This addresses a specific manual-testing risk;
it is not another font-selector hypothesis. A byte match proves only that phase's
declared files match at the stated path. It never proves installation history,
game behavior, successful restoration of runtime behavior or Chinese rendering.

## Double-click or drag/drop entry, no manual resource copying

`tools/prepare_oneclick_probe.py` prepares two **complete independent game
copies**, `candidate` and `raw-controls`, from a supplied original resource tree.
It verifies the original default.xex hash, all six original/packet resource
hashes and every copied file; all other source files and empty directories are
retained. It never uses hardlinks/junctions and never installs into the original
tree. It requires free space for two full games plus the phase resources.

```powershell
python tools/prepare_oneclick_probe.py --source-root ORIGINAL_DISC1_ROOT --packet-root PREPARED_PACKET/Disc1 --manifest-sha256 TRUSTED_DISC1_MANIFEST_SHA --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/NEW-oneclick-disc1
```

Preparation **does not launch anything**. After both full copies pass byte
checks, it publishes `开始中文测试.cmd` and `开始原文对照.cmd`. The user may
double-click either file, or drag the corresponding directory's `default.xex`
into their own Xenia. Keep the whole prepared game directory intact; the XEX
alone is not a self-contained patch or game.

Each CMD first checks the six selected phase resources, then invokes the existing
config-preserving launcher only when the user clicks it. The original config
hash is pinned; each run gets a new snapshot, log/storage/content/cache path.
No keyboard/graphics override is added. Changing the user's config deliberately
requires refreshing this prepared entry rather than silently changing a test
baseline. CMD dependencies refer to the original local project/emulator paths;
these are local convenience launchers, not a portable release.

Synthetic tests inspect generated launch text and independent copy behavior;
they never execute CMD, Xenia or game instructions. Preparation/byte checks are
not evidence that a launcher has run or that Chinese renders in game.
