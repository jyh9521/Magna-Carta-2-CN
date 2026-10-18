# Native style getter and guarded font overlay — 2026-10-19

## What is verified, and what is not

**Verified offline:** exact hash-locked PPC words and their static branch/call
shape. Both independently reconstructed disc images produce byte-identical
reports. This is a bounded template/metadata checker, not an interpreter,
emulator, native call, deployment or game/render test.

**High-confidence deduction:** the object word+0xd8 is the custom DrawFont and
bit0x20000000 at+0xe4 enables that override. The paired scoped SetFont and
DisableCustomFont chains established these coordinates; this follow-up finds
the same mask/pointer at the guarded copy into output+0x20. The destination
field name DrawFont remains a deduction, not a recovered complete C++ layout.

**Unverified:** virtual target identity, active style/font, constructors, call
reachability/order, external helper effects/register preservation, actual font
rendering and Chinese acceptance. Game testing remains entirely user-operated.

## The two guards matter

The leaf window0x826a92c0..0x826a937c contains47 instructions, with no calls and
only forward conditional branches/returns. The font-specific subpath is:

1. Load object-relative flag word+0xe4; mask with rlwinm(0,2,2), i.e.0x20000000.
2. At0x826a931c, branch to0x826a9330 when that bit is zero.
3. Otherwise load object-relative pointer word+0xd8 and compare it with zero.
4. At0x826a9328, branch to the same bypass when the pointer is zero.
5. Only the double-nonzero path reaches0x826a932c, storing that word at output+0x20.

The other exact-template stores target output offsets0/4/8/12/56/60/61;
the floating alpha store also targets12, not32. No bypass path writes output+0x20.
Thus a set override bit **alone** is not evidence that a font word is replaced.
In this checked path a null pointer preserves the preexisting output word,
even when the bit is set. The pointer word is copied, not dereferenced here.
Conditions refer to the words read along the path, not sampled runtime values.
No arbitrary input state or native instructions are executed by the checker.

The other mask groups and byte/float transfers are structurally retained but
not promoted to a general style evaluator, floating-point model or constructor.

## Getter/call association

- GetFinalStringStyle descriptor code word0x823fe0d8 has a checked tail at
  0x823fe1c4; its direct call goes to0x826a90c0 and the call result is stored.
- That128-byte helper reads virtual slot byte-offset0x128. A zero virtual-call
  result branches past the producer/copy/overlay call sites. The nonzero path
  calls0x826c6300, then0x82874e80 with operand r5=0x64, then the leaf0x826a92c0.
- GetAppliedStringStyle's checked tail0x826a9094..0x826a90c0 reads the same
  virtual slot0x128 before its indirect call and result store.

These are shared slot/call-site facts, **not** proof of a concrete vtable target.
The100-byte operand is verified; calling0x82874e80 a proven memcpy or asserting
the producer's complete base-style semantics would go beyond this evidence.
Earlier parameter extraction and helper register preservation are not evaluated.

Separately, the existing hash-locked struct reader now parses Engine
ScriptStruct5390 UIRoot.UICombinedStyleData: nine owned declarations include
DrawFont5387 as ObjectProperty -> Engine.Font, plus TextColor, ImageColor,
FallbackImage, AtlasCoords, TextAttributes, TextAlignment[2], AdjustmentType[2]
and bInitialized. Its explicit persistent DrawFont default is null. These are
serialized declarations/defaults; do not compute native offsets from tag sizes
or equate this persistent null with an active getter output.

## CE/PPC function metadata, not guessed next-start extents

`tools/ppc_pdata.py` reads the little-endian PE32 exception-directory entry3
using the reconstructed **virtual** layout. This profile requires exact agreement
with one .pdata section's RVA/virtual size; raw file pointers are not followed.
Each8-byte entry contains two big-endian words: begin address and packed fields
(prologue8 bits, function length22 bits, two raw flags). Length/prologue units
are four-byte instruction words. Source provenance and hashes are in
references/pdata-research.lock.json; the independent format reader uses no
upstream SDK/runtime. MIT attribution is retained in NOTICE and licenses/.

All44484 records at RVA0x26f200, size0x56e20 pass alignment, positive length,
prologue<=length, sorted/nonoverlapping and bounded code-range checks.
Raw high-bit pairs0/1/2/3 occur3/38782/3/5696 times. The reader retains all pairs
without guessing unwind behavior or interpreting ThirtyTwoBit as CPU width.
Metadata-declared extents are not a full control-flow or code-coverage proof.

| Start | Declared end | Next start would mislead? |
|---|---|---|
|lookup0x82414188|0x82414208|no gap in this case|
|initializer0x82e6afc8|0x82e6b1a0|next0x82e6b280 leaves a gap|
|SetFont0x823fdb68|0x823fdc40|adjacent|
|DisableCustomFont0x823fdf28|0x823fdfb4|next0x823fdfb8 is4 bytes later|
|final helper0x826a90c0|0x826a9140|next0x826a9198 is88 bytes later|

The selected initializer0x82e6afd0 is exactly its declared prologue end and
the previous straight-line analysis ends at the declared function end.
All18 descriptor code words have exact entries; the new report lists them.
The overlay leaf0x826a92c0 has **no** exact or covering entry. Its188-byte checked
window ends with BLR, but is not labelled a .pdata-proven function extent.
Missing leaf records are explicit null, never a reason to extend a predecessor
to the next listed function or claim the leaf contains no code.

## Reproducible read-only CLI

Keep the original ui-draw-string-native plan unchanged: its report shape and
bytes stay reproducible. The extended plan opts in to style_selection.

```powershell
python tools/inspect_native_bindings.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/ui-draw-string-style-selection.json `
  --plan-sha256 d0809f9b7b96a321f05fb586186b219d1e331d860996ef7daf6223276683fef5 `
  --native-report build/native-binding-verification/native-methods.json `
  --output build/native-style-verification/disc1-final.json
```

Use a **new** output path on every invocation. Literal stdout remains
`{"bindings": 18, "executed": false, "font_mask": "20000000"}`, exit0.
The report carries style windows/guards, native declared extents, absent leaf
entry and whole-table summary. Input files are reread before/after output;
report bytes are reopened. Neither image nor game resources are modified.
Exact Engine/native-report source identity and generation command remain in
NATIVE_BINDINGS.md; Engine is not silently reread by this CLI.

Fifteen new synthetic tests use self-authored PE/CE records, encodings and
metadata, not game files. They cover all384 template bytes with fresh hashes,
the two distinct bypasses, disjoint font destination, declared ends/gaps, raw
flag pairs, truncation, ordering/overlap, source hashes, opt-in compatibility
and report reopening. Default CI needs only the Python standard library.
Full source regression480 ->495 -> isolated rollback480; decoder-enabled495.
Ignored build/native-style-verification retains exact local outputs and rollback.

Next offline investigations follow the base-style producer, virtual target,
conditional refresh helper and native constructors/measurement. None of these
static findings substitutes for the user's Chinese display acceptance.

Follow-up: NATIVE_CLASS_TABLES.md adds an independent opt-in plan associating
full class-name operands, leaf callback table stores and the concrete static
slot0x128 word/getter routing. This does not establish an active vptr or runtime
dispatch and does not change the original profile's narrower evidence scope.
