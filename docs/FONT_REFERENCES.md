# Font defaults and missing package discovery (2026-10-18)

## Verified serialized references, not runtime binding

Engine.xxx SHA256:
`f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a`.
The `Default__Engine` tagged defaults contain:

| Property | Serialized value | Logical value offset (includes FString length) |
|---|---|---:|
| TinyFontName | MC2EditorResources.koreantinyfont | 2596128 |
| SmallFontName | MC2EditorResources.koreansmallfont | 2596190 |
| MediumFontName | Font.EngineMedium_Subtitle | 2596253 |
| LargeFontName | font.General_15 | 2596308 |

The existing three-package/26-Font study was a subset, not the complete set of
fonts in this game. The name `MC2EditorResources` does not establish editor-only
runtime use; excluding it by filename omitted relevant serialized references.

The original Coalesced.ini also contains two different sources:
`MC2Engine.ini` agrees with the table; `Xe-MC2Engine.ini` instead points Tiny/Small
to EngineFonts.TinyFont / EngineFonts.SmallFont. Both retain the same Medium/Large
names. Configuration precedence and the actual warning's font are UNVERIFIED.
Do not select an effective default merely because one source is present.

## Additional font package (Verified static data)

MC2EditorResources.xxx is uncompressed, size **8290304**, SHA256
`4febba3cc55d45cba83a834be5f60f9f742489c6cfb4cec272e711cba556da31`.
It contains 527 exports and three Engine.Font objects:

| Object | Characters / remap entries | Texture references | Maximum glyph height |
|---|---:|---:|---:|
| koreantinyfont | 11534 / 11534 | 32 | 12 |
| koreansmallfont | 11534 / 11534 | 36 | 13 |
| koreanlargefont | 11534 / 11534 | 456 | 48 |

All three pass existing tagged/native Font parsing and have **zero** remap keys
in U+4E00–U+9FFF. The existing U+B85C entry maps to glyph 3514 in each. Their
sampled atlas for that glyph is 256x256, Format=7 (DXT5). This is not a claim that
all atlas pixels or bounds in this package have received full validation. The
large font's >255 texture-reference count needs separate study before expanding
its byte-sized glyph TextureIndex representation.

The current inspected scope is 29 Font objects across four named packages,
with resident Startup duplicates studied separately. A complete font
inventory must follow references / inspect class tables, not only `font*` names.

## Reproduction

```powershell
python tools/inspect_font_references.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-font-defaults.json
```

The reader validates the supported UE3 profile, exact source hash and export
selection, parses bounded tagged `*FontName` FString fields, labels logical
rather than physical offsets, writes only a new report and reopens it. Five
synthetic tests cover fields/offsets, malformed data, exhaustive truncation,
hash/export guards and CLI overwrite prevention. No original assets are copied
into the public repository. Local config findings are in
`build/font-binding-references/config-font-defaults.json`.

## Same-size sentinel and remaining gate

A local copy redirects existing U+B85C to ASCII A in Tiny, B in Small, C in Large.
Only three native uint16 glyph-index fields change; text, package length, atlas
bytes and TOC stay original. Copy SHA256:
`cdb7ced7b41758f6028fb084e531df19422e353594191167f65664c2ab70d753`.

The initial Return-key editor run had only movie evidence. Later paired F7 runs
captured the actual original warning and two real remap-probe warnings:

- `binding-20261018-f7-baseline/original-recovered-login.png`: original resources;
  original Korean warning restored after the earlier ASCII/Chinese experiments.
- `binding-20261018-f7-editor-sentinel/unchanged-login.png`: three editor-font
  mappings changed, but the first Korean syllable remains unchanged.
- `binding-20261018-f7-general-sentinel/unchanged-login.png`: General_15 and
  Subtitle mappings changed in both external and raw resident packages; the
  warning also remains unchanged. TOC length changed for the raw Startup only.

These are negative mapping-sensitivity results, NOT positive font binding and
not proof that a Font is unused: the inferred remap representation/runtime
consumption itself must still be tested. Next use a guarded duplicated-geometry
sentinel (tagged AND native glyph metrics), then follow actual renderer selection
if it remains unchanged. No Chinese supplementation is accepted by these tests.

All five touched resource paths were restored to original hashes. The final
fresh recovery run uses the same F7 input profile; its final same-warning capture
is tracked separately. No save/progression/full-game acceptance is implied.

The F23 experiment was rejected by the computer-use API and is not an accepted
key event. F7/F8/Delete runs record input-only CLI deviations, original TOML and
graphics unchanged. These are not identical-input comparisons with older Return
runs. Reproduction for this exact Canary build is in XENIA_TESTING.md.
