# Constructor metadata, callback and intermediate clear — 2026-10-19

## Evidence levels and purpose

**Verified offline:** a name-scoped class registration argument reaches a
metadata result object's callback word+0x11c and size word+0x50, through fully
checked register-save/base-constructor templates. A separate wrapper reads
callback words at+0x11c and contains the corresponding indirect call site.
The allocation routine has a zero-fill call site followed by further calls.
Both original-derived disc images produce byte-identical reports.

**High-confidence deduction:** this is the generated constructor-metadata and
object-construction path for the previously associated UI classes. The verified
facts remain code operands, stores and control shapes, not live metadata values.

**Unverified:** active registration/instances, arbitrary allocator paths, later
property/default application, external helper effects/register preservation,
effective font values and Chinese rendering. No target code or game is executed.
The mathematical fill partition below accesses no target memory and is not a VM.

## Keep the metadata object separate from the component

The new opt-in plan extends the four class-name associations from
NATIVE_CLASS_TABLES.md. Their r4 size operands are0x110 (DrawString/Slider/Caption)
and0x148 (Editbox); r9 contains their previously verified leaf callback words.

- Registration helper0x823a6150 has77 words, with exact .pdata extent ending
  0x823a6284. It saves entry r9 in r28 and calls base helper0x823a0a48.
- That57-word base helper ends0x823a0b2c, contains no calls, preserves r3/r4/r28,
  and stores entry r4 at result+0x50. Its conditional global-list writes do not
  bypass or replace this size store.
- The77-word helper stores r28 at result+0x11c and sets result's table word to
  0x82154758. Its save/restore helpers are also structurally checked, so argument
  preservation inside this particular metadata chain is no longer merely an
  assumed external-call convention. This is not a general ABI proof.
- The bounded73-word metadata table has slot byte-offset0x120 ->0x823a8e60.
  That8-byte leaf reads r3+0x50 into r3 and returns. The table window is not
  labelled a complete virtual table or an active runtime table.

This supplies a conditional static bridge between the class registration size
operand, constructed metadata size word and size-getter slot. Metadata can be
modified later; no current class-size/instance assertion follows automatically.

The metadata initializer also writes zeros at **its own**+0xd8/+0xe4. Those
addresses do not denote a UI component's font fields. Broadly treating all its
stores as zero would also be wrong: metadata+0x14c receives8. Keep object contexts
and individual nonzero stores distinct.

## Callback dispatch and allocation failure

The wrapper0x823b99c0..0x823b9c14 is149 words, full-hash locked. Selected entry,
allocation-result, dispatch, post-callback and exit windows are structurally
checked; the remaining words are explicitly **not** semantically interpreted.

Before the allocation call, entry r3 is aliased in r23. The result of
0x823b8b28 is copied from r3 into r30. A zero result branches directly to
0x823b9be8, beyond the selected callback site; its exit window is checked too.
This is not an invented null-Class guard: the r23==0 branch in the dispatch
window still leads to a load from r23+0x11c, not a successful null-Class return.

The ordinary selected path loads a code word directly from r23+0x11c. Another
path calls0x822d0b48 and loads the same offset from that helper's returned pointer.
The code then moves r30 to r3 and uses BCTRL at0x823b9b18. Raw flag/ancestor
conditions are retained without guessing a named flag catalog or asserting that
the original class's callback is always chosen. The fallback helper remains
unverified. Do not confuse a direct metadata field+0x11c with a method-table
slot+0x11c found by an indiscriminate pointer-load scan.

Calls0x823ae250/0x823af930 appear in the checked post-callback window and may
perform additional work. Their effects are not inferred from their positions.
Allocation-callee register preservation/runtime reachability remain separate
unknowns even though the small metadata-helper chain is now fully checked.

## Zero-fill helper: a bounded arithmetic contract

At0x823b94a4..0x823b94c8, the allocation routine reads virtual slot0x120 on r24,
moves its return value into r5, sets r4=0, moves r30 into r3 and calls0x8286f490.
The broader739-word allocation function is exact-hash/.pdata bounded, not fully
decoded or granted a complete control-flow proof by this inspector.

