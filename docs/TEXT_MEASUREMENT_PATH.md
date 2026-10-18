# Canvas.TextSize: native metric branches — 2026-10-19

## Evidence boundary

**Verified offline:** the initialized Canvas.TextSize binding, its38-word tail,
the directly called47-word helper and a122-word call-free metric window. All828
selected code bytes have exact structural templates and hash guards, not merely
refreshed hash comparisons. Both disc-derived images reproduce the same report.
No PPC instruction, wrapper, game or emulator is executed; no resources or user
configuration are changed. Game acceptance remains user-operated.

**High-confidence deduction:** the observed pointer/array/map fields are Font,
Characters, Textures, CharRemap, IsRemapped and Kerning-related storage. Source
Font declares IsRemapped and Kerning as IntProperty, and the offsets/operations
are consistent with those names. This is **not** a verified serialized/native
offset bridge or proof of an active Font instance.

**Unverified:** the caller's live object identity, register preservation across
earlier external calls, initialization/serialization into these offsets, runtime
field values, lookup-chain termination, actual warning font, equality with the
drawing path, layout result and Chinese pixels. No coverage flag is upgraded
from these observations: SmallFont's existing audit stays mode-unverified.

## Three source-anchored windows

| Window | Coordinates | Structural scope |
|---|---|---|
|Canvas.TextSize tail|0x8263ee24..0x8263eebc|38 words; exact end of the declared wrapper|
|direct helper|0x8263d5c8..0x8263d684|47 words; exact .pdata extent, five-word prologue|
|metric leaf window|0x826c7e18..0x826c8000|122 words; no exact or covering .pdata record|

The third window ends at its own BLR and has no external calls. It is a bounded
selected template, **not** a .pdata-proven function extent or a range inferred
from the next function start. Conditional returns and both loops are retained.

### Wrapper -> helper -> parameter block

The wrapper tail loads r3 from word r24+0x3c. Its zero branch bypasses the metric
helper through a separate logger/cleanup-shaped path; their semantics are not
invented. The nonzero branch passes that unchanged r3 to0x8263d5c8, with output-
like stack pointers in r4/r5 and a selected string-like pointer in r6. The empty
string operand is independently checked to start with a zero16-bit unit.

The47-word helper clears both output words and tests its own entry-r3. On the
nonnull path it stores that pointer at stack+0x68, builds a block at stack+0x50,
loads exact0.0/1.0 constant bits, stores scale1.0 at block+0x10/+0x14 and calls
0x826c7e18. The pointer is therefore at block+0x18. Float outputs at block+8/+0xc
are converted/copied after that call. No actual pointer is supplied by the
offline checker and no computed size is presented as observed game output.

## Verified character-selection branches

The leaf loads a font-like pointer from parameter+0x18, clears output floats
at+8/+0xc and returns conditionally for null/empty inputs. It reads text via
16-bit loads and advances the string pointer by two bytes. That does not prove
anything about an upstream lexer, surrogate handling or drawing implementation.

### Mode word zero

For native word pointer+0x68 equal to zero, the code masks a unit to16 bits and:

1. compares it with the word at pointer+0x40;
2. if in range, computes a20-byte stride into the array at pointer+0x3c;
3. keeps the code unit as the selected index only when that record's word+0xc
   is nonzero; otherwise it selects the literal index0x7f;
4. also selects0x7f for the out-of-range path.

This is an exact static **conditional direct-index branch**, not a constant
Unicode-remap path. In a separately assumed runtime state with count256/mode0,
the two BMP probe values exceed that count and route to0x7f. The source SmallFont
records alone do not prove that runtime state or that this routine measures the
warning. Do not report this conditional deduction as failed Chinese rendering.

### Mode word nonzero

The other branch checks native words+0x60 and+0x58, uses a mask derived from
word+0x64 minus1, and follows entries from the array at+0x54. The selected entry
stride is8: next-link word+0,16-bit key+4,16-bit value+6; -1 terminates a miss.
The successful value is loaded as16 bits; missing paths select0x7f. Runtime map
validity, power-of-two sizing and acyclic links are not assumed or simulated.

### Shared metric reads

The selected index is again range-checked, then uses20-byte records. The code
reads a texture-index byte at+0x10, validates it against native count+0x4c and
tests a pointer from the array at+0x48. Width/height-like words are read at record
+8/+0xc. Native word+0x6c contributes a converted scalar on a nonterminal unit.
A float read through the runtime pointer in slot0x83263c14 at object+0x430 also
affects the width-like calculation; the slot's runtime value/meaning is unknown.

These20-byte in-memory records are **not** permission to change the existing
17-byte on-disk native glyph records. The serialized Font reader/writer and its
non-remapped supplement guard are unchanged.

## Reproduction

Generate the three exact native-only metadata reports as documented in
INITIALIZED_NATIVE_TABLES.md. This opt-in plan extends that initialized-table
plan; all prior plans retain their original bytes and default report shapes.

```powershell
python tools/inspect_initialized_natives.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/font-metrics-measurement-path.json `
  --plan-sha256 7351e9138fbfcfbb5b0dec681596f0b57dfcaa95eec20939142fc34cdb138cf4 `
  --native-report Font build/initialized-native-table-verification/font-methods.json `
  --native-report MultiFont build/initialized-native-table-verification/multifont-methods.json `
  --native-report Canvas build/initialized-native-table-verification/canvas-methods.json `
  --output build/measurement-path-verification/disc1-final.json
```

Use fresh output paths; D2 substitutes its independently reconstructed image.
Literal stdout stays `{"bindings": 13, "executed": false, "tables": 3}`, exit0.
Report `measurement_path` preserves all unknowns separately from verified words,
including false `source_font_mode_bridge_verified` and
`native_rendering_path_equivalence_verified`.

Fifteen new self-authored tests cover all828 selected bytes with refreshed
hashes, independent mode/fallback/loop words, constant bits, exact caller/helper
metadata, the absent leaf record, scope/range/type guards, opt-in compatibility
and CLI readback. Default suite643 tests passes with one optional decoder skip.
These are static/synthetic tests, not game tests.

## Next offline work

Corroborate Font's ArrayProperty/MapProperty declarations and serialization
before connecting disk IsRemapped to word+0x68. The current scoped declaration
reader reports those three property kinds unsupported; this is not evidence
that Characters/Textures/CharRemap are absent. Keep those errors, investigate
the representation and compare the separate draw path. No font is converted or
selected based only on this metric window.
