# Phase 333 — voice-drama typography, punctuation and native-style loading indicators

## Scope and evidence levels

This revision addresses the five user screenshots, not a new font replacement,
gameplay rewrite, DLC repack, or executable patch. The existing directory test
copy is incrementally refreshed. No game launch, ISO generation, full-game copy,
configuration change, or save migration is part of this iteration.

The reproducible source inputs start at `14c99196fae59dbecf7f83e84b78d740ed421c03`.
The phase-332 candidate packet manifest is
`8bb35dec5b01ce8efd66bbaa1d712555c5dbffc61ceea218aa46bb34fb33a920`.
Full local inputs, outputs, source screenshots, rejected experiments and receipts
remain under ignored `build/phase-333-voice-loading/`.

**Verified:** source identifiers, bounded changed blocks/fields, source hashes,
font identity against the actual reference texture, video frame/timing structure,
pixel-support invariants, independent decoded replay, and resource-envelope checks.

**High-confidence deduction:** right-hand original loading cards use screen
composition with the standalone `loading.bik` effect. Weighted 90-frame fits to
the native reference give roughly 0.60–0.75/255 average residual. This is not a
universal Bink property. Three left-hand cards use differently arranged effects
and must not be forced into a translated right-hand model.

**Authored reconstruction, not recovered original pixels:** hidden/ill-conditioned
letter regions and the underlying black-reference FX estimate. A screenshot or
small inverse-composition residual cannot prove the invisible original artwork.
Offline visual review does not replace user acceptance in the game.

## 1. Exact reference-heading reuse

`Extra_Drama_Tex0` occurs in both `TitleMap_MSPT.xxx` and `UI_Name_Jpn.xxx`.
The upper label `img_ui_name_jpn_13_0` previously used Noto Sans Regular at 17 px;
the actual lower `img_ui_name_jpn_13_1` uses **Noto Serif CJK SC SemiBold, 20 px**.
Rebuilding the unchanged lower label reproduces its native blocks and pixels
exactly in both active aliases, rather than merely resembling a screenshot.

The upper label now uses that same font, gradient, outline, glow, shadow, tracking
and weight. Only placement differs to center it in its own row. The native donor
rectangle `[28,0,228,28]` is transferred using `build_texture_region_update`:
228 native blocks change per alias; the lower label, icons, other blocks, other
exports and the existing raw/32-KiB package envelope remain unchanged.

Versioned data:

- `locales/zh-Hans/texture-overlays/voice-drama-headings-v10.json`
- `locales/zh-Hans/texture-overlays/voice-drama-heading-contracts-v10.json`
- `locales/zh-Hans/texture-overlays/voice-drama-region-update-v10.json`

The tool is locale-neutral: it accepts source-locked donor plans, precise native
regions and package/export identities; it does not know these Chinese labels.

## 2. Three synopsis fields, five missing marks

The missing punctuation exists in the translation data, not just in rendering.
`MC2UI_Field.int / [Live Drama] / Drama1_Story, Drama2_Story, Drama3_Story` receive
four full stops and the comma after the subordinate phrase ending `之际`.
`locales/zh-Hans/voice-drama-punctuation-v10.json` is a current-source-SHA delta.

All other 18,173 fields, wording, leading spaces, literal `\n` controls, empty
paragraphs and ellipses are preserved. Measured with actual General_15 advances,
the three maximum line widths remain 478, 405 and 432: each inserted mark is on
a shorter line. Coalesced grows exactly 10 bytes; reverse rebuilding reproduces
the prior file byte-for-byte. Do not change hash-bound historical batch-097 or
apply a global remove/add-period heuristic to titles, labels and narrative prose.

## 3. Loading indicator reconstruction

The target inventory is `loadingmovie_01` through `loadingmovie_14`, plus
`loading`: **15 silent BIKi loops, 90 frames each, 1280×720**, with original
timing `10000000/333333`. The title/body recipes in v9 are unchanged. Only the
indicator restoration, lettering and animation differ in v10.

### Why the old method failed

