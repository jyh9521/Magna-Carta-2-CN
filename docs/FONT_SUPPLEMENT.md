# Minimal font supplement prototype — 2026-10-18

## Status

**Verified offline:** the append-only tool builds two local package copies with
only `踢` (U+8E22) and `击` (U+51FB) added to General_15. It reparses font records,
texture pixels and the complete rebuilt package. **Runtime rendering remains
unverified.** This is not a release font, a complete Chinese character set, a
verified UI font binding or a completed game-localization proof of concept.

No original package, font-source file, ISO or existing output is overwritten.
Generated packages, reports and original-derived previews remain ignored under
`build/font-supplement/`. Do not upload these complete game assets.

## Inputs and final v2 outputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| font.xxx | 1343488 | `b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6` |
| Startup_int.xxx | 1769472 | `be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3` |
| NotoSansCJKsc-Regular.otf | 16437364 | `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b` |

The font source is locked separately in `references/font-sources.lock.json`,
Noto Sans CJK SC Regular Sans2.004, commit
`523d033d6cb47f4a80c58a35753646f5c3608a78`, OFL; notice is retained in
`licenses/Noto-Sans-CJK-OFL.txt`. The binary remains local in `build/font-source/`.
Tooling does not hard-code that font identity; explicit CLI hashes bind inputs.

Final plan: `locales/zh-Hans/font-supplement.json`, SHA-256
`2fee020c8c51d7daea834fae1a17b16b61ae03df85ab25f156c63f7392586bef`.
It requests 22 px raster, **metric_height=23**, and two 24×24 BC3-aligned cells
on TextureIndex5 at (420,24) and (448,24). All existing glyph metric rectangles
and their 4×4 blocks are disjoint from those cells.

| Final output (under build/font-supplement/v2/) | Bytes | SHA-256 |
|---|---:|---|
| font.xxx | 1842707 | `91dd68f7a2048d7f3a71b3af56f7e6dae326744c6f37e9f136e4528f5fec51be` |
| Startup_int.xxx | 2993190 | `a95821ee7a5cf41d92f4cc92d436dc1cf1bd104106a014ba42c7894358067d75` |

Reports are `font-report.json` and `Startup-report.json` beside those files.
Earlier trial files directly in `build/font-supplement/` used 24 px metric
height and are **superseded by v2**, not silently overwritten.

## Reproduction

Metadata/append/package tests use the Python standard library. Rasterization
imports Pillow/fontTools lazily; optional dependencies are declared separately
in `requirements-font.txt`. This local run used Pillow **12.2.0**, fontTools
**4.63.0**, FreeType **2.14.3**. Identical package output is observed with these
inputs/runtime; cross-platform font-raster byte identity is not promised.

The optional LZX adapter was built separately as documented in the LZX
research/build files. Use fresh output/report paths if the following exist:

```powershell
python tools/supplement_font.py build/disc1-font-study/MC2Game/CookedXenon/font.xxx --package-sha256 b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6 --font-file build/font-source/NotoSansCJKsc-Regular.otf --font-sha256 2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b --font-object General_15 --plan locales/zh-Hans/font-supplement.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/font-supplement/v2/font.xxx --report build/font-supplement/v2/font-report.json
python tools/supplement_font.py build/disc1-font-study/MC2Game/CookedXenon/Startup_int.xxx --package-sha256 be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3 --font-file build/font-source/NotoSansCJKsc-Regular.otf --font-sha256 2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b --font-object Font.General_15 --plan locales/zh-Hans/font-supplement.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/font-supplement/v2/Startup_int.xxx --report build/font-supplement/v2/Startup-report.json
python -m unittest discover -s tests -p test_supplement_font.py -v
```

Both package builds exited **0**. Existing output paths, unsupported profiles,
source-hash mismatch, unsupported codepoints, missing cmap glyphs, zero rasters,
clipping, overlapping cells/blocks and font-height growth fail rather than
silently replacing data.

## Exact modification strategy

1. Verify SHA-256 and big-endian UE3 profile 446/25; decode package-level LZX
   only for the supported compressed layout.
2. Resolve an explicit Engine.Font export path; keep its original texture
   object-reference array and all existing glyph/remap records.
3. Append two Characters tagged records (145 bytes each), two native metric
   records (17 bytes each) and two remap pairs (4 bytes each). Count fields and
   Characters payload size change; existing raw records are retained verbatim.
   Glyph indices are **2608/2609**, total **2610**.
