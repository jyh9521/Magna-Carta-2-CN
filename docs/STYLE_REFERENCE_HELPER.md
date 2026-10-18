# Style-reference helper: name and class operands — 2026-10-19

## Evidence boundary

**Verified offline:** the predicate's direct-call target0x826c5ec0 has an exact
90-word body, a .pdata-declared360-byte extent ending0x826c6028 and a three-word
prologue. Every instruction/branch and three bounded16-word registration
argument windows are structurally checked, together with their complete
UTF-16BE class/tag literals. Both disc-derived images yield byte-identical
reports. No PPC instruction, function, constructor, game or emulator executes.

This continues STYLE_SELECTION_PREDICATE.md's static call association, not a
runtime invocation. No source assets, user settings or deployment are changed.
All game/display acceptance remains user-operated.

**High-confidence deduction:** the three call/name chains are class-based
style-tag fallback logic, and the final external call constructs a name pair.
The verified facts are operands, exact words, literals and branch destinations;
external callees' contracts and returned runtime class identities are not
proved by a registration window inside their functions.

**Unverified:** lookup/constructor-call semantics, register preservation across
calls, loop termination, serialized/native field correspondence, the actual
owner pointer, effective style/font, instance values and Chinese rendering.
Neither this helper's output-zero stores nor its optional flag writes establish
that any font pointer or component override is initialized to zero.

## Verified static shape

After the prologue save call, the body aliases r3/r4/r6 in r28/r30/r31. These
are **pre-lookup-call aliases**; their correspondence to entry arguments and
their preservation across other calls require the external contracts. The
report deliberately names them post-prologue-save register values.

1. Direct stores clear two words at post-save r3+0/+4 and conditionally clear
   the post-save r6 word. These are output/name-shaped words, not a Font.
2. The body reads the two words at reference-register+0/+4. If their comparison
   gates and post-save r5 permit, it passes a64-bit copy through stack+0x50 and
   r5+0xb0 to0x8262bc38. A nonzero external result routes through two output
   word copies, optionally stores1 through the flag alias, and returns.
3. Otherwise it loads the reference word+8. A zero value skips the class-like
   walks. Three ordered calls are followed by equality/parent-walk comparisons.
   Each walk repeatedly loads word+0x3c; no cycle bound is present in this checked
   code. The tool records the loops without pretending to run or terminate them.
4. Each matching comparison routes to one full tag-literal address. The common
   call0x824719a0 receives that address, stack+0x50, r5=0, r6=1 and r7=1. Two stack
   words are copied to the output alias. The meaning of those constants and the
   external call's complete name-construction ABI remain unverified.

The lookup can have side effects; the two output copies and flag stores do not
turn this into a pure-function proof. The actual pointers supplied to these
loads/stores are never read from a running target.

## Three class-name/tag operand associations

| Helper call target / registration entry | Full native name | Fallback literal | Literal address | Registration size operand |
|---|---|---|---|---:|
|0x82409d30|UUIStyle_Text|DefaultTextStyle|0x821c5df8|0x68|
|0x82361ec0|UUIStyle_Image|DefaultImageStyle|0x821c5dd4|0x90|
|0x82409c18|UUIStyle_Combo|DefaultComboStyle|0x821c5e1c|0x9c|

Each registration entry has an exact .pdata record covering the selected
entry+52..+116 argument window. The known template passes the complete native
name+2 in r6, a bounded size in r4, a callback operand in r9, r5=0, and calls the
already checked common registration helper. Neither the callback's body nor
the rest of each registration/cache function is part of this new proof.

The three literal pointers occur at helper offsets+280,+292,+304; the ordered
class-call sites occur at+160,+196,+232. A swapped association fails the complete
helper template even if its own literals and argument-window hashes are valid.

The parent-load loops begin at comparison offsets+176,+212,+248, load+0x3c eight
bytes later and branch backward sixteen bytes later. They are recorded as raw
word/edge relationships, not a recovered native UClass ABI.

## Relationship to the serialized UI evidence

OWNER_PRIMARY_STYLE.md already keeps DefaultComboStyle's six text-data CDO
Font observations separate from General_15's component route. Read-only follow-up
also finds one supplied DefaultTextStyle and one DefaultImageStyle tag. The text
and combo definitions each retain six SmallFont default-plane observations;
the image definition is not forced through a text-font fallback.

Both warning renderer CDOs separately serialize RequiredStyleClass=UIStyle_Combo.
Those source facts are compatible with this native literal/branch family, but
they do not prove reference-register+8 contains that field in a live object or
that this fallback executes for the warning. No source field is copied into
native memory by the checker; no resolved style/font is chosen for the player.

## Opt-in reproduction

The prior five native plans remain byte-unchanged. This sixth plan adds the
explicit `style_reference_helper` block after the predicate prerequisite.

```powershell
python tools/inspect_native_bindings.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/ui-style-reference-helper.json `
  --plan-sha256 679e59ab780347d608d41076acdf61e89fa19a90ee369ef6acc266aead2e31e1 `
  --native-report build/native-binding-verification/native-methods.json `
  --output build/style-reference-helper-verification/disc1-final.json
```

Use a fresh output path. D2 substitutes its independently reconstructed image.
Literal stdout remains `{"bindings": 18, "executed": false, "font_mask": "20000000"}`,
exit0. The360-byte helper window SHA256 is
a6224373a7fef78fb2a29aa019c7ea5a712b8032d8ff9badd015bd4a9dcd6bfd.
The CLI rechecks all inputs and reopens exact output bytes; no disassembler or
game binary is required by default CI.

Fifteen new self-authored helper tests cover all552 selected code bytes with refreshed
hashes, independent64-bit copy encodings, literal content/boundaries, ordered
association/type/range/metadata guards, prerequisite compatibility, CLI readback
and preservation of externally changed output. Three additional Font-class
identity tests cover the real package distinction below. Full default suite602 tests
passes with one optional LZX skip. Decoder-enabled testing is offline only.

## SmallFont format audit, without assuming a glyph-index mode

The first real SmallFont coverage invocation exposed a tooling assumption:
Engine's local Font Class has class_path=Font, not an imported Engine.Font.
The previous auditor rejected that valid object before writing a report (exit2).
The shared payload reader already accepts its structure and validates256 glyphs.

The coverage auditor now recognizes either an exact Engine.Font Class import
or a positive local reference to the exact Font Class definition. It does not
accept arbitrary suffix matches or unrelated local objects named Font, and it
does not promote format recognition to runtime class identity.

The same source-locked warning plan now produces a report for both SmallFont
aliases (exit1):256 glyphs, IsRemapped=false,39 requested literal codepoints per
font, all explicitly `non-remapped-font-mode-unverified`. This is **not** a
missing-remap verdict or proof of absent visible glyphs. Direct-index/fallback
semantics remain unknown; no Unicode value is used as a glyph index by guess.
The existing supplementer still rejects fonts without an explicit remap rather
than silently converting them. No SmallFont bytes are changed.

## Next offline work

Correlate the lookup/name-construction paths with scoped declarations, and
inspect the newly retained SmallFont candidates' format/coverage without
silently treating them as the active font. Keep direct serialized links, CDO
observations and native operand associations distinct. No font deployment or
bulk translation follows from an unobserved fallback branch.
