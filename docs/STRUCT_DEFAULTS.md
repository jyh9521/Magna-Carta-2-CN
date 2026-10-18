# Serialized UI struct defaults and scoped declarations — 2026-10-19

## Evidence levels

**Verified offline:** hash-locked Engine/Core packages contain explicit
ScriptStruct defaults. This closes a serialized-data gap; it does not execute
C++ initialization, choose a loaded font, or prove current widget memory.
Original packages/configuration remain unchanged and no game is launched.

The warning renderers' TextStyleCustomization is bound by defining Class,
property export outer and native StructProperty type reference—not by searching
for the first similarly named struct:

```text
Engine Class15601 UIComp_DrawString
  -> property15535 TextStyleCustomization -> ScriptStruct5371 UIRoot.UITextStyleOverride
  -> property15534 StringStyle            -> ScriptStruct5255 UIRoot.UIStyleReference
```

Both TitleMap renderers2191/2204 resolve these same declarations. The definition
explicitly serializes DrawFont=null and bOverrideDrawFont=0. All five override
flags are serialized0, and all five nested text-attribute flags are serialized0.
These are observed values, **not assumptions from absent fields**. Package-level
prototype/CDO data still shows no explicit font override along the previously
inspected chains. Native construction and dynamic mutation remain unverified;
no claim of an effective runtime flag or actual drawing font follows.

The instances serialize alignment override1 and TextAlignment[0]/[1]=1.
Native ByteProperty metadata points to the stored EUIAlignment catalog, whose
slot1 is UIALIGN_Center. The static-array enum slots0/1 are
UIORIENT_Horizontal/UIORIENT_Vertical. These are verified stored names/slots,
not a screenshot or a claim about resulting on-screen placement.

## Original package identities and exact locations

- Engine.xxx SHA256
  `f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a`.
- Core.xxx SHA256
  `1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815`.

Engine ScriptStruct5371 starts at logical2389777, size530. Defaults start48
bytes into that payload. DrawFont's serialized object word is logical2389925;
bOverrideDrawFont's serialized bool word is logical2390239. Both are0. Every
one of the ten relevant bool words (five overrides plus five text attributes)
was independently read from its reported four-byte logical location.
Offsets are **logical package bytes**, not compressed physical offsets or
runtime C++ member addresses. Bool bit packing/memory layout is not recovered.

## Supported metadata layout

The reader is restricted to the observed big-endian446/licensee25 data-only
profile. A metadata UObject starts with NetIndex followed by an empty tagged
property stream. Its native ScriptStruct header is:

| Payload offset | Stored field |
|---:|---|
| 12 | UField super reference |
| 16 | UField next reference |
| 20 | ScriptText reference (required0 in supported profile) |
| 24 | Children property-chain head |
| 28 | CppText reference (required0) |
| 32 / 36 | Line / TextPos (required0) |
| 40 | script size (required0; bytecode is not skipped heuristically) |
| 44 | raw struct flags u32 |
| 48 | tagged persistent struct defaults |

The editor-shaped fields really are present in these Xenon resources. A console
filename is not permission to omit them or scan forward for a plausible None.
Unknown nonzero editor/script data, stack/CDO prefixes, bad bounds and trailing
bytes fail instead of selecting another guessed layout. Raw struct flags1 are
reported; they are not substituted for a native-initializer proof.

Each UProperty declaration has its own UObject/UField prefix, dimension word,
big-endian64-bit property flags, category FName, static-array enum reference and
type-specific reference words. The verified branch supports Bool/Int/Float/Name/
Str/Byte/Object/Class/Struct/Interface declarations. Packed dimension high bits
and networked metadata are unsupported rather than silently truncated/skipped.
Property flags are not the export table's separately ordered LO/HO object flags.
ClassProperty definitions serialize ObjectProperty default tags in this profile.
InterfaceProperty values here are one serialized object-reference word; this
does not recover native interface-pointer layout.

Children chains must be bounded, acyclic, local to the correct owner, complete
against immediate property exports and free of duplicate names. Default fields
must match declared names/types/static indices; nested tagged structs are checked
against their referenced declaration schemas. Opaque binary structs such as
LinearColor remain opaque. Enum catalogs are bounded FName arrays after UField;
unknown ordinal slots remain unnamed, not guessed.

## Inheritance without inventing zero defaults

