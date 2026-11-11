# Native payload coverage: UE3 446/25

## Purpose and evidence levels

`tools/ue3_native_coverage.py` is a read-only, locale-neutral parser for two
explicit profiles. It does not infer that a package or class is text-free merely
because its name sounds technical, or because a byte search found no Korean.

- **Verified:** source SHA-256, supported version, field boundaries, array
  lengths, complete selected-export byte consumption and reference checks.
- **High-confidence deduction:** the Xbox shader subclass tails are compatible
  with pairs of big-endian `uint16` register indices/counts. Their individual
  native serializer functions have not been traced. This does not become a
  verified absence of every possible native string slot.
- **Unverified:** exact shader parameter names and GPU instruction semantics.

The output deliberately separates `fully_consumed` (byte framing) from
`native_semantic_coverage_complete`. ShaderCache reports
`known_native_string_fields: 0`, **`native_string_fields: null`**, and explicit
`semantic_unresolved_regions`; it does not erase uncertainty with a zero.

## Verified StaticMesh profile

The 38 previously excluded `Engine.StaticMesh` exports in the phase-368
`MC2Game.xxx` use package version 446, licensee version 25, big-endian fields,
and `InternalVersion = 15`. In serialization order:

1. NetIndex and tagged-property list, including the terminating None FName.
2. Seven-float bounds and BodySetup object reference.
3. Counted KDOP node records of 36 bytes and triangle records of 16 bytes.
4. InternalVersion and counted LOD records.
5. Each LOD has an empty inline raw-triangle bulk header; counted sections of
   seven 32-bit fields; UV-set count, vertex stride/count and vertex array;
   duplicated vertex count; two counted uint16 index arrays; counted 16-byte
   edge records; counted byte face flags.
6. Five fixed 32-bit footer words. The supported, observed profile is exactly
   `[1, 0, 0, 0, 0]`; different values fail rather than being silently ignored.

For the old combined vertex/UV stream, the validated stride is
`32 + 8 * UV-set-count`. Position floats must be finite, both vertex counts
must agree, and every index must remain within the vertex array. The parser
requires the final footer to end at the export's exact serial size. The five
footer words' individual names remain unknown, but their fixed numeric storage
and exact supported values are retained explicitly.

No native FString field exists in this supported InternalVersion15 geometry
profile. Tagged StrProperty values, if supplied in another matching export,
are parsed and returned rather than silently discarded.

## Verified Xbox global ShaderCache framing

The selected cache has 86,903 serialized bytes, including its 12-byte object
prefix. Its observed serialization is:

1. Platform byte `2`.
2. Shader-type CRC map: 198 FName/uint32 entries.
3. Vertex-factory CRC map: 20 FName/uint32 entries.
4. 95 shader records. Each has type FName, GUID, absolute end offset, platform
   and frequency bytes, counted compiled-program bytes, duplicate GUID/type,
   instruction count, and a bounded subclass tail.
5. MaterialShaderMap count **zero**.
6. 95 global-map entries, each containing a type FName, shader GUID and duplicate
   type FName. These resolve bijectively to the 95 earlier shader records.

All compiled programs independently agree on:

- `0x102a1101` for the 36 vertex shaders and `0x102a1100` for the 59 pixel shaders;
- header word 1 plus header word 2 equals the counted program size;
- the declared header/body boundaries stay within the program;
- duplicate record GUID/type values match and end offsets land exactly at the
  next record.

This old Xbox layout has **no ParameterMapCRC word** at the position used by
the newer PC comparator. Importing that layout blindly shifts every subsequent
field. The actual duplicated GUID is the positive alignment check.

The empty MaterialShaderMap array proves that its native FriendlyName FString
field is absent here. It does not prove all shader subclass semantics.
Of 95 subclass tails, 11 are empty and **84 contain 1,792 bytes**. Those 84
regions remain explicitly graded **High-confidence deduction**, not Verified.
No phase-366 counted-string candidate intersects them; this intersection check
is reported separately and is not used as their semantic proof.

## Other phase-369 candidate ownership findings

The 443 main-package and two DLC byte candidates were rebound to recipe SHA
`7fc7aca33b52a1f2cbf0c9d70e90181de26aafecd4b2362a49f52f8a9224a0fc`.
Their per-ID evidence is in the active phase-369 audit artifacts:

