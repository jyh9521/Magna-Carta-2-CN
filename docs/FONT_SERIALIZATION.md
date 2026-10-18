# Font serialization: operand anchors and record widths — 2026-10-19

## Evidence and confidence

**Verified offline:** two class-registration argument chains, two13-word null-
guarded callbacks, bounded readonly table windows and six complete function
templates (58/17/81/75/47/27 words). Each function has an exact declared .pdata
extent/prologue and an independent hash guard. Every selected function,
registration and callback byte is covered by refreshed-hash mutation tests.
This inspector is independent of, and does not relax, the old style-class
profile. It reads user-supplied reconstructed bytes without executing them.

**High-confidence deduction:** slot34 is the Font serialization chain; the word
before the remap array is Kerning-related storage at entry+6C, and the final word
is IsRemapped-related storage at entry+68. The two array/element chains match the
already parsed disk record sizes and the earlier TextSize native offsets.

**Unverified:** external parent/texture/archive-call contracts, callee register
preservation, field identity across those calls, actual archive direction,
loaded Font state, selected warning font, draw-path equivalence and Chinese
pixels. No generic ABI/layout is reconstructed from these selected windows.
The existing parser still requires the pre-remap word to be zero; this work
does not silently enable nonzero Kerning or reinterpret opaque Map declarations.
Existing SmallFont coverage remains mode-unverified. Game QA stays with the user.

## Reproducible source locks

Plan: `references/probes/font-serialization.json`, profile
`ppc-font-serialization-v1`. Reconstructed image SHA256:
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`,
base82000000, size20119552. Both source-disc images produce identical reports.
Hash the plan independently before running; the CLI requires both hashes,
checks input stability and exclusively creates/reopens a new report.

```powershell
$plan = 'references/probes/font-serialization.json'
$sha = (Get-FileHash $plan -Algorithm SHA256).Hash.ToLowerInvariant()
python tools/inspect_font_serialization.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan $plan --plan-sha256 $sha --output build/font-serialization.json
```

No Capstone, emulator, optional decoder or complete proprietary fixture is
required for the committed self-authored tests. Capstone5.0.7 was used only for
initial read-only disassembly; the validator independently constructs words.
The evidence extends the project's earlier initialized-native/metric/declaration
research; it does not attribute selected-game findings to upstream UE3 code.
The existing .pdata reader retains its separately documented upstream format
reference and raw-flag boundary.

## Class association, not runtime vptr evidence

| Full literal | Literal address | Argument window | Callback | Table window | slot34 |
|---|---|---|---|---|---|
| UFont |821AE46C|822E648C|8261D4B8|821AE490,70 words|8261C8B0|
| UMultiFont |821AE478|82429D9C|8261D3A8|821AE5A8,71 words|8261CA60|

Each16-word registration window materializes the **full U-prefixed literal**,
then passes literal+2 in r6. Its size argument is70/7C respectively, not a
general field-layout calculation. Both windows sit at declared getter+52.
The callback stores table at entry+0, zero at54/58/5C/60, and8 at64; neither
callback writes68 or6C. Bounded windows do not prove full table extent.

UFont is preceded by non-string pointer bytes, not a NUL code unit. A global
preceding-NUL scan missed it. This new profile accepts only an explicitly
instruction-anchored, terminated, exact literal in readonly data; it does not
strip U prefixes, accept substring guesses or weaken the old class scanner.

## Ordered call/transfer observations

Font slot34 target8261C8B0:

1. entry-object alias r30 / archive-like alias r29, external parent helper;
2. entry+3C passed to8261CCF8 (81-word glyph-array template);
3. entry+48 passed to external82605678 (texture-array hypothesis);
4. entry+6C / size4 supplied to archive-like vtable slot4;
5. entry+54 passed to8261CF20 (75-word map-array template), followed by
   bucket-capacity/rebuild/free branch;
6. entry+68 / size4 supplied to archive-like vtable slot4.

UMultiFont's17-word target calls the Font target, then passes entry+70 to
external822D6668. No float-array schema is claimed from that call alone.

Glyph-array code contains size20 allocation/index arithmetic and two direct
calls to8261D0C0, plus a20-byte non-load-loop stride. The47-word record template
supplies offsets0/4/8/C/10 and transfer sizes4/4/4/4/1 through slot4:17 bytes,
not a copied20-byte native record. Map-array code uses size8 and two calls to
8261D050. Its27-word element supplies offsets4/6 and sizes2/2:4 bytes; the
native next-link at0 is absent from that transfer sequence.

These checks preserve the important distinction between opaque serialized
property declarations, explicit disk payload parsing, selected native address
arithmetic, and unobserved runtime state. The next offline task is to establish
external archive/texture-helper return and preservation contracts before
promoting the source IsRemapped -> native+68 bridge or changing coverage policy.
