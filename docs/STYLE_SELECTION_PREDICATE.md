# The static slot124 selection predicate — 2026-10-19

## Progress and confidence boundary

**Verified offline:** the four class-associated tables previously checked in
NATIVE_CLASS_TABLES.md all have slot0x124 = 0x826a8e70, not an unknown constant
function. Its exact36-word body is now structurally checked, including every
conditional edge, input offset, direct call and return sequence. The .pdata
record starts there, ends0x826a8f00 and declares a three-word prologue.
Both disc-derived images produce byte-identical reports. No target function,
instruction, constructor, game or emulator was executed.

This closes the **static table-word -> predicate-body** association. It does
not prove an active instance has one of these vptrs or that either getter
branch runs. The old report's runtime-facing selection-target flag remains
false; the new report explicitly calls its result a static association.

**High-confidence deduction:** the entry addic/subfe. pair normalizes the loaded
word to a nonzero boolean. The exact words312affff/7c695111 and their CR0 branch
are verified; no runtime word, carry state or native evaluation is sampled.

**Unverified:** serialized-to-native field names/layout, the entry+0x28 owner
identity, callee preservation, indirect effects, actual field values, effective
style/font, object precedence, text measurement and Chinese rendering. Game
testing stays entirely with the user. No deployment or configuration change
accompanies this analysis.

## Predicate operands and control flow

All offsets below are relative to function start0x826a8e70 unless stated.

| Instruction offset | Literal operation / branch |
|---:|---|
|0x0c|load entry-r3 word+0x104|
|0x10,0x14|alias entry-r3 in r11 and entry-r4 in r5|
|0x18,0x1c|addic/subfe. normalization pair|
|0x20|CR0 not-equal -> epilogue+0x80|
|0x28|entry-r4 zero -> epilogue+0x80|
|0x2c..0x48|load/OR entry words+0x100,+0xfc,+0xf8,+0xf4; compare with zero|
|0x4c|OR nonzero -> literal r3=1 at+0x7c|
|0x50..0x5c|r6=0, r4=entry-r3+0xe8, r3=stack+0x50, BL0x826c5ec0; r5 retains entry-r4|
|0x60..0x68|load helper-return pointer word0; nonzero -> literal1|
|0x6c..0x78|load pointer word4; set r3=0; zero -> epilogue, otherwise literal1|
|0x7c|set r3=1|
|0x80..0x8c|restore stack/LR and BLR|

The function is therefore not evidence for an unconditional owner/default
route. The early word gate, four-word gate and helper-result gates all matter.
No actual warning-instance values are supplied to any of them.

The checked body directly stores only stack/LR bookkeeping, not entry-object
fields. The called helper can have effects; neither this fact nor the template
establishes that the predicate as a whole is side-effect free. The helper's
metadata entry is retained, but its instructions/semantics are **not** part of
this36-word proof. Its returned pointer is read, not dereferenced in advance by
the offline tool, and no null-guard guarantee is invented for that return.

## Relationship to the two getter sources

The existing getter calls virtual slot0x124 and selects component-like+0xe8
for nonzero, versus the related-object-like+0x174 for zero. Its chosen reference
then uses word+0x1c. Numerically,0xe8+0x1c=0x104; the predicate's four-word span
0xf4..0x100 is0x0c..0x18 relative to0xe8. Those offset equalities are verified,
not a recovered native ABI.

The serialized UIStyleReference schema and PrimaryStyle/StringStyle source
observations suggest possible field names for these words. That is still a
layout hypothesis: this profile deliberately reports
`serialized_field_names_verified=false` and does not attach serialized zero,
null, AssignedStyleID or DefaultStyleTag values to native memory.
OWNER_PRIMARY_STYLE.md's SmallFont default-plane candidates and the original
General_15 component candidates remain separate; this predicate does not pick
one or justify another font patch.

## Opt-in reproduction

The old four native plans stay byte-unchanged. The fifth plan adds only the
explicit `style_predicate` block to the class-table plan. Its whole file uses
Git LF bytes, guarded by a documentation/hash regression test.

```powershell
python tools/inspect_native_bindings.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/ui-draw-string-selection-predicate.json `
  --plan-sha256 8cd91fde1ea42eb02fd42c243d8d94b9daa5285d6e876ccbbdab41e15bf080fe `
  --native-report build/native-binding-verification/native-methods.json `
  --output build/selection-predicate-verification/disc1-final.json
```

Use a fresh output path; D2 uses its independently reconstructed disc2 image.
Exact stdout remains `{"bindings": 18, "executed": false, "font_mask": "20000000"}`,
exit0. The144-byte window SHA256 is
b3a92e719121d144d6e9213adea79c326120091408d4f0f38106c7467ccdc113.

The checker requires the previously verified class/getter report, checks every
supplied slot124, rejects wrong/missing .pdata extent/prologue and rejects
mutated instructions even if a caller supplies a matching new window hash.
Unexpected config fields, bool-as-int addresses, unaligned/out-of-code helpers
and self-overlapping helper targets fail. No optional disassembler is needed
by the tool or default CI; temporary disassembly was only a research aid.

Eleven new self-authored tests cover all144 code bytes, independent literal
encodings, five distinct edges, association/metadata/type/range guards, old
opt-in compatibility, new-output/readback and late-input-mutation cleanup.
Default suite584 tests passes with one optional LZX skip; native-decoder mode
is a separate offline decoder test, not a game test.

## Next offline lead

Inspect the helper0x826c5ec0 and corroborate named property/class relationships
without treating offset arithmetic as ABI proof. The retained helper disassembly
suggests name/class-dependent fallback branches, but their external calls,
register preservation and semantic identities remain unverified. The UUIObject
registration operand variant and UIObject.PrimaryStyle declaration lead are
also retained for this correlation, not treated as completed layout recovery.