4. Rasterize only characters present in the source font's cmap; reject tofu.
   Use a shared cell baseline **20**, rather than centering each glyph
   independently. Both rasters are bounded inside the first **23** rows; the
   24th row remains transparent. Their metric VSize is **23**. Original and
   supplemented maximum VSize both remain **23**, avoiding a known source of
   global line-height changes. This does not establish game-side advance or
   baseline behavior.
5. Encode white BC3 color and alpha coverage. Maximum observed alpha error is
   **18/255**, with endpoints exact. Exactly **72** selected BC3 blocks change;
   all other tile blocks, aligned padding and decoded RGBA pixels outside the
   cells are identical. Original glyph rectangles therefore retain their
   pixels; all untouched atlases retain their complete payloads.
6. Append the updated Font and texture payloads to the logical package end.
   **No original payload is relocated or erased.** Only those two export table
   serial-size/serial-offset fields (+32/+36) are repointed. Other export
   locations, metadata and payloads remain identical.
7. Rebase the appended texture's SourceArt and mip bulk absolute pointers.
   Standalone font.xxx preserves texture bulk flag0x40 (MCARTA inline LZX).
   Startup resident texture preserves original **raw inline flag0** and exact
   count=disk size=65536; no compression mode is guessed or forced.
8. Compressed Startup keeps 13 original compressed chunks byte-for-byte,
   rewrites the first chunk containing changed export fields using validated
   stored LZX, and adds one final logical chunk. The physical summary grows
   from 14 to 15 chunks; physical offsets are rebuilt. Original chunk gaps and
   **17767** trailing bytes are retained. Re-decoding the complete output must
   equal the expected logical buffer (including updated summary count).

Uncompressed output preserves **10** unaffected exports; Startup preserves
**4372**. These are complete byte comparisons, not just export-count checks.

## Cross-package checks and previews

The resident raw atlas and standalone LZX atlas have identical original tiled
bytes after decoding:
`c36a443620cc7c9744aeef7436a49bb85f911fdce3d15f4a1eede347b44705e5`.
Both supplemented tiled buffers likewise match:
`599229bab04b5c15a64e1932898d4bda9d6f56ee485369b61fc11bf0717ca9f8`.
Evidence: `build/font-supplement/v2/cross-package-validation.json`.

Both variants retain original native metric records SHA-256
`68ddc7100b03e8bf23659a40273f2d8bbf74c26f90df387025f35e9345b734c1`
and remap pair records SHA-256
`eca352e8742c2385d3f8b47c6cfaa2b58ae0b9d8a041d8cc849a984323b96679`.
Tagged record hashes differ across packages because their FName indices differ;
each is compared with its own unchanged original record stream and recorded in
its report. Neither variant replaces existing Unicode mappings.

Decoded **output**, not source raster, previews were reopened and inspected:

- `build/font-supplement/v2/Startup-General15-atlas5-black.png`
- `build/font-supplement/v2/decoded-glyph-cells-black.png`

They show original Hangul rows and readable 踢击 in the unused cells. Black
composites are provided because some preview surfaces ignore PNG alpha and
show the constant-white BC3 RGB of transparent pixels as solid white cells.
The underlying raw RGBA previews also exist; the actual atlas stores alpha,
not the black preview background. Raster visual QA is offline only.

## Automated checks and remaining gates

**14 synthetic tests pass**, without Pillow/fontTools or native decoder:
append record byte preservation, explicit remap, control/non-BMP/duplicate
rejection, source hash guards, overlap guards, raw/LZX texture variants,
compressed first-chunk rewrite plus original-chunk/trailing preservation,
exclusive output semantics, height23 preservation, maximum-height regression
rejection and visible-alpha-below-metric clipping rejection. The controlled
synthetic stored-block decoder is test-only, not a replacement for the native
LZX validation used on real files.

No installation or game launch is performed by this builder. A future isolated
runtime test still needs verified UI binding, correct text/TOC deployment and
same-scene original/modified/rollback capture. Preserve source hashes, verify
saves/load behavior and measure actual layout before extending the glyph set.
Static package parse and readable local PNGs do **not** satisfy that gate.

## Runtime qualification (2026-10-18)

Offline append/pixel checks above remain valid, but runtime Chinese rendering
is NOT accepted. Both General_15 and EngineMedium_Subtitle experiments omitted
Chinese. Stored-LZX rebuilt Startup packages guest-faulted even in original-data
no-op controls. Experimental `--raw-atlas` plus a fully uncompressed outer package
loads the warning, but does not establish font binding. See RUNTIME_TEXT_BINDING.md.
