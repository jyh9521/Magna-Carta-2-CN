# Static UI native bindings and paired font-word operations — 2026-10-19

## Evidence planes

**Verified offline:**18 scoped Engine native method declarations match18 full
names in a cold native table. A bounded116-instruction initializer analysis
recovers every8-byte descriptor, including the zero sentinel. A32-word lookup
template verifies stride12 and selection of row+4 when the comparator returns0.
Both independently reconstructed disc images produce byte-identical reports.
No instruction, initializer, lookup or native method is invoked.

**Verified instruction operands/chains:** the statically associated SetFont and
DisableCustomFont code set/clear complementary0x20000000 bits in a word at
entry-object-register-relative0xe4. SetFont stores a word read from stack+0x50
at object-register-relative0xd8. Both chains also contain an addend0xc4.

**High-confidence deduction:**0xd8 is the DrawFont pointer word and the matching
0xe4 bit is bOverrideDrawFont. This follows the scoped SetFont.NewFont
ObjectProperty -> Engine.Font declaration, paired named method descriptors and
complementary instruction chains—not a guessed serialized UProperty offset.
The0xc4 addend is a candidate TextStyleCustomization base, not a complete proven
native struct layout. Entry-r3 alias instructions are checked; call preservation
and the stack parameter producer are not evaluated.

**Unverified:** constructor values, initializer/runtime reachability, comparator
semantics, dynamic call order, actual component instances, effective Font asset,
native text measurement and Chinese pixels. No game/emulator/input/deployment/
configuration change or bulk story translation occurs here.

## Identity and reproducible inputs

