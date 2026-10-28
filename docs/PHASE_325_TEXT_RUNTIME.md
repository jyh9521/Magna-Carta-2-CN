# Gameplay feedback: text consumers and font shadow (2026-10-27)

## Evidence boundary

This work addresses screenshots 03, 04, 10 and 12. No game was launched and no
ISO was written. The actual repaired test ISO supplied the baseline resources.
This is a resource candidate with static, red-capable consumer checks, **not**
completed in-game rendering acceptance.

### Verified static consumers

- `UI_Core.Scenes.QuickMenu.PosPannel.Bt_LbRb` contains the exact markup
  `<Styles:MC2_StyleFont_0>l<Styles:/><Styles:MC2_StyleFont_0>r<Styles:/><Strings:MC2UI.Common.ChangeTab>`.
  Its child `Bt_Cursor` starts at 135 and references `Common.Cursor`, preceded
  by the same icon font's `U`. The following `Bt_A` starts at 254. These are
  tagged `UIScreenValue_Bounds.Value[0]` values, not screenshot estimates.
- Actual `font_ui.MC2StyleFont_0` metrics give `l/r/U` widths 31/31/27.
  Current General_15 metrics give four-character labels 108 pixels each.
  Thus the two controlled runs occupy 170/135 pixels against 135/119 slots.
  `切换` / `移动` reduce them to 116/81, leaving 19/38 pixels. No icon markup,
  button ordering, texture position or controller mapping changes.
- The same StringStyle ID `9fe5e7d1-481e0c9d-c03b5f9f-40f3726d` is the GeneralFont
  path documented in [UI_STYLE_GRAPH.md](UI_STYLE_GRAPH.md). This is a serialized
  linkage; runtime skin/instance selection remains separately unobserved.
- `Default__MC2UIBalloon.WidthExtentMax` is 400. The serialized
  `UI_Core.Scenes.Scene_Balloon_10.Balloon_Base.Dialogue.LabelStringRenderer`
  has `AutoSizeParameters[0].Extent.Value[1] = 452`, WrapMode 3. The chosen
  NPC hard lines measure 351/326/337 in General_15, below both limits. A
  secondary Subtitle-font sensitivity check gives 416/389/398 against 452.
  The complete native word/markup tokenizer and the live balloon choice are
  not reproduced by this bounded measurement.
- The screenshot-12 CSMB source has an explicit sentence break. Earlier
  readability data removed it. Restoring that one break leaves the translated
  prose otherwise identical; line maxima are 591 (General) / 695 (Subtitle).
  The replay uses a conservative controlled 1078-pixel region from the native
  1280-pixel frame and 101-pixel margin constants, not a sampled live rectangle.

### Native text route

