# Phase 330 — store sampling, quest illustrations, and loading-loop residue

This is an offline resource/render verification record. No game was started.
The runtime UI, font-size work, dialogue layout and deployment record are separate.

## Verified findings

### Store atlas cells are not consumer windows

- Both `Store_Kamond_Meun_click` and `Store_Kamond_Meun_normal` have 128-pixel-wide
  atlas cells, but the `StoreMenuScene` and `KamondStore` category consumers use
  `UL=79`, `VL=31`, with rows at `V=0/32/64/96`. All eight owned labels and the
  selected-state red background now center in that 79-pixel window, not at x64.
- The money image consumer reads `U=176`, `UL=68`. The prior 74-pixel ink box
  extended outside that consumer. The revised ink box reserves room for the
  existing outline and shadow and contains the complete four-character label.
- The subtitle starts at `V=70` and uses 26-pixel sampling slots. The atlas edits
  used 28-pixel writing cells. Purchase lettering/shadow leaked into the sale
  slot. The revised glyph positions and explicit `effect_clip` keep effects
  inside the real slot without clipping any glyph ink.
- `texture_appearance.effect_clip` is optional and locale-neutral. It validates
  an in-canvas rectangle and fails if the clipping operation would remove glyph
  pixels. Existing labels without this field retain their old rasterization.

The 15 new consumer checks are in
`locales/zh-Hans/texture-overlays/gameplay-consumer-contracts-v9.json`.
The v7 baseline fails 15/15 (exit 1); the v9 recipe passes 15/15 (exit 0).
Purchase/sale/process alpha in the following slot is now zero in the owned layer.
The serialized consumer proof is retained in
`build/phase-330-gameplay-qa/ui-consumers/store-category-consumers.json`.

### Quest illustrations: a two-disc inventory, not only the first screenshot

`tools/inventory_texture_exports.py` read all 4,145 package headers from the two
original discs (1,912 + 2,233 packages; 2,551 distinct hashes). There were zero
unparsed packages and 61 matching texture exports: six store aliases per disc,
23 quest illustrations on disc 1, and 26 on disc 2. The extra disc-2 illustrations
are `20_Wereboar`, `21_Grami`, and `22_Groundbeast`.

The repair translates 25 unique Korean captions: 22 shared between discs and
three exclusive to disc 2. `Quest_Monster_17_Albedo` contains intentional `???`
and remains untouched. Shared source-package hashes agree between discs before
reuse. The recipe binds each new resource to `[1,2]` or `[2]` explicitly.

Quest labels use the terminology in the current quest text or the existing
monster-name inventory, including 克洛普斯, 穿刺蠕虫, 蓬蓬, 沼泽鳗, 格拉米 and 地行兽.
The original pink-to-white treatment is retained with the already selected
Noto Sans CJK font. No tutorial embedded screenshots were edited.

Each replacement is confined to `[32,220,192,36]`, uses a source-locked,
glyph-supported transparency restoration mask, and protects the entire
`[0,0,256,220]` creature-art region. Unchanged native blocks are retained, rather
than recompressing the full picture. The final 25-image contact sheet was viewed.
Runtime normalization preserves the native tile bytes.

### Loading loops: source glyph core, halo and destination differ

The former erase mask used only the first frame of `loading.bik` and a 4-pixel
dilation. It removed bright source letters but left their outer glow behind the
shorter Chinese label. The new reference mask unions all 90 original reference
frames and uses an 8-pixel dilation. The reference rectangle is now
`[993,538,192,40]`.

**Important pitfall:** a common reference is not a common destination.
`loadingmovie_01`, `11` and `12` display the indicator at x132, not x995. Their
destination erase rectangle is `[130,538,192,40]`; all other entries use the
right-side destination. The original destination-minus-reference displacement
is preserved. A regression test checks all 15 entries, all non-indicator captions,
the complete styles/font locks, and the left/right coordinate relationship.

An intermediate attempt that replaced all destinations with the right-side
reference failed the new regression in three cases. It is not an eligible
delivery. Those three movies were rebuilt. The other 12 were retained only after
checking complete entry identity, tool/font locks and output hashes. The plan
equivalence record is in `loading-destination-equivalence.json`; the final
candidate directory is **`texture-fixes/loading-v9-final`**, never `loading-v9`.

All 15 final movies retain 90 frames, 1280×720 dimensions, silent BIKi streams,
and the exact `10000000/333333` time base. They were independently decoded.
`tools/verify_video_caption_regions.py` additionally compares every final frame
against independently reconstructed indicator pixels, with the region and both
protection windows translated to the actual left/right destination.

Focused replay result:

| Check | Baseline | Modified |
|---|---:|---:|
| Frames exceeding halo error limits | 1,350 | 0 |
| Maximum mean halo decode error (8-bit RGB) | see per-frame reports | 1.401163 |
| Maximum halo P99 error | see per-frame reports | 3.666667 |
| Mean/P99 limits | 5 / 20 | 5 / 20 |
| Protected pre-encode pixels changed | — | 0 |
| Pixels changed outside old/new mask union | — | 0 |

The left spinner and the artwork to the far right are separate protected
windows. The final encoded first/middle/last-frame contact sheet was viewed.
This is lossy video recompression: final decoded backgrounds are checked against
error bounds, not described as byte-identical. Artwork hidden by original text
is reconstructed, not claimed to be recovered original pixels.

## Recipes and composable delivery