UIRoot.STYLE_ID (Engine5234) imports Core.Object.Guid (Core72) as its super.
Its own56-byte payload has no persistent default fields and no own declarations.
The four A/B/C/D declarations and explicit zero default records exist in the
parent. The report keeps parent records separately and lists four missing own
default slots; it does not silently materialize zeros or assert native merge
order. Other inspected defaults can serialize a complete nested STYLE_ID value.
Superclass cycles, unavailable imports, shadowed declarations and invalid parent
or nested default data fail. Explicit parent/default planes remain distinct from
renderer prototypes, class defaults and native/runtime state.

## Bool offset correction and scalar decoding

BoolProperty has size0: its value is in the tag header, before the empty raw
payload. The old flattened logical_package_offset pointed four bytes too late.
The shared tagged reader now preserves bool_value_offset, and the flattener's
logical_package_offset points at the actual bool word. logical_payload_offset
separately records the empty-payload position; value_storage=tag-header makes the
distinction explicit. Old bool offsets must not be reused as patch addresses.
Existing StyleFont ObjectProperty probe offsets are unchanged; no game bytes
are patched by this correction.

The shared flattener now handles UITextAttributes, InterfaceProperty references
and exact-width FloatProperty values. Float bits are retained; nonfinite values
are reported as bits/non_finite without emitting invalid NaN JSON. Bounds,
recursion/count limits and scalar-width checks remain mandatory.

## Reproducible commands

```powershell
python tools/inspect_struct_defaults.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --object UIRoot.UITextStyleOverride --object UIRoot.UIStyleReference --object UIStyle_Combo.StyleDataReference --object UIRoot.UITextAttributes --object UIRoot.STYLE_ID --object UIDataStoreSubscriber.UIDataStoreBinding --reference-package Core build/poc-game/disc1/MC2Game/CookedXenon/Core.xxx 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-struct-defaults.json
```

This requests6 definitions, all parsed with0 errors. Root default field counts:
UITextStyleOverride16; UIStyleReference8; StyleDataReference9;
UITextAttributes5; STYLE_ID0 own (parent4); UIDataStoreBinding6.
The inspector writes only a new metadata report, reopens it and rechecks source
package bytes. Exit0 means all requested definitions parsed;1 records partial
unsupported definitions;2 means an input/output/profile failure.

For the existing warning trace, add --audit-struct-defaults to the documented
--deep --audit-bindings command in FONT_BINDING_AUDIT.md, including the original
Core reference. The flag requires both modes. It emits scoped declaration,
struct-default, inherited schema/catalog and explicit-instance planes separately.
The trace retains1209 selected/parsed UI objects (480 prefix4;729 prefix8),
2 text matches and12 font-state paths. All4 property bindings succeed; the old
7 non-UI classification errors remain explicitly outside that parsed UI count.

## Format sources and limits

Format research uses Eliot van Uytfanghe's MIT Unreal-Library commit
`8236c39b79e30887a487ecf9b018204e430a5ebc`:
[UField](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UField.cs),
[UStruct](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UStruct.cs),
[UScriptStruct](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UScriptStruct.cs),
[UProperty](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/Props/UProperty.cs),
[UInterfaceProperty](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/Props/UInterfaceProperty.cs),
[UEnum](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UEnum.cs).
Exact file hashes are locked in references/struct-default-research.lock.json;
version thresholds retain the existing ui-style-research lock. The Python
implementation is independent; no upstream runtime/source is integrated.

REA open_binary rejected the original UE3.xxx header as unsupported; no native
session or target execution was opened. The supported format-aware project
reader provides the actual package evidence. This does not establish any
native-code disassembly or runtime result. The bounded diagnostic is retained
locally, not hidden or repeatedly retried with a renamed file.

Baseline381 -> modified397 -> independent source rollback381; native-enabled397.
Sixteen new synthetic tests include real self-authored package CLI input,
complete/inherited/nested declarations, exact bool-header positions, typed scalar
and enum slots, scoped class binding, cycles/omissions/owners, unsupported header/
flag/type/size paths, missing defaults, every struct-payload truncation and CLI
mode guards. Default CI needs no game, font source or decoder DLL.
Local reports/commands and original hash rechecks are under
build/struct-defaults-verification/; no full game asset enters Git.

Next bounded investigation: declared UIComp_DrawString functions SetFont15555,
DisableCustomFont15563, GetAppliedStringStyle15568 and GetFinalStringStyle15571.
Their export identities/sizes were found; names alone do not prove bodies,
native behavior, call order or active drawing. No invocation is authorized here.