The original and repaired ISO `default.xex` are both 19,611,648 bytes with SHA256
`26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f`.
The independently reconstructed image remains
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`.
The new replay profile verifies exact native-window hashes; Capstone supplied
the offline PPC disassembly. REA's known PPC limitation is not bypassed by
claiming an unsupported decompilation.

- `0x8241ef40..68` binds config `SubTitleCharGap` to Engine +0x42c.
- `0x82589c04/08/44` supplies that gap and Engine +0x60 font to `0x8263c150`.
- `0x8263c150..548` remaps UTF16 units, reads 20-byte FontCharacter records,
  samples `USize/VSize/TextureIndex`, advances by USize and subtracts the
  configured gap from each glyph position. The visible route makes one draw
  per glyph with the white RGBA constant at `0x83217ccc`.
- The normal-texture branch calls `0x8263b3a8`; this transports the texture,
  UVs and supplied RGBA into the quad batch. The alternate material branch
  exists. The adjacent `0x8263c548` two-pass shadow helper has a different
  calling convention and was **not** substituted or patched.

**Unverified:** final pixel-shader/material sampling has not been decoded to
prove whether every live font route preserves atlas black RGB. The candidate
contains actual black+alpha shadow pixels and the decoded preview shows them,
but final shader behavior and in-game contrast need user retest. No XEX patch
is necessary for building this resource candidate.

## Changes and preservation

`gameplay-readability-v7.json` is a four-entry, SHA-locked **post-composition**
Coalesced plan. It consumes the existing repaired Coalesced SHA
`6eb5235e468c3d20ac9f48d1226777aca3eb2647e99a9b12408562aec7ed561f` on both discs.
All four IDs/selectors were independently matched to the original-disc source.
18,172 unselected entries are exact. For the two dialogue edits, removing only
literal `\\n` leaves the previous translation byte-for-byte identical. Brackets,
names, quotes and other control tokens remain in place. The explicit break
policies are 0→2 for NPC 00_115_01 and 0→1 for CSMB voc_csmb_0010_10.

`tools/font_shadow.py` is locale-neutral. It accepts an existing raw package,
its exact SHA, a selected Font export and the existing glyph placement plan.
It adds a one-pixel right/down black shadow only to currently transparent pixels
inside the selected glyph metrics. All existing foreground RGBA samples remain
exact after BC3 encode/decode. It never changes USize/VSize, advances, remap,
UVs, package size, export tables, offsets or unrelated blocks/exports.

Both EngineMedium_Subtitle aliases receive the same 2,391 glyph-cell operation,
adding 263,490 black pixels each. Two shadow samples on `；` stop at the existing
metric edge; **no original ink is clipped or moved**. Glyph spacing and baseline
remain unchanged. Existing padding accommodates the one-pixel shadow rather
than widening the font. Foreign hashes, placements, already-colored glyphs,
overlapping glyph cells and foreign rollback copies fail closed.

### Composition order matters

- `font.xxx` is not a v6 texture-overlay source. The standalone corrected
  resource is `text-runtime/final-resources/MC2Game/CookedXenon/font.xxx`, SHA
  `a6aa9782cd780860c4370b65963d8a2b42fcb3a543828c3bc616da11d8a9c8bd`.
- For Startup_int, **do not** feed the already-v6-overlaid ISO copy into a
  complete texture rebuild. The PRE-OVERLAY input is the v6 plan's source.base,
  SHA `52e8c9bc07a2bfc397011c660c1419f8d30ce8e3849a83ed03cdd788e2bd2c97`.
  Its shadow-only output is `text-runtime/pre-overlay/MC2Game/CookedXenon/Startup_int.xxx`,
  SHA `3eb6b69217f438257642f2d1929466cbd49f36555ab7183f4438e64ea415dfe0`.
  All 28 v6 texture inputs retain their exact original payload hashes, and all
  export offsets remain unchanged. Apply the full v7 overlays after this stage.
- The separate current-ISO Startup_int shadow-only copy exists solely for
  isolated before/after/rollback checks; it is not the v7 texture base.

All `text-runtime/` paths above are under
`build/phase-325-gameplay-feedback/`; generated proprietary resources stay there.

## Reproduction and acceptance

Use the existing font build inputs, especially the hash-locked
`locales/zh-Hans/cumulative-font-route/glyphs-2.json`; this stage does not require
a new font, glyph atlas layout or manual drawing.

```powershell
python -m tools.build_coalesced CURRENT_COALESCED locales/zh-Hans/gameplay-readability-v7.json --output NEW_COALESCED
python -m tools.font_shadow PRE_OVERLAY_PACKAGE --sha256 BASE_SHA --font-object Font.EngineMedium_Subtitle --glyph-plan locales/zh-Hans/cumulative-font-route/glyphs-2.json --glyph-plan-sha256 c96d8b169a965d0e1596a0f12e4504b34987d0e6e8d9009d5eeb50607a389457 --output NEW_PACKAGE --report NEW_PROOF
python -m tools.replay_text_consumers --resource-root RESOURCE_ROOT --ui-package MC2GAME_PACKAGE --native-image NATIVE_IMAGE --profile locales/zh-Hans/gameplay-text-consumers-v7.json --output NEW_REPLAY_REPORT
python -m unittest discover -s tests -p test_font_shadow.py -v
python -m unittest discover -s tests -p test_replay_text_consumers.py -v
```

The consumer profile pins the actual repaired MC2Game resource SHA
`952d659948ea529f216bd446bcde1a4cc1e460d8d7fa66be5636edd11ad9392c`; extraction
from the existing test ISO is read-only. It does not use stale cached logical
headers as a physical package. Native-image reconstruction is the established
XEX inspection workflow, not an external game dependency.

Observed replay: **baseline 8 failures / modified 0 / isolated rollback 8**.
Rollback reconstructs all three resource copies exactly, including the complete
Coalesced bytes; the modified outputs remain present. The local ROLLBACK.sh
accepts only a new isolated output tree, never an ISO or an existing game tree.

User retest still covers: subtitle shadow through the real shader on bright
movie frames; all QuickMenu button gaps; complete `[阿巴泽特]` on one line with
three-line balloon height; both CSMB lines inside the bottom panel. Also check
other subtitles using the same two Font aliases. No full-playthrough or live
rendering pass is claimed by the static checks.
