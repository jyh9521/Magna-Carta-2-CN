# Font/Canvas native rows: initialized pointers, not cold descriptors — 2026-10-19

## Evidence and confidence

**Verified offline:** three complete initialized8-byte name/code tables, full
UTF-16BE native symbols, exact Class-scoped native declarations, their retained
native indices, full zero sentinels and13 exact .pdata function entries. Both
independently reconstructed disc images produce byte-identical reports. No
native instruction, wrapper, function, game or emulator is invoked.

**Unverified:** registration/dispatch reachability, global native-index tables,
wrapper/helper semantics, native Font layout, glyph indexing, text measurement
results, active font and Chinese rendering. Declared function extents are not
code-body semantic proofs. Game testing remains entirely user-operated; this
workflow does not deploy resources, send input or change configuration.

## The storage distinction changes the next analysis

The earlier UIComp_DrawString table is a cold12-byte name plus two-zero-word
descriptor, requiring an initializer proof. Font, MultiFont and Canvas instead
store nonzero code pointers directly after each name. The new reader has the
explicit profile `ppc-initialized-native-row8-v1`; it does not silently adapt the
old cold profile or invent an adjustor/initializer for this storage.

| Exact Engine Class/export | Name/code table | Rows | Immediate Function headers | Non-native headers retained as omissions |
|---|---|---:|---:|---:|
|Font /4920|0x8320d290|2|2|0|
|MultiFont /11474|0x8320d3e8|1|1|0|
|Canvas /5062|0x8320d028|10|22|12|

The13 bindings account for **all declared-native functions** of those exact
classes, not a picked successful subset. Each table includes one full eight-
byte zero sentinel. Table hashes cover the complete rows plus that sentinel;
all method names, code addresses and exact .pdata starts must validate.

### Measurement entry coordinates now anchored statically

| Full symbol | Code word | Native token retained |
|---|---|---:|
|intUFontexecGetResolutionPageIndex|0x8243d3c0|0|
|intUFontexecGetScalingFactor|0x8243d478|0|
|intUMultiFontexecGetResolutionTestTableIndex|0x8243bdd8|0|
|intUCanvasexecStrLen|0x8263e9f0|464|
|intUCanvasexecTextSize|0x8263eca0|470|

Canvas also retains DrawTile466, DrawText465 and DrawTextClipped469, plus five
declared-native methods with token0. No nonzero token is replaced with0 to fit
the earlier cold-descriptor checker. The table associates names with code words;
it does not prove what a VM dispatch of token464/470 actually invokes.

## Complete native-only declaration inventory

`inspect_function_metadata.py --class ... --native-only` first validates every
immediate Function header. It records owner/Class/source identity, flags and
native token for both native and non-native functions. Only native parameter
stubs are then parsed. The12 Canvas scripted bodies remain explicitly omitted,
not decoded by the limited UI-wrapper grammar and never executed.

A malformed non-native header remains an error, not a silent omission. The new
initialized-table reader requires zero unparsed headers, exact inventory and
omission counts, matching native parsed/header identities and the complete
selected-object set. Bool-as-int tokens/IDs, forged sources/classes, missing
metadata, duplicate names and arbitrary class/prefix substitutions fail.
Native full-name prefixes must retain their UE3 U/A prefix and exact Class name.

This opt-in mode requires --class and excludes --include-scripted. Default
metadata CLI output remains byte-compatible; the six old native plans/readers
are unchanged. The new reader never rereads Engine itself: its report says so,
and hashes/validates reproducibly generated, source-locked metadata instead.

## Reproduce metadata from user-supplied originals

Original package identities/extraction are documented in RESOURCE_SURVEY.md,
FONT_BINDING_AUDIT.md and BUILDING.md; image reconstruction is in NATIVE_IMAGE.md.
The example root below is the retained original extraction, not a deployed
candidate. An equivalent original root can be substituted without changing the
reports, provided every explicit hash matches. Use fresh output paths.

```powershell
$root = 'build/poc-game/disc1/MC2Game/CookedXenon'
foreach ($class in @('Font', 'MultiFont', 'Canvas')) {
  python tools/inspect_function_metadata.py "$root/Engine.xxx" `
    --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a `
    --class $class --native-only `
    --reference-package Core "$root/Core.xxx" 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815 `
    --lzx-library build/lzx/native-verified/ue3_lzx.dll `
    --output "build/initialized-native-table-verification/$($class.ToLowerInvariant())-methods.json"
  if ($LASTEXITCODE -ne 0) { throw 'metadata inventory failed' }
}
```

These reports contain no runtime samples and must reproduce these complete hashes:

| Scope | Metadata report SHA256 |
|---|---|
|Font|63b7fae367b771c60ab53e1fcaaba02c282efb062b8a009b914c755a0eb93f05|
|MultiFont|49504af61b26871907bfd2b3693c2e8599a2613eb1031d05999e63b7730eab3d|
|Canvas|86310872caffa62026e1c684368f2ad02949b6b61b6c0c3053f7d7c47bbb074d|

The explicit LZX decoder is used only to read source containers. It is not a
game/native-function executor. Default synthetic tests need no native decoder.

## Inspect all three initialized tables

```powershell
python tools/inspect_initialized_natives.py `
  build/xex-native-verification/final/disc1-pycryptodome.bin `
  --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 `
  --plan references/probes/font-metrics-initialized-tables.json `
  --plan-sha256 a3ad86387425934f3c3cd283114900be32b2ae7b60536e63f1bed4c5114b424e `
  --native-report Font build/initialized-native-table-verification/font-methods.json `
  --native-report MultiFont build/initialized-native-table-verification/multifont-methods.json `
  --native-report Canvas build/initialized-native-table-verification/canvas-methods.json `
  --output build/initialized-native-table-verification/disc1-final.json
```

D2 substitutes its independently reconstructed image and a fresh report path.
Literal stdout is `{"bindings": 13, "executed": false, "tables": 3}`, exit0.
Every metadata label must match the plan; source/plan/report bytes are bounded,
hashed, rechecked before/after publication and reopened exactly. A failed check
removes only the tool's own unchanged output, preserving external changed bytes.

Eighteen self-authored initialized-table tests and six native-only metadata tests
cover initialized/cold separation, tokens0/nonzero, header/selection completeness,
full symbol boundaries, sentinels, source/type/scope/extent guards, duplicated
code/table candidates, hashes, input mutation and output reopening. Two additional
repository-only contracts check documented metadata hashes and cold/initialized
plan separation. Full default suite628 tests passes with one optional LZX skip.

## Next offline work

Trace the now source-anchored Font and Canvas metric wrappers into their helper
calls before assigning native Font offsets or direct-index semantics. SmallFont
still has non-remapped-font-mode-unverified coverage; no new remap conversion,
font deployment or bulk translation is justified by these table associations.
