# Font payload research — 2026-10-18

## Scope and confidence

**Verified (static bytes):** `tools/ue3_fonts.py` reads only uncompressed,
big-endian UE3 package profile 446/25. It uses the separately attributed table
reader in `tools/ue3_package.py`. The payload reader is new project code and does
not copy a third-party font implementation. It never writes a package or decodes
texture pixels. All generated JSON stays under ignored `build/`.

**High-confidence deduction:** the native `(u16, u16)` pair array represents
Unicode codepoint to Characters index mapping. Evidence: unique keys, bounded
indices, count equal to glyph count for both remapped fonts, ASCII identity
prefix followed by coherent Hangul ranges, and native flag equal to tagged
`IsRemapped`. Epic's [UFont API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UFont)
documents a `TMap<uint16,uint16>` CharRemap with precisely that role. That modern
API is supporting vocabulary, not proof of this older game's serialization.

**Unverified:** actual font binding for the startup prompt/main menu; missing-
glyph fallback behavior; rendering priority of tagged versus native data;
kerning/advance/line-height behavior; Xbox texture tiling and pixel formats;
中文 actual game rendering. No patch or game acceptance is claimed here.

## Source identities

Disc 1 extracted, unmodified files in
`build/disc1-font-study/MC2Game/CookedXenon/`:

| File | Bytes | SHA-256 | Font exports |
|---|---:|---|---:|
| EngineFonts.xxx | 229376 | `49e89e6c91ae4ead4297e10e44c3634e164a651f214c1a6eb3e161e3dd9ae5bc` | 4 |
| font.xxx | 1343488 | `b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6` | 2 |
| font_ui.xxx | 688128 | `5c0629a587b87fa54db57fdd3822fbab33315cc34e747545101505fb9dc1592f` | 20 |

Reports: `build/font-research/EngineFonts.payload-v2.json`,
`build/font-research/font.payload-v2.json`,
`build/font-research/font_ui.payload-v2.json`. These contain exact property,
glyph, native duplicate and remap offsets. Font-field offsets are relative to
`serial_offset`; texture serial offsets are package-absolute. They include
original metric/remap data and are not public release artifacts.

## Verified bounded Font export layout

1. Signed big-endian 32-bit object net index.
2. Tagged properties through `None` FName. Each nonterminal tag has name FName,
   type FName, u32 byte size and u32 array index. This profile's BoolProperty
   value is **four bytes**, outside its zero-sized payload; do not apply a
   modern one-byte BoolProperty assumption.
3. `Characters: ArrayProperty`: i32 count, then nested tagged records. Each has
   `StartU`, `StartV`, `USize`, `VSize` as four-byte IntProperty and
   `TextureIndex` as one-byte ByteProperty, then None. No vertical-offset or
   advance field is serialized in these tagged records.
4. `Textures: ArrayProperty`: i32 count followed by signed i32 object references.
5. Optional `IsRemapped: IntProperty` (1 in both fonts in font.xxx).
6. Native duplicate: i32 glyph count, each record four i32 atlas metrics plus
   u8 texture index (17 bytes, **no alignment**), then i32 texture-reference
   count and the same object references.
7. One i32 field is zero in all 26 exports; its semantic name is **unknown**.
   Reader rejects nonzero values rather than assuming kerning semantics.
8. i32 remap count, `(u16 codepoint, u16 glyph_index)` pairs, final i32 remap flag.
   Reader consumes exactly the export size, and cross-checks all duplicates.

| Font | Absolute serial offset | Size | Relative native start | Relative remap count | Glyphs / remaps | Textures |
|---|---:|---:|---:|---:|---:|---|
| EngineMedium_Subtitle | 1635 | 209142 | 182667 | 204098 | 1259 / 1259 | four 512×512 |
| General_15 | 210777 | 433092 | 378280 | 422652 | 2608 / 2608 | five 512×512 and one 512×64 |

EngineFonts Large/Medium/Small/Tiny each have 256 glyphs and no remap entries.
UI fonts include numerical/damage/icon/style assets with 64, 91, 126 or 256
glyphs. Font names alone do not prove which UI or script uses them.

## Coverage and original-data anomalies

**Verified static map result:** both font.xxx remap arrays contain **zero**
codepoints in U+4E00–U+9FFF. Subtitle has 994 Hangul syllables (U+AC00–U+D7AF);
General_15 has 2352. Every codepoint in `开始游戏请按确认` is absent. This is a
mapping-level finding, not a claim that no other runtime font/fallback exists.
A naive text-only Chinese substitution is therefore not a validated PoC.

The reader compares glyph rectangles against referenced Texture2D tagged
`SizeX`/`SizeY`. Two original UI exports have anomalies:

- `Font_Damege_Normal_Enemy`, indices 244–255: StartV=119, VSize=16 exceeds
  tagged height 128 (12 records).
- `StyleTree_Number_Font`, indices 238–255: StartV=60, VSize=11 exceeds tagged
  height 64 (18 records).

Both tagged/native metric copies agree. Reports retain these 30 findings in
`atlas_bounds_anomalies`, without truncating, repairing or discarding original
records. Their runtime significance remains unknown; unused glyph slots,
texture storage dimensions and sampler behavior require further evidence.

## Reproduction

After extracting supported files with the existing read-only inventory tool,
use a new output filename (the reader rejects existing output):

```powershell
python tools/ue3_fonts.py build/disc1-font-study/MC2Game/CookedXenon/font.xxx --output build/font-research/font.payload.json
python -m unittest discover -s tests -p test_ue3_fonts.py -v
```

15 synthetic tests pass, including exhaustive prefix truncation rejection,
metric/reference/remap mismatch, unsupported native field, malformed FName,
BoolProperty width, and compressed-package rejection. Real-file reports cover
all 26 fonts and all their tagged/native metric duplicates. This is static
format validation, **not** game rendering or full glyph coverage acceptance.

## Next engineering gates

1. Resolve visible startup prompt to actual UI object and Font reference via
   payload references/runtime evidence; do not label chapter-title textures as
   the main menu just because the package name is UI_Title.
2. Inspect actual Texture2D storage/mip/format metadata and preserve original
   anomalies before designing any atlas generator.
3. Determine whether both tagged and native font data must be rebuilt, then
   build a defensive same-size isolated PoC only after font binding is known.
4. Verify original/modified/rollback in the same Xenia scene. Keep original ISO
   unchanged, verify hashes, and only then expand the localization toolchain.

## Inventory scope correction (2026-10-18)

The 26-font results above cover the original three selected packages only.
Engine default references identify three more Fonts in MC2EditorResources.xxx;
see FONT_REFERENCES.md for exact fields, conflicting cooked configuration values
and the runtime-binding boundary. A filename-based inventory is incomplete.