The old `restore_masked` call interpolated a broad foreground mask directly in
each character/background frame. It averaged across skin, boot and cloth edges.
Increasing the mask removed more lettering but enlarged the smear. No fully
off original-caption frame exists in the 90-frame source loop.

A rejected direct temporal-minimum matte removed not only lettering but also
the minimum ambient haze. It produced a dark rectangle. Lower reprojection error
did **not** make that image correct. This failed route remains in local research
evidence and is not used by `loading-captions-v10.json`.

### Current bounded pipeline

1. Decode the locked standalone black-background effect reference. Use the
   original v9 ink-union mask inside a 320×100 context with a known perimeter.
2. Estimate the minimum diffuse FX beneath that ink **in the black reference
   only**. The existing interpolation solver is used on that reference, never
   on a character, costume or scene backdrop. Infer the glyph matte by
   `T = (F_min - E_min) / (1 - E_min)`; set it to zero outside ink support.
3. Invert each target pixel pointwise using `C = (Y - T) / (1 - T)`. A static
   validity union also marks any target pixel more than 4 code values below
   the proposed matte across the entire 90-frame loop. This prevents clipping
   a wrong model into black letter-shaped fringes, particularly on left cards.
4. The production minimum transmittance is **0.90**: trusted inversion amplifies
   errors at most 1.111×. The earlier 0.12 experiment allowed 8.33× amplification
   and left visible English-shaped noise despite passing a rescreen metric.
   It was visually rejected. Low-confidence glyphs are declared reconstruction,
   not passed off as recovered pixels.
5. Load a source/geometry/mask-hash-locked sparse RGBA repair. Only the explicit
   low-confidence/inconsistent glyph pixels are authored. The 15 small 192×40
   assets together contain 60,556 painted pixels; all other RGBA bytes are zero.
   They are derived from a reviewed image-generation repair sheet, not a whole
   generated replacement frame. Known source pixels are never replaced by that
   generated sheet. No original full frame, video or complete texture is tracked.
6. Apply nearby native **temporal lighting change only** to repaired pixels,
   bounded to ±48 code values. No spatial background averaging is performed.
   The support is fixed for the complete loop, avoiding confidence-mask flicker.
7. Render Noto Serif CJK SC SemiBold at 22 px, fine warm outline/glow, explicit
   one/two/three-dot states and a subtle continuous cyclic pulse. Preserve the
   original native spinner, lightning, source frame order and loop timing.

`video_screen_underlay` contains the generic inverse/reference mathematics;
`video_native_indicator` holds the bounded operation. Locale-owned wording,
font choice, geometry, thresholds, repair pixels and hashes are data. Existing
v9 plans retain the old code path. The focused regional verifier shifts a native
operation as an operation; it must never downgrade it to the old blur tuple.

Tracked authored assets and provenance:

- `locales/zh-Hans/loading-captions-v10.json`
- `locales/zh-Hans/loading-restoration-v10/*.png`
- `locales/zh-Hans/loading-restoration-v10/PROVENANCE.json`

## Rebuild

Supply the original movies, the documented previous resource candidate, locked
OFL fonts, the existing local LZX library and licensed RAD encoder. Full binaries
and generated intermediates stay outside Git. Use new output directories.
The heading donor also requires the two original packages at the exact
`build/poc-game/disc1/MC2Game/CookedXenon/{TitleMap_MSPT,UI_Name_Jpn}.xxx`
paths and hashes declared by `voice-drama-headings-v10.json`; these are separate
from the current candidate inputs. They may be supplied individually, without
copying a complete game tree.

```powershell
python -X utf8 -m tools.build_texture_region_update `
  --profile locales/zh-Hans/texture-overlays/voice-drama-region-update-v10.json `
  --profile-sha256 d889bb223e6afefd96b8bfce1b975400d27dd08dfd10974e807c722e2332422d `
  --project-root . --input-root build/phase-332-startup-black/packet/candidate `
  --output build/phase-333-rebuild/voice `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll

