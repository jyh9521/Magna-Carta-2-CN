# Direct serialized font consumers (2026-10-18)

## Current execution boundary

The user performs all game tests. Continue offline extraction, serialization
research, synthetic tests and candidate preparation without launching Xenia,
sending game input or deploying research packages to the game directory.
The earlier runtime matrix remains historical evidence, not a new test request.

## Verified offline findings

`inspect_font_references.py --consumers` extends the earlier exact UIStyle scan
to direct top-level ObjectProperty references on other tagged objects, including
custom widgets and class-default objects. A property's name need not contain
`Font`; its resolved target must have exact class leaf `Font` or `MultiFont`.
Imports and exports remain distinct; package-local object indices are preserved.

The 62 existing packages selected by the previously recorded file-request log
were read with their recorded SHA256 identities. The source selection is the
same as FONT_REFERENCES.md; file requests do not establish successful loading
or drawing. No process or game was started for this scan. All 62 package hashes
were rechecked after analysis and stayed unchanged.

| Scope | Exports | Tagged exports parsed | Skipped | Unparsed | Direct font links |
|---|---:|---:|---:|---:|---:|
| MC2Game.xxx | 83392 | 39865 | 33824 | 9703 | 16 |
| Engine.xxx | 21574 | 1202 | 19937 | 435 | 2 |
| Startup_int.xxx | 4374 | 3633 | 140 | 601 | 41 |
| All 62 packages | 122876 | 52541 | 58210 | 12125 | 59 |

The other 59 packages produced zero links **within the parsed scope**, not proof
that they never use fonts. The 41 Startup links reproduce the earlier direct
StyleFont findings; the 18 other links expand the previous scan's coverage.

### MC2Game.xxx

Source SHA256: `13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641`.

| Owning default export | Properties | Font targets |
|---|---:|---|
| 10973 Default__MC2UIScene_Reaction | 6 | Four critical-damage fonts, ComboFont, DamageUPFont |
| 12549 Default__MC2HUDUI | 8 | Number/enemy/damage/healing fonts and four damage fonts |
| 14107 Default__MC2MiniGame_BarPress | 2 | Font_LimitTime, Font_MaintainTime |

These 16 links refer to twelve local `font_ui` Font objects. There is no direct
top-level link to General_15 in the successfully parsed MC2Game objects.
That is **not** evidence General_15 is unused or that a warning uses a HUD font.

### Engine.xxx

Source SHA256: `f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a`.
Both Default__Canvas.Font and Default__UIStyle_Text.StyleFont refer to
EngineFonts.SmallFont. This supplies a serialized fallback candidate beyond
the four FontName strings; runtime override/inheritance precedence is unverified.

## Coverage and serialization limits

The scanner reads NetIndex followed by a complete bounded tagged-property
sequence. It validates each top-level ObjectProperty's four-byte value and
signed object-table reference. If a later property fails, it discards all links
from that object and records the object and failure reason. Array indices are
retained. Offsets address the decoded logical package, not the compressed file.

Class/function/state/struct/enum/const/property metadata, Font/MultiFont and
Texture2D assets, and empty payloads are explicitly skipped. Other failures are
listed under `unparsed`, never silently reported as zero references. Nested
StructProperty/ArrayProperty values, native tails, class inheritance, imported
class descendants and dynamically selected resources are not resolved.

Of MC2Game's 9703 unparsed objects, 4749 are UIComp_Event, 3629 UIComp_DrawImage
and 954 UIComp_DrawString. Their initial bytes do not match the assumed
NetIndex-plus-tags layout. Selected samples expose a plausible tagged sequence
at payload offset 16 rather than 4, but this observation does not establish the
prefix's schema or general applicability. The tool deliberately does not search
for plausible tag starts or hard-code an unverified 12-byte skip.

**Next offline work:** establish the component prefix from independent format
evidence and exhaustive bounds checks, then follow draw-string style structures
and warning scene references. The minimal Chinese display gate and same-scene
candidate/recovery checks remain for the user's game tests. No bulk translation
starts from these static links alone.

## Reproduction

Run from the repository root with a new output path:

```powershell
python tools/inspect_font_references.py build/poc-game/disc1/MC2Game/CookedXenon/MC2Game.xxx --sha256 13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641 --consumers --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-MC2Game-consumers.json
python -m unittest discover -s tests -p test_font_consumers.py -v
```

The existing `--inventory` and default FontName modes remain unchanged. The
three modes are mutually exclusive. Source hash/profile/decoder guards and
new-output/readback checks apply to every mode. A zero exit status means the
report completed, not complete object coverage: inspect its coverage/unparsed
fields. Full package-specific reports remain local under
`build/font-consumer-verification/package-consumers/`; the local summary is
`build/font-consumer-verification/scan-summary.json`.

Ten new synthetic tests cover custom owning classes, exact offsets, indexed
properties, imported MultiFont targets, non-Font property names, null/wrong-class
targets, malformed sizes/references, all truncated payload lengths, metadata
skips, atomic object-level failure, hash guards and mutually exclusive CLI modes.
Baseline: 258 tests passed (one optional native test skipped). Modified: 268
passed (one skipped); with MC2_LZX_LIBRARY explicitly selected, all 268 passed.