| Count | Positive ownership evidence |
|---:|---|
| 168 | Complete active Texture2D/ShadowMapTexture2D mip/bulk framing, including the two DLC objects; candidate falls inside an exact pixel/bulk byte span |
| 94 | Complete old Texture2D payload is byte-identical to its original-disc export, current export moved elsewhere; 93 are additionally typed SourceFilePath fields and one is an original mip bulk span |
| 91 | Old relocated SourceFilePath StrProperty headers have exact declared size/type/name and the same field bytes in an original texture export |
| 76 | Counted native numeric arrays: 63 Model candidates and 13 Terrain height/alpha candidates |
| 14 | Terrain blend-weight byte arrays: count equals explicit width × height, Terrain reference resolves to the containing export and Material reference resolves to Engine.TerrainMaterial |
| 2 | Old relocated texture streams reconstructed through all mip headers and exact candidate-containing bulk spans |

For Model, the observed full profile after the property terminator is bounds
(28 bytes), counted vectors/points (12-byte records), nodes (68), self export
reference, surfaces (56), verts (24), shared-side count, zones (24), Polys
reference, leaf-hull/leaf int32 arrays, two uint32 booleans, portal int32 array,
shadow-volume records (16), vertex count and vertex-buffer records (40).
All 63 candidate-containing Model exports end exactly after this profile.

Terrain has a HasStack prefix before its NetIndex/property list. Height and
InfoData counts agree with tagged NumVerticesX × NumVerticesY. Alpha maps are
counted byte arrays. Beyond the material-expression records, each observed
weighted-material entry contains a counted blend plane and ten metadata words;
the first two words are explicit dimensions, the third is the owning Terrain
reference, and the eighth resolves a TerrainMaterial object. The remaining
metadata-word names are not asserted. This establishes the 14 candidate byte
spans without claiming that the whole Terrain native payload is semantically
decoded.

These findings close the enumerated candidates. They are not a claim that all
game artwork, every native class or every possible runtime text route has been
decoded or game-validated. No game resource was changed by this audit.

## Reproduction

Run the synthetic, asset-free tests:

```powershell
python -B -m unittest discover -s tests -p test_ue3_native_coverage.py -v
```

Run the parser against a hash-locked user-supplied/effective package, with a
**new** report destination:

```powershell
python -B -m tools.ue3_native_coverage PACKAGE_FILE --sha256 PACKAGE_SHA256 `
  --class Engine.StaticMesh --class Engine.ShaderCache `
  --output build/native-audit/coverage.json
```

Compressed input additionally needs `--lzx DLL_FILE --lzx-sha256 DLL_SHA256`.
Package identity/profile and DLL identity are checked before loading the DLL.
An existing report, a symlink output or an input/output alias is rejected;
exclusive output creation prevents a late overwrite race. Unknown profiles,
malformed arrays/references, non-empty material shader maps and trailing bytes
fail closed. This command never rewrites the source package.

## Research provenance

Pinned primary-source comparisons and their hashes are preserved in
`references/native-coverage-research.lock.json`:

- [UEViewer UnMesh3.cpp](https://github.com/gildor2/UEViewer/blob/882794d2624ae1db987da986e03b138b5d177787/Unreal/UnrealMesh/UnMesh3.cpp)
- [LegendaryExplorer StaticMesh.cs](https://github.com/ME3Tweaks/LegendaryExplorer/blob/b5e746233491ec5a7cbfc077685996af37a3d125/LegendaryExplorer/LegendaryExplorerCore/Unreal/BinaryConverters/StaticMesh.cs)
- [LegendaryExplorer ShaderCache.cs](https://github.com/ME3Tweaks/LegendaryExplorer/blob/b5e746233491ec5a7cbfc077685996af37a3d125/LegendaryExplorer/LegendaryExplorerCore/Unreal/BinaryConverters/ShaderCache.cs)

The comparator's ShaderCache implementation explicitly skips non-PC caches and
uses opaque per-shader tails. It is a research lead, not Xbox validation. This
repository's read-only parser was independently authored and checked against the
current source-locked bytes; no upstream implementation was copied.