Native image SHA-256:
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`,
base0x82000000,20119552 bytes. The two original XEX identities and dual-backend
reconstruction/inverse proof remain in NATIVE_IMAGE.md. Original XEX files stay
distinct and unchanged; the common derived image is the code/data input here.

The trusted plan is references/probes/ui-draw-string-native.json, SHA-256
`37357ba123caecd98c0cc3ff1629028d40f7e5a2cde18e3c64068ac2f137afa9`.
It locks the image, Engine source, exact native metadata report and both code
windows. It supplies a locale-neutral profile, not a blind offset patch.

First reproduce the native-only declaration report:

```powershell
python tools/inspect_function_metadata.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --lzx-library build/lzx/native-verified/ue3_lzx.dll --class UIComp_DrawString --output build/NEW-native-methods.json
```

Expected exit1 deliberately retains the5 non-native siblings outside the18
native records. The report byte SHA must be
`c991997d33d16e15137b20bc16f1e55cf9497541466081a88f0653c71ddb4652`.
It was independently regenerated and compared byte for byte this milestone.
Do not change the expected hash merely to admit a different report; a changed
producer/schema requires deliberate plan review and source revalidation.

```powershell
python tools/inspect_native_bindings.py build/xex-native-verification/final/disc1-pycryptodome.bin --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 --plan references/probes/ui-draw-string-native.json --plan-sha256 37357ba123caecd98c0cc3ff1629028d40f7e5a2cde18e3c64068ac2f137afa9 --native-report build/NEW-native-methods.json --output build/NEW-native-bindings.json
```

The binding inspector uses only the standard library. It **does not reread
Engine.xxx**: it verifies the exact previously source-validated report identity,
typed declaration/source/class/export fields and method set. The two input
planes remain explicit. It never trusts an upstream success boolean alone.
Expected output is18 bindings/font_mask20000000/executedfalse, exit0; failed
hash/type/template/range/identity/output guards return2. Reports must be new;
input snapshots and exact output bytes are rechecked, not False==0 JSON equality.

## Recovered static entry associations

The full-name table starts0x83225928, contains18 rows of12 bytes and a full
zero sentinel at0x83225a00. Each row contains a big-endian UTF-16 name pointer
and8 cold zero bytes. The prefix is `intUUIComp_DrawStringexec`; names are read
at actual aligned NUL boundaries. Interior/suffix guesses are not accepted.

| Method | Descriptor code word |
| --- | --- |
|NotifyResolveStyle|0x823fd5f0|
|SetStyleResolverTag|0x823fe1e0|
|GetStyleResolverTag|0x823fd550|
|GetFinalStringStyle|0x823fe0d8|
|GetAppliedStringStyle|0x826a8ff8|
|DisableCustomAlignment|0x823fe048|
|DisableCustomAttributes|0x823fdfb8|
|DisableCustomFont|0x823fdf28|
|DisableCustomOpacity|0x823fde98|
|DisableCustomColor|0x823fde08|
|SetAlignment|0x823fdd38|
|SetAttributes|0x823fdc40|
|SetFont|0x823fdb68|
|SetOpacity|0x823fda88|
|SetColor|0x823fd9f0|
|RefreshValue|0x823fd980|
|GetValue|0x823fd868|
|SetValue|0x823fd778|

These are static associations to code-range words, not observed runtime
registration or full function-extent proofs. All second descriptor words are0;
nonzero adjustment words are outside this profile. Compiler aliases would not
be silently reinterpreted as a different name.

Initializer window0x82e6afd0..0x82e6b1a0 is straight-line lis/li/addi,
stw-to-symbolic-stack, ld-from-fully-known-stack, std-to-descriptor and a terminal
branch0x8286f454. The prologue/helper before the selected window is not evaluated.
Constants use64-bit sign extension; effective addresses must be canonical32-bit
values. DS-form displacements include their multiply-by4, and updating forms
are rejected. The analysis tracks byte-level def/use evidence through reused
symbolic stack slots. It does not read a process stack or overlay recovered
values onto the original image. Unknown registers/reads, calls/branches inside
the window, stack-base changes, unexpected/duplicate/incomplete stores fail.

Lookup0x82414188..0x82414208 is structurally checked, not just hash-labelled.
It uses comparator0x8286eac0, advances an index*12, returns0 at the sentinel,
or returns the selected row+4 after comparator-zero. Prologue/epilogue helper
semantics and the comparator's actual string behavior remain separately unverified.

## Paired font-word chains and coordinates

SetFont's entry-r3 -> r30 alias is at0x823fdb90; its checked field chain starts
0x823fdbf0. It reads flags at r30+0xe4, ORs with0x2000 shifted16, writes flags
back and stores the stack+0x50 word at r30+0xd8. The initializer store linking
this method descriptor is0x82e6b180.

DisableCustomFont's r3 -> r31 alias is at0x823fdf3c; checked chain0x823fdf7c
reads r31+0xe4, extracts its old bit using rlwinm(3,31,31), applies
rlwinm(0,3,1), and writes it back. Its mask keeps0xdfffffff, exactly the
complement of setter0x20000000. The conditional call target is0x826a9380;
the checker records the call/skip shape without claiming this helper's effect.
Its descriptor store is0x82e6b16c. Source aliases/word chains are verified;
semantic field names and full object layout retain the confidence distinctions
at the top of this document.

Keep three coordinate systems separate: native virtual code/data addresses,
object-register-relative word offsets0xd8/0xe4, and logical UE3 package tag
offsets. Native packed-bit0x20000000 is **not** the serialized BoolProperty
tag-header0/1 value. Cold native function descriptors are not component defaults.

## Validation and remaining path

Twenty synthetic tests use self-authored image/table/PPC words/metadata, not
game code. They cover static binding/provenance, all1024 circular32-bit masks,
all initializer prefix truncations, every128-byte lookup mutation, every font
chain/alias byte mutation, cold/sentinel/string/descriptor guards, typed metadata,
unknown registers/stack/DS forms/control flow, path/hash/reopening and source
mutation. Default CI needs no game files, crypto or Capstone. Full regression
460 ->480 -> independent source rollback460; native-decoder-enabled480.
Exact local commands/results remain under ignored build/native-binding-verification/.

Independent implementation references versioned IBM instruction documentation:
[rlwinm](https://www.ibm.com/docs/en/aix/7.2.0?topic=is-rlwinm-rlinm-rotate-left-word-immediate-then-mask-instruction),
[ld](https://www.ibm.com/docs/en/aix/7.2.0?topic=set-ld-load-doubleword-instruction),
[std](https://www.ibm.com/docs/en/aix/7.1.0?topic=set-std-store-double-word-instruction),
[oris](https://www.ibm.com/docs/en/aix/7.1.0?topic=set-oris-oriu-immediate-shifted-instruction).
Source URLs/research scope are retained in references/native-binding-research.json;
no vendor instruction prose/runtime is integrated. Previous REA unsupported-PPC
boundary remains; this is a bounded static format/data-flow tool, not a VM.

Next offline work follows constructor/default initialization, getter/format
helper selection and text measurement. Effective Font and Chinese rendering
remain unverified, with all game acceptance still reserved to the user.
