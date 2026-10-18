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

## Duplicated geometry probe

`probe_font_mapping.py --geometry` keeps remap keys/values unchanged. It copies
an existing donor glyph's StartU, StartV, USize, VSize and TextureIndex into BOTH
the tagged property values and the 17-byte native glyph record. Exact package
SHA256, codepoint/original mapping and donor bounds are still required. Font
reparsing must match the expected metrics; all other exports (including atlas
bulk bytes) must remain byte-identical. Reports record reversible old/new bytes
for each bounded field. Existing remap-only CLI behavior remains the default.

```powershell
python tools/probe_font_mapping.py build/disc1-font-study/MC2Game/CookedXenon/font.xxx --sha256 b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6 --font-object General_15 --codepoint 0xB85C --expected-glyph 959 --target-glyph 65 --geometry --output build/NEW-geometry.xxx --report build/NEW-geometry.json
```

The single General_15 static copy keeps size 1343488, output SHA256
`725236937cefd2b3fd445f92a70c70b6d5d2ee693904171c7066e6dbc12cea45`.
Independent report-driven inverse recovery equals the complete original hash.
Three additional synthetic tests validate both copies, untouched remap/other
exports, inverse restoration, guards and CLI dispatch; the suite now has 253 tests.

A local combined candidate redirects U+B85C geometry to A in General_15, B in
Subtitle (both external and resident), C in editor Tiny, D in Small, E in Large.
No atlas, remap or text content changes. The resident package uses the already
studied raw wrapper and its TOC size update. This geometry probe is diagnostic,
not a translated font or a release candidate. Runtime result is recorded below
only after a real interactive warning capture; movie/title loading is insufficient.

### Geometry trial outcome (2026-10-18)

`build/binding-20261018-f7-geometry` started with the unchanged user TOML and the
same F7 input overrides as the recorded original warning. It reached movie and
title frames. Automated Start taps did NOT produce a captured warning in this
trial. Therefore geometry sensitivity is **pending**, not a negative result and
not successful font binding. The four deployed files (font, Startup, editor
resources, TOC) were SHA-guarded and restored; `restored.json` retains identities.
The original ISO, XEX and user configuration were not changed.

The next runtime gate is still a same-warning geometry capture, followed by its
recovery view. If input remains unreliable, preserve the candidate and investigate
resource loading/draw selection read-only instead of adding further atlas glyphs
or calling a title/movie frame a passing test.

## Main script package embeds another General_15 (2026-10-18)

**Verified serialized evidence:** the logging-only run
`build/binding-20261018-file-trace` adds only `--log_level=3` to the unchanged
user TOML. The stopped runtime log SHA256 is
`15ee4c1c1fb78bdf5c144fd2e38a6ecc4f6ab43d6a7aca6743d8db643722127b`.
NtCreateFile requests selected 62 existing CookedXenon files; their tables
parsed without errors. Requests do not prove successful loads or Font selection.
Local per-package hashes/results: `requested-package-font-scan.json` under
`build/font-geometry-probe/`. No log or proprietary package is distributed.

MC2Game.xxx original SHA256
`13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641`
contains **13 Engine.Font exports**: Font.General_15 and 12 font_ui Fonts.
General_15 logical offset 10172281, size 433092, parses with matching tagged/native
records, 2608 glyphs/remap entries and six local Engine.Texture2D references.
These are separate package-local objects from the previously probed copies.
TitleMap_MSPT.xxx SHA256
`e094df8399beac753e07a1ee388d5192b8f0a721fa854d786104de7439e98395`
has no Font/MultiFont-class export. Engine.xxx also has EngineFonts.SmallFont;
class-default Font/MultiFont objects must not be counted as textured fonts.

Reproduce the inventory from the user's extracted package (new output required):

```powershell
python tools/inspect_font_references.py build/poc-game/disc1/MC2Game/CookedXenon/MC2Game.xxx --sha256 13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641 --inventory --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-MC2Game-inventory.json
```

This read-only mode shares package hash/profile/decoder guards with the existing
FontName inspector. It matches the exact class leaf Font or MultiFont, flags
Default__ names, and returns logical-package offsets/sizes (not positions in
compressed on-disk bytes). It does not parse every candidate's
payload, infer class inheritance, or claim runtime use. --object and --inventory
are mutually exclusive; existing default inspection remains unchanged. Three
new synthetic tests cover exact class filtering, defaults, hash guards,
unchanged source, CLI output reopening/overwrite protection and exclusive modes.

**Runtime pending:** `binding-20261018-mc2game-raw-control` used the recorded F7
input profile, original text/fonts and only the raw MC2Game wrapper plus TOC size
11632640 -> 58032128. Source/snapshot config verification passed. Title/movie
were visible, but repeated short Start taps did not yield a captured warning.
Do not call this a passing interactive raw-package control. Its two deployment
paths were hash-guarded back to the original MC2Game and TOC; the owned process
was stopped. Original ISO, XEX and TOML were not edited.

The not-yet-deployed MC2Game geometry candidate copies glyph 65 (A) geometry
into tagged/native glyph 959 (U+B85C). Raw baseline SHA256
`3aec13662b165e9b78c4af75756d13114069f1cb580078baf90123d1332f3fe3`,
geometry SHA256
`15911b07764cfffbfdc0374357e5dd6a22b34ac50fee37b6a5088311162ecd6b`,
both 58032128 bytes. Remap and all other exports/texture bytes are preserved.
The independent inverse-copy check is byte-identical; it is not in-game recovery.
Next gate: capture the raw-original warning, then this candidate in the same
warning, then original recovery. Only a positive controlled Font change permits
moving the two-glyph Chinese experiment onto this copy.