- `locales/zh-Hans/texture-overlays/ui-labels-gameplay-v9.delta.json`: 12 corrected
  store labels plus 25 new quest captions, guarded against the v7 label/source
  metadata.
- `locales/zh-Hans/texture-overlays/ui-labels-gameplay-v9.json`: reproducible full
  master assembled with `texture_region_repair.merge_delta`.
- `locales/zh-Hans/loading-captions-v9.json`: unchanged titles, descriptions,
  fonts and visual styles; only the indicator erase recipe changes.
- `build/phase-330-gameplay-qa/texture-fixes/texture-delivery.json`: six store
  alias transfers in three existing packages, each with before/after tile hashes,
  allowed rectangles, donor path/hash and tile bytes; also 25 normalized quest
  package candidates with explicit disc membership.
- `build/phase-330-gameplay-qa/texture-fixes/movie-delivery.json`: final movie
  candidates, frozen before hashes, both original-disc hashes and replay reports.

The store transfers must be applied to the current numeral/UI candidate, not by
replacing its entire `MC2Game`, `Startup_int` or `UI_Name_Jpn` package. Trial
transfers preserved all unselected exports and blocks. Isolated rollback copies
match the frozen pre-turn resource hashes exactly, while trial candidates remain
modified. This preserves phase-329 status-label repairs and independent work.

Frozen prior resources are under
`build/phase-330-gameplay-qa/baseline-resources`; they do not point at a live test
folder that changes after incremental refresh.

## Reproduction and evidence

Native texture build/replay uses the existing builder with the generated subset
plan and explicit disc 2 (the subset includes the three exclusive images):

The subset is reproducible from the versioned master alone; the development
`make_texture_recipe.py` and image-review caches are not required. With the
master's hash-matched `original`/`base` resources and fonts materialized, generate
the same plan as follows (keep complete layers of each selected texture):

```python
import copy, json
from pathlib import Path
p = json.loads(Path('locales/zh-Hans/texture-overlays/ui-labels-gameplay-v9.json').read_bytes())
sub = copy.deepcopy(p)
sub['sources'] = []
ids = set()
names = {'Store_tex_01', 'Store_Kamond_Meun_click', 'Store_Kamond_Meun_normal'}
for source in p['sources']:
    edits = [t for t in source['textures']
             if t['object'].split('.')[-1] in names or t['object'].startswith('Quest_Monster_')]
    if edits:
        sub['sources'].append(dict(source, textures=edits))
        for t in edits:
            ids.update(t.get('regions', [t.get('label')]))
sub['labels'] = [r for r in p['labels'] if r['id'] in ids]
out = Path('build/texture-v9-subset-plan.json')
out.parent.mkdir(exist_ok=True)
with out.open('xb') as f:
    f.write((json.dumps(sub, ensure_ascii=False, indent=2) + '\n').encode())
```

Use that plan with `--output-dir NEW_OUTPUT_DIRECTORY` for a fresh build; use
`--verify-root` only for an existing build. For composition, extract the three
selected donors' native tiles with `replace_texture_regions.selected`, lock the
tiles' SHA256 and transfer only the rectangles recorded in the delivery. Keep
the current font/UI package as the destination, as described above.

```powershell
python -B -X utf8 -m tools.build_texture_overlay --plan build/phase-330-gameplay-qa/texture-fixes/texture-v9-subset-plan.json --disc 2 --project-root . --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-330-gameplay-qa/texture-fixes/texture-v9-final
python -B -X utf8 -m tools.texture_sampling_probe --plan locales/zh-Hans/texture-overlays/ui-labels-gameplay-v9.json --contracts locales/zh-Hans/texture-overlays/gameplay-consumer-contracts-v9.json
```

The video argv arrays preserve the exact externally supplied decoder/encoder
paths and hashes. They can be executed without hand-copying or shell quoting:

```powershell
python -B -X utf8 -c "import json,subprocess; from pathlib import Path; subprocess.run(json.loads(Path('build/phase-330-gameplay-qa/texture-fixes/loading-v9-verify-command.json').read_bytes()),check=True)"
python -B -X utf8 -c "import json,subprocess; from pathlib import Path; subprocess.run(json.loads(Path('build/phase-330-gameplay-qa/texture-fixes/loading-region-command.json').read_bytes()),check=True)"
```

For a clean checkout the direct entry point is `tools.build_video_captions`:
pass the versioned v9 plan and its SHA256, `--source-root` containing the 15
original BIK files (for example the extracted disc-1 `MC2Game/Movies` directory),
a new `--output-dir`, and explicit `--ffmpeg`/`--ffmpeg-sha256` and
`--encoder`/`--encoder-sha256`. The source/font/rasterizer locks in the plan are
checked before rendering. Add `--verify` to independently replay an existing
candidate. The generated argv record is evidence of the local executable paths,
not a required private source input.

Unit coverage includes temporal-mask count/geometry failures, glyph-preserving
effect clipping, both video destination layouts, recipe delta equality, all 25
quest mask hashes, disc membership, and focused-region error metrics. Original
source files, fonts, configuration and saves are not modified by these tools.

Full `--verify` also exposed a previous report-only defect: Pillow returns
`alpha_bbox` as a tuple, while a persisted JSON report reloads it as an array.
Report-field comparison now compares JSON values rather than rejecting that
representation difference. Tests still reject changed coordinates and missing
fields; this fix changes no rendered or encoded asset bytes.