python -X utf8 -m tools.build_coalesced `
  build/phase-332-startup-black/packet/candidate/MC2Game/Localization/Coalesced.int `
  locales/zh-Hans/voice-drama-punctuation-v10.json `
  --output build/phase-333-rebuild/text/Coalesced.int

python -X utf8 -m tools.build_video_captions `
  --plan locales/zh-Hans/loading-captions-v10.json `
  --plan-sha256 6c43b0739b3ee378dd692558c8d61cadfe58622d6ed104f33a6eee09bcd5ca75 `
  --project-root . --source-root build/phase-325-gameplay-feedback/loading-art `
  --output-dir build/phase-333-rebuild/loading `
  --ffmpeg $FFMPEG --ffmpeg-sha256 589e50b766d251afdf181dd664d40bd94407e200b019989fd7468c7d118a28d0 `
  --encoder $RADVIDEO --encoder-sha256 b405986b11fdc214033bcf385f4c7c3d126a9899815391b96af955618139a1ce
```

`--preview --entry loadingmovie_14` makes an offline first-frame preview. A full
build streams one owned scratch AVI, privately encodes the Bink, then decodes all
90 frames and independently replays the recipe. Encoder-input and replay hashes
must agree; all pixels outside declared support must be identical before lossy
encoding. Header/timing/frame counts and bounded decode errors are checked.
The scratch AVI is removed by its exact known path. `--verify` reopens an existing
result rather than overwriting it. Original media must remain hash-identical.

## Deployment and regression boundaries

Compose the 18 changed resources against the phase-332 packet with
`compose_incremental_comparison`; regenerate TOC sizes and run the final
`runtime-envelope` gate. Retain the other 422 resources, raw controls, executable,
DLC binding, configuration, saved profiles and runs. Use
`refresh_oneclick_probe` on the existing test directory only after hash preflight.
Both-disc provenance is checked separately from local Disc-1 installation.

The local four-artifact record is `MODIFIED_FILE.json`, `DIFF_FILE.patch`,
`VERIFICATION.txt`, `ROLLBACK.sh`. Rollback evidence exercises the real guarded
refresh-restore path on a separately copied write set; the authoritative modified
candidate remains installed. The source baseline is archived, not overwritten.

User acceptance should check all three voice-drama descriptions and the matching
headings, then ordinary scene transitions with left/right loading cards. Offline
frame checks do not establish every in-game transition or aesthetic perfection.

## Hash-bound source serialization

All new JSON recipes use canonical LF, matching `.gitattributes`. Physical CRLF
hashes are not portable through Git normalization. The initial local CRLF build
inputs and reports are archived in the local encoding-baseline evidence. The
canonical recipe is structurally identical; updated nested profile hashes are
replayed, and the canonical video recipe independently reproduces every encoded
input frame. A source-only archive plus binary Git diff is applied in an isolated
source tree; canonical source bytes and the complete unit suite are checked there.

## Completed offline checks and incremental delivery

- Baseline unit suite: 2,620 tests, 2 skipped; revised suite: 2,651 tests,
  2 skipped. Source-only archive/diff replay: 2,651 tests, 3 skipped because
  optional local native dependencies are not part of the source archive.
- Independent clean-source rebuild reproduces all three voice resources exactly.
- All 15 Binks pass independent canonical-recipe replay of all 1,350 frames.
  Focused ROI mean error is at most 3.107905/255, p99 at most 18.666667/255
  (limits 5 and 24). Native spinner/top-effect guards change 0 preencode pixels;
  outside the old/new mask union also changes 0 pixels.
- First-frame titles, descriptions and artwork outside the indicator context
  match the previous preencode images exactly in all 15 movies.
- The 18 resource replacements are byte-identical shared inputs on both discs.
  Disc 1 packet `c5892de612a03cca0b0758f9e47e0d5c921f73b5b0791acd691f48b2d97e2abf`
  passes 441/441 resource and final envelope checks.
- Existing Disc 1 test directory is refreshed with 22 journalled writes:
  18 resources, their TOC, and 3 entry/metadata files. DLC binding remains
  `0d71b7f3cf1a6be5952c28a4f1aae8346a6bd5e2d7273cf7f499397274556148`.
  No game was launched and no Disc 2 ISO was written.
