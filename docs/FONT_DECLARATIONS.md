# Font container declarations, not a native layout guess — 2026-10-19

## Result and confidence

**Verified offline:** all five immediate property exports of the hash-locked
Engine.Font Class now have validated declaration records. Array inner references
are exact local/owned property definitions; the FontCharacter StructProperty
resolves to its complete five-member schema/default report, and Textures resolves
to Texture2D. The CharRemap MapProperty stores **two null type references**.
It remains opaque, not an invented IntProperty/ByteProperty pair.

No game, emulator, target function or instruction is executed. No Font, game
resource or user configuration is modified. Game testing remains user-operated.

**Still unverified:** native member offsets/alignment, copied runtime values,
the source IsRemapped -> metric word+0x68 bridge, a live Font instance, lookup
behavior, draw-path equality and Chinese pixels. Container declaration support
does not decode container values or authorize a non-remapped Font conversion.

## Original-source identities

Engine.xxx SHA256:
f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a.
Core.xxx reference SHA256:
1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815.

| Engine export | Exact property | Kind / reference evidence |
|---:|---|---|
|4913|Font.Characters|ArrayProperty -> local4900 Font.Characters.Characters|
|4912|Font.Textures|ArrayProperty -> local4901 Font.Textures.Textures|
|4911|Font.CharRemap|MapProperty -> null/null; raw flags0000000000001002|
|4910|Font.IsRemapped|IntProperty|
|4909|Font.Kerning|IntProperty|

Inner4900 is a StructProperty targeting ScriptStruct4908 Font.FontCharacter.
Its complete schema contains StartU/StartV/USize/VSize IntProperty and TextureIndex
ByteProperty. Inner4901 is an ObjectProperty targeting Class1222 Texture2D.
These are script/serialization type identities, not recovered C++ field offsets.

The local Next run is Characters -> Textures -> CharRemap -> IsRemapped -> Kerning
-> Font.FontCharacter. The terminal object is a same-owner ScriptStruct, not a
missing property. The audit scans all immediate property exports and retains
this boundary. It does **not** claim to have parsed UClass.Children, merged
inheritance or recovered an allocation order/layout from a property-name list.

The five declarations are structurally parsed without errors, while
`serialized_type_trees_complete=false` correctly records the opaque map. A
zero error count is not a complete-map-type or native-layout success flag.

## Generic tooling contract

`ue3_struct_defaults.property_declaration` additionally recognizes the verified
ArrayProperty single-reference tail and MapProperty two-reference tail:

- Array inner and typed Map key/value refs must be positive local definitions
  of exact Core property kinds, immediately owned by the container.
- Typed Map key/value refs must be distinct. Every immediate property child
  must be accounted for; extra/unreferenced definitions fail.
- Map null/null preserves `opaque-null-type-references`. Half-null maps fail.
  Nulls are not assigned guessed key/value types, widths or flag meanings.
- Truncation, trailing bytes, wrong owner/class and unsupported kinds fail.
- Scalar declaration output stays unchanged; only container records gain the
  additional `container` field.

`property_declaration_audit.py` follows container references with depth/node
bounds, optionally binds referenced ScriptStruct schemas, inventories exact
local Class properties and validates local Next runs. Imported/foreign/cyclic
or ambiguous property edges fail rather than disappearing from a successful
subset. Non-property same-Class boundaries remain explicit.

Container **value** decoding is separate. Existing struct-default validation
now explicitly rejects serialized Array/Map value tags until a typed decoder
exists. Missing default slots remain unknown, not zero. This closes a possible
false-success route after expanding the declaration-kind set.

## Reproduce the read-only Font audit

Use original packages extracted as described in BUILDING.md/RESOURCE_SURVEY.md.
The example paths refer to retained originals, not deployed candidates. An
equivalent original root can be substituted while keeping names and hashes.

```powershell
python tools/inspect_property_declarations.py `
  build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx `
  --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a `
  --class Font --bind-structs `
  --reference-package Core build/poc-game/disc1/MC2Game/CookedXenon/Core.xxx 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815 `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll `
  --output build/font-declaration-verification/font-final.json
```

Use a fresh output path. Literal stdout:
`{"native_layout_verified": false, "selections": 1, "unparsed": 0}`, exit0.
The CLI validates all original package identities before loading the optional
decoder, snapshots/rechecks every input including that decoder, writes a new
report and reopens its exact bytes. Object mode supports selected exact property
paths with `--object`; Class mode inventories all immediate properties.

Fifteen new self-authored tests cover typed arrays/maps, opaque maps, ownership,
all container-payload truncations, nested cycles/depth, full local Next runs,
typed-default rejection, source guards and output/input mutation/readback.
Default suite658 tests passes with one optional LZX skip. No original assets or
native libraries are needed by default tests. Older scalar/default/function
metadata and native inspector reports are independently replayed for byte
compatibility; these results remain offline evidence only.

## Next work

Follow Font's native serialization/class layout evidence instead of assigning
offsets from declaration order. The native metric code's u16 map entries and
20-byte glyph stride cannot fill CharRemap's null type references or change the
17-byte serialized glyph contract. Source/native bridging and drawing behavior
remain separate investigations.