The helper0x8286f490..0x8286f530 is exactly40 words. Its checked stores cover a
prefix,16-byte blocks, up to three4-byte words, and up to three tail bytes. For
the zero-fill call operand, insert/rotate operations leave the stored word zero.
The entry destination in r3 is not changed, and this helper has no calls or
input-memory reads. End-of-window BLR does not invent a missing .pdata entry.

For a32-bit nonwrapping effective destination and0<=size<=MAX_IMAGE, assuming a
writable range and the checked call preconditions, the static interval argument is:

```text
prefix = min(size, (-address) & 3)
remaining = size - prefix
blocks16 = remaining >> 4
words4 = (remaining >> 2) & 3
tail = remaining & 3
prefix + 16*blocks16 + 4*words4 + tail == size
```

The prefix counter starts at size+1 and the counted/conditional branch tests
before the first byte store. Thus size0 does not write even at an unaligned
address. Remaining partitions are contiguous/disjoint; the report ties each
partition to its actual store instructions. Branch prediction bits remain
explicit in the template, not a substitute for the count/condition rules.
Instruction references: [IBM bc](https://www.ibm.com/docs/en/aix/7.1.0?topic=set-bc-branch-conditional-instruction)
and [IBM rlwimi](https://www.ibm.com/docs/en/aix/7.2.0?topic=is-rlwimi-rlimi-rotate-left-word-immediate-then-mask-insert-instruction).
Versioned source scope/availability is recorded in references/object-initialization-research.json;
no vendor prose, runtime or disassembler code is integrated.

`zero_fill_partition` computes those integer intervals only; it does not run or
simulate the target instruction stream, inspect a process, or write image bytes.
All four synthetic alignment cases for each declared class size cover the
relative font-pointer range0xd8..0xdb and flag range0xe4..0xe7. Actual destination
translation, writable memory, later metadata changes and runtime values are not
verified by this arithmetic exercise.

## An intermediate zero is not a constructor/render default

The allocation path continues after the clear site. Later direct call sites
include0x823b0f18,0x823ab900 and0x823b8a00 before returning to the construction
wrapper. Their full effects are unknown, and the selected class leaf callback
does not write font wordsD8/E4. Consequently:

- The checked zero-fill contract supports **zero immediately after that call
  under its preconditions**, not zero at the callback entry or rendering time.
- Default/archetype/property application could change component fields after
  this intermediate clear. Persistent ScriptStruct defaults remain a separate
  evidence plane; explicit null/zero there is not a sampled active component.
- Another call to the same zero helper at0x823b8f80 targets a stack buffer
  (r31+0x124), not the component. Its presence is not a second font-default proof.

## Reproduce and validate offline

```powershell
python tools/inspect_native_bindings.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/ui-object-initialization.json `
  --plan-sha256 2bb1051a31c7ef172fd0a9228785c148f112107411ddd07b8f7f183871537f88 `
  --native-report build/native-binding-verification/native-methods.json `
  --output build/object-initialization-verification/disc1-final.json
```

Require a fresh output path. The exact existing image/metadata anchors are
documented in NATIVE_BINDINGS.md; no Engine package is implicitly reread here.
Literal stdout remains `{"bindings": 18, "executed": false, "font_mask": "20000000"}`,
exit0. Prior native/style/class plans retain their exact-input report bytes.

Twenty new tests use synthetic metadata/code words and pure arithmetic, including
all checked-window byte mutations with fresh hashes, all4 alignments at lengths
0..1024, interval/canary bounds, zero lengths/large limits, helper/table/pdata
guards, opaque-region scope, context separation and CLI immutability/reopening.
Repository byte-contract tests now check the exact documented CLI hash argument
for all four LF plans, not merely a hash appearing somewhere in a document.
Full source regression517 ->537 -> isolated rollback517; optional decoder537.
Default CI requires no game assets, crypto or Capstone.

Next offline work follows the later property/default phases and the base-style/
measurement path. Font values at callback entry and actual drawing remain
unverified; all game acceptance continues to belong to the user.
