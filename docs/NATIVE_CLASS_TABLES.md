# Class-prefix, callback and style-table association — 2026-10-19

## Evidence and confidence

**Verified offline:** four complete UTF-16BE native class names, their bounded
registration argument chains, three call-free leaf initializer windows, three
read-only table windows and the shared61-instruction getter branch shape.
Both original-derived disc images produce byte-identical reports. No PPC
instruction, constructor, registration function or game is invoked.

**High-confidence deduction:** these name/callback/table chains identify the
class-associated virtual-table families and generated default-constructor helpers.
The exact verified facts are code/data operands and their static associations,
not an observed active component vptr or proof of the registration callee's
complete argument semantics. Do not erase this distinction in downstream tools.

**Unverified:** actual registration/constructor reachability, allocation/zero-fill,
post-construction property loading, concrete active instances, complete vtable
extent, external helper/register-preservation semantics, effective Font, layout
measurement and Chinese pixels. All game acceptance stays with the user.

## Preserve the class prefix and the actual name operand

The native literals begin at full NUL boundaries with a leading `U`. The checked
registration chain materializes that full address, then passes address+2 in r6:
exactly one UTF-16BE code unit later. This is a verified operand, not permission
to strip prefixes from arbitrary resource identifiers or translate native names.
The first U is retained in the report together with the suffix/name pointer.

Each selected registration window has16 words: lis/addi chains, one stack store,
the full-name+2 operand in r6, size in r4, code word in r9 and a direct call to
0x823a6150. Unknown/mutated instructions fail even with refreshed expected hashes.
Selected windows must sit inside exact .pdata-declared registration functions.

| Full native name | Name literal | Registration start | r9 code word | r4 size | Table written by leaf |
|---|---|---|---|---|---|
|UUIComp_DrawString|0x821c0c30|0x823fe298|0x826a4a20|0x110|0x821c13c0|
|UUIComp_DrawStringEditbox|0x821c0c58|0x823fe4c8|0x826a4b90|0x148|0x821c1508|
|UUIComp_DrawStringSlider|0x821c0c8c|0x823fe5e0|0x826a4cc8|0x110|0x821c1650|
|UUIComp_DrawCaption|0x821c0cc0|0x823fe3b0|0x826a4cc8|0x110|0x821c1650|

The Slider and Caption associations share one callback/table; they are not
silently collapsed into one class. Size values are verified call operands,
not a complete recovered native class layout or heap-allocation measurement.

The same hash-locked Engine package independently declares these four Classes:
15601 DrawString,15609 Editbox,18529 Slider and18527 Caption. The latter three
have DrawString as local superclass; DrawString -> DrawComponents -> UIComponent
is the observed Engine-local chain. This confirms stored class names/relations,
not a native ABI equivalence or an imported parent's complete ancestry.
The native inspector anchors its existing scoped Engine metadata report; it
does not reread Engine or consume that additional local declaration report.

## Initializer stores do not establish font defaults

All three84-byte leaf windows start with an entry-r3 null test/conditional return
and end with BLR. Exact templates prove no calls, no r3 modification and these
explicit writes on the nonnull path:

- Word+0x6c first receives0x82123a6c and later0x821c1794. Both ordered stores are
  retained, not flattened to the final value before recording their evidence.
- Word+0 receives the class-associated table listed above.
- Words+0x70 and+0x74 receive0; bytes+0xa0/+0xa1/+0xbc/+0xbd receive3.

The base and derived templates have different store orders, preserved by the
report. No word+0xd8 or+0xe4 is written in these windows. Therefore these leaf
instructions **do not prove DrawFont=null or its override flag=0**. The input
field values, allocator defaults and later property application are not inferred.
No .pdata record covers the leaf windows; their selected BLR endings are not
mislabelled metadata-proven full function extents.

The earlier lis/addi candidates0x826a4998/4ad8/4c40 also write table addresses
but contain calls and cleanup-shaped adjacent code. A vptr-like store alone
does not identify a default constructor. They are not the checked leaf r9 code
words above and are not used to assert initial font state.

Another potential trap: the registration helper's local research shows zeros
at its own result-object offsets including+0xd8/+0xe4. That is a different
object/context; those writes are not UIComp_DrawString component defaults.

## Read-only table association and shared getter routing

The checker derives .rdata's virtual RVA/size/flags from the reconstructed PE
header, requires readable/non-writable/non-executable bytes, and rejects overlap
with code ranges or .pdata. It never uses raw-file pointers. This distinction
rejects a real .pdata occurrence of0x826a8f00 that a bare pointer scan found.

Each table window contains81 aligned code-range words, exact-hash locked;
81 is the selected verification window, **not a claimed complete vtable size**.
All three windows have:

- slot byte-offset0x124 ->0x826a8e70;
- slot byte-offset0x128 ->0x826a8f00;
- slot byte-offset0x12c ->0x826a9e98, except Editbox ->0x826aa268.

This connects the previously verified getter wrapper/final-helper slot0x128
to a concrete **static class-associated table word**. An active runtime dispatch
through that table remains unverified. Other entries are hash/range checked,
not given guessed method names from their positions.

The getter0x826a8f00..0x826a8ff4 has an exact .pdata record. Its template binds
entry r3 to r30 and reads a related pointer from entry+0x28. After the indirect
slot0x124 call, a nonzero result selects r30+0xe8; a zero result selects
r31+0x174. Their pre-call aliases are the entry object and related pointer;
their preservation by the indirect callee is not independently proved.
Later code uses a pointer word at selected-base+0x1c,
with conditional clearing/resolution calls retained in the complete template.
The direct call targets are0x826c5b30,0x826c4998 and0x826afc88. Their full
semantics, the slot0x124 target and register preservation across calls remain
unverified. Treat StringStyle/owner-primary-style field names as candidates,
not recovered native offsets from serialized property order.

## Reproduce, without game execution

Use the same original-derived image and exact native-report hash from
NATIVE_BINDINGS.md. Earlier native-only and style-selection plans remain unchanged,
with byte-identical legacy report output. The new plan explicitly opts in:

```powershell
python tools/inspect_native_bindings.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/ui-draw-string-class-tables.json `
  --plan-sha256 daca5d6c5d24af06d4b9b697124ca3cc870d4e0ea84086bd16047d14005c0774 `
  --native-report build/native-binding-verification/native-methods.json `
  --output build/native-constructor-verification/disc1-final.json
```

Every invocation requires a new output. Literal stdout remains
`{"bindings": 18, "executed": false, "font_mask": "20000000"}`, exit0.
The class_tables report adds exact names/callbacks/stores/table slots/getter
operands and explicit confidence flags; input/output bytes are reopened.

Twenty new synthetic tests cover both leaf families, every registration/leaf/
getter byte with refreshed expected hashes, every table byte with original
expected hashes, fresh-hash structural failures, suffix/boundary/class guards,
.rdata vs .pdata, gaps/declared ranges, null guard/order, signed address halves,
legacy opt-in compatibility and CLI/input reopening. Other table-slot semantics
are deliberately not invented when a new trusted plan changes a valid code word.
Two additional repository byte-contract tests enforce LF probe sources and exact
documented plan hashes. Full source regression495 ->517 -> isolated rollback495;
optional decoder517.
No game, crypto, Capstone or original assets are needed by default CI.

Next offline work follows registration callback storage/invocation, allocation
and property/default phases, plus the slot0x124 and base-style producer paths.
These remaining phases are required before making an effective Font claim;
the two-guard font overlay from NATIVE_STYLE_SELECTION.md still applies.

Follow-up: OBJECT_INITIALIZATION.md checks the small metadata-helper chain,
size/callback words and selected callback/clear-phase sites. It distinguishes an
intermediate clear from later property/default effects; active font/default
values remain unverified. Earlier class-table plan inputs/reports are unchanged.
