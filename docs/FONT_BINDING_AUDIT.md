# Font binding audit and all-alias controls — 2026-10-19

## Findings and limits

**Verified offline:** the warning's three serialized General_15 copies are not
three different canonical names. Their cooked/standalone representations share
**Font.General_15**, namespace GUID **48dc8cf544327a628eab7dad23b9607d** and an
identical normalized glyph/remap/atlas fingerprint. Package-local export indices
still differ. These facts establish serialized namespace candidates, **not**
which copy wins or whether the game coalesces them into one loaded object.

The game is never launched or deployed by these tools. User configuration,
original resources and ISO files remain untouched. Raw-package compatibility,
visible geometry change, recovery and Chinese display remain user-run gates.

## Prototype and class-default planes

`inspect_ui_fonts.py --deep --audit-bindings` now audits both planes separately:

| Plane | Exact serialized chain |
|---|---|
| Warning renderer prototypes | TitleMap exports2191/2204 -> MC2Game export32829 Default__MC2UILabel.LabelStringRenderer -> Engine export21510 Default__UILabel.LabelStringRenderer -> null archetype |
| Class-default candidates | Engine export15602 Default__UIComp_DrawString -> export15479 Default__UIComp_DrawComponents -> export6065 Default__UIComponent -> Core export4 Default__Component -> Core export2 Default__Object -> null archetype |

Class defaults are located using the defining Class index and HO flag0x200,
not a `Default__` name guess. The defining package must have exactly one CDO
candidate to avoid ambiguity; all candidates and errors are retained otherwise.
Prototype class compatibility, cycles and bounds are checked. Null archetype or
missing fields **do not mean zero/false values**. The Core CDO tail is now
resolved from the original hash-locked Core.xxx, not inferred.
The only explicit warning customization observed is alignment; no serialized
DrawFont override appears in these inspected prototype/CDO nodes. Native default
initialization and effective inherited overrides remain unverified.

## Cooked namespace identity

Raw export flag bit1 matches EF_ForcedExport. For a forced Font export, the
outermost exported Package supplies the uncooked namespace and GUID. A regular
standalone Font uses its package label and summary GUID. Cycles, imported outers,
missing/wrong-class Package roots and malformed GUID metadata fail explicitly.
This produces candidate identities; the resolver does not pick runtime precedence.

Format references: Konstantin Nosov's MIT UEViewer commit
`a0bfb468d42be831b126632fd8a0ae6b3614f981`,
[GetUncookedPackageName](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealPackage/UnPackage.cpp),
[EF_ForcedExport](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealPackage/UnPackage.h).
Fixed file SHA256 values are in references/font-namespace-research.lock.json.
Unreal-Library's already locked ExportFlags enum independently declares bit1.
The Python identity implementation is independent and is not a reimplementation
of the game's object loader.

| Physical source | Font export | Serialized path | Namespace GUID source |
|---|---:|---|---|
| font.xxx | 2 | General_15 | package summary |
| MC2Game.xxx | 34612 | Font.General_15 | exported Package Font, export45279 |
| Startup_int.xxx | 21 | Font.General_15 | exported Package Font, export1955 |

The two cooked Package roots have the same GUID and net-object counts [19].
All three Font payload byte hashes differ because table-local property/object
indices differ. Full Font parsing validates tagged/native agreement and complete
consumption. Normalization preserves all 2608 glyph metrics, 2608 remap entries,
IsRemapped and the ordered dimensions/full decoded tiled-byte hashes of six
atlases. NetIndex, property-name indices, object indices, bulk offsets/headers
and compression representation are excluded explicitly.

All three normalized fingerprints equal:
`f06656fc2f1364b438a924eb8115be604d45c307be4707b59692488590a05e0a`.
Fingerprints include atlas padding, so equality is conservative; they are not a
GPU rendering observation. Unknown formats or unavailable decoders produce errors,
not guessed equality. Reports emit hashes/counts, not original glyph tables/images.

## Both-disc inventory, beyond the previous 62 requested packages

`inventory_font_namespaces.py` validates each disc descriptor and full directory
against the retained hashed inventory, then verifies every .xxx member's SHA256
before decoding **only the logical header**. Shared packages reuse header results
only after the second resource hash also passes. It never extracts or executes
package payloads and does not equate table validation with Font validity.

| Disc | Package hashes verified / tables parsed | Font/MultiFont class candidates | General_15 namespace matches |
|---|---:|---:|---:|
| D1 | 1912 / 1912 | 55 | 3 |
| D2 | 2233 / 2233 | 55 | 3 |
| Total | **4145 / 4145** | **110** | **6** |

No header or Font-identity errors occurred; D2 reused 1594 identical header
results. The six matches are exactly the three paths above on each disc. Their
three resource SHA256 values match across discs. Thus no additional exact
Font/MultiFont-class General_15 candidate was found in either original disc's
.xxx tables. This does not cover runtime-created Fonts, custom subclasses,
DLC/updates or other resource formats. Other Font payloads are not validated by
this class inventory. Whole ISO SHA256 was **not** rehashed in this scan; the
manifest's historical full-image digest is labelled expected, not verified.

```powershell
python tools/inventory_font_namespaces.py --disc "MagnaCarta II (Korea) (Disc 1).iso" build/disc1-hashed.json --disc "MagnaCarta II (Korea) (Disc 2).iso" build/disc2-hashed.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --canonical-path font.general_15 --output build/NEW-two-disc-font-inventory.json
```

Add `--audit-bindings` and the hash-locked standalone reference to the existing
warning graph command in UI_STYLE_GRAPH.md:
`--reference-package font build/poc-game/disc1/MC2Game/CookedXenon/font.xxx b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6`.
Legacy/default deep reports are unchanged when the audit switch is absent.

## Reproducible all-planned-alias geometry packet (undeployed)

`build_font_binding_probe.py` locks canonical path, GUID, normalized baseline,
all three source hashes, old mapping and donor index. Compressed sources first
produce validated raw controls. It changes U+B85C glyph959 to existing glyph65
geometry in **both tagged/native copies in all three aliases**. Remap, atlas
bytes and every unrelated export remain original. It creates controls,
candidates, independent file-backed inverse checks, reports and a shared TOC.
No outputs publish until all inputs/variants have validated. Output directories
must be new and outside the source tree. Every output is reopened; original
source hashes are rechecked. No game copy is patched in place.

```powershell
python tools/build_font_binding_probe.py --plan references/probes/login-font-geometry.json --game-root build/poc-game/disc1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW-all-alias-geometry
```

The D2 plan references the same three font source hashes but its own original
TOC hash. With a separately extracted D2 root, use
references/probes/login-font-geometry-disc2.json. This is localization resource
preparation, **not** ISO merging or disc-switch acceptance.

| Candidate filename | Bytes | SHA256 (identical on both discs) |
|---|---:|---|
| font.xxx | 1343488 | 725236937cefd2b3fd445f92a70c70b6d5d2ee693904171c7066e6dbc12cea45 |
| mc2game.xxx | 58032128 | 15911b07764cfffbfdc0374357e5dd6a22b34ac50fee37b6a5088311162ecd6b |
| startup_int.xxx | 12845056 | ab7d95eb1e861312d09fa93685c090cb401a4f68a89da36cba0d17f9de6cbd21 |

All three changed fingerprints equal
`4afa570959be3f570e68361b7c5b697dafd00d570e275c98335e4d00dc209e17`,
and differ from the original. All six independent inverse files (three per disc)
reproduce their complete raw control bytes. Candidate lengths equal raw controls.

TOC updates affect only first sizes: MC2Game 11632640 -> 58032128 and Startup_int
1769472 -> 12845056. Paths/sectors/other columns/CRLF stay unchanged; inverse TOC
is byte-identical. D1 TOC output SHA256
`d36ec07fae9045a05264e9c632437cef783c7d9f470096b3e6615bb361b47301`;
D2 `f49e95873ababd9605f6ed9fe16ca21f3ff21a10404a4d2b90e0b8c1f7e5bb30`.
The packets keep the original text and do not add Chinese glyphs. Do not combine
this diagnostic with the earlier StyleFont 21->20 probe and call the result an
isolated test. Raw compatibility/visible change/original recovery remain untested.

Local evidence: build/style-inheritance-verification/{binding-audit-final.json,
two-disc-font-namespaces.json,all-alias-geometry-v2/manifest.json,
all-alias-geometry-disc2/manifest.json}. No full game resource enters Git.

Validation checkpoint: baseline 293 tests passed (one optional native skip).
26 new synthetic tests cover prototype/CDO separation, namespace/GUID guards,
full atlas/metrics fingerprints, raw/compressed equivalence, all-alias candidate
and inverse construction, both version plans, output readback failures, and
hash-locked XDVDFS/header-only inventories. Modified 319 tests passed (one skip),
and all 319 passed with the explicitly selected native decoder. None run game
code. Source rollback is checked separately against the 293-test baseline.

## Core ancestry closure and nested scalar follow-up

Core.xxx is a 32768-byte original package, SHA256
`1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815`.
Supply it alongside the earlier five packages:

```powershell
# Add to the --deep --audit-bindings command; choose a new output file each run.
--reference-package Core build/poc-game/disc1/MC2Game/CookedXenon/Core.xxx 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815
```

The reader previously stopped class ancestry at Core.Component, a useful
unsupplied-Core boundary. This incorrectly rejected Component's legitimate
Object CDO archetype when Core was supplied. With Core present it now follows
the real super link to Core.Object; missing/cyclic/non-Class definitions fail
rather than silently using the old boundary. Without Core, existing behavior
is retained. Both warning renderer CDO audits terminate at null archetype with
no unresolved audit entries. Their explicit renderer prototype chains remain
separate and unchanged. This closes the serialized CDO tail, not native defaults
or effective/runtime values.

Nested IntProperty values now retain signed i32 values. ByteProperty values are
reported as either exact u8 or checked eight-byte FName, with value_encoding;
other lengths fail rather than guessing. Static array indices stay explicit.
Both warning TextStyleCustomization.TextAlignment[0] and [1] serialize u8 **1**;
bOverrideAlignment is **1**. Enum meaning is not inferred from this number.
No serialized DrawFont override appears along either complete inspected chain.

The final graph still has 1209 parsed UI exports (480 at offset4; 729 at8),
two matches and twelve state paths. Seven non-UI classification errors
(Level/Model/Polys/ShaderCache/World imports missing from supplied Engine)
remain reported, not counted as successfully classified objects. All three
Font candidates retain their original full semantic fingerprint.

Eight new synthetic regression tests cover Core closure/compatibility, optional
boundary preservation, broken/cyclic/non-Class Core, exact signed/byte/named-enum
values and sizes, and FName bounds. Baseline319 -> modified327 -> independent
source rollback319; native-enabled327. Evidence remains local under
build/core-style-verification/, including binding-audit-core-final.json.

## Two-glyph candidate coverage across all three aliases

The existing locale prototype plan (only U+8E22 and U+51FB, not bulk translation)
now also rebuilds original MC2Game.xxx with supplement_font.py. The Noto font
source, glyph placements and source/package hashes remain locked as documented
in FONT_RESEARCH.md and references/font-sources.lock.json. This candidate uses
append-only compressed-package storage, not the raw geometry-control packet.

| Candidate | Bytes | SHA256 |
|---|---:|---|
| font | 1842707 | 91dd68f7a2048d7f3a71b3af56f7e6dae326744c6f37e9f136e4528f5fec51be |
| mc2game | 18254735 | 0614f916c20e1166fb21517037cfa431cf6a570fedb0eb4a825412def151cc23 |
| startup_int | 2993190 | a95821ee7a5cf41d92f4cc92d436dc1cf1bd104106a014ba42c7894358067d75 |

All three independently decoded candidates have 2610 glyphs/remap entries and
the same full normalized fingerprint:
`3e720fef59fc0a0e1a545555a517369e1d55c68f32ec019f2c143e45658d87f7`.
MC2Game preserves 83390 unaffected exports, 52 original compressed chunks and
3241 trailing bytes. Its original 2608 tagged/native/remap records remain;
72 previously unused BC3 blocks change, maximum glyph height stays23, and all
original glyph pixels/other blocks/padding stay identical. Rasterization quality
and in-game use remain unverified. The original resources were rehashed afterward.

Font-only TOC copies use all three new physical lengths, including MC2Game's
11632640 -> 18254735. Each disc uses its own hash-locked original TOC, and the
independent inverse first-size updates reproduce that original byte-for-byte.
Neither TOC changes Coalesced or any text resource; do not substitute these for
the earlier text+two-font experiment or combine them with geometry diagnostics.

- D1 font-only TOC SHA256 `575535af22d1f0b44da8e3b9f0331d3302787b4a0b0a4c1af6f6fae448153b00`.
- D2 font-only TOC SHA256 `598849c89c1dd38f3f5d6fd326f881f8f7f69dafc3a51817b3fe7469db89ba10`.

Local evidence: build/all-alias-supplement-verification/{MC2Game-report.json,
cross-alias-validation.json}. The existing font/Startup candidates are hash-
checked against their own reports, not assumed compatible from filenames.
Only metadata and rebuilding instructions enter Git; no candidate is deployed.
The reusable multi-alias supplement assembly/validation entrypoint is now
implemented with version/identity/semantic guards; see FONT_BUNDLE_BUILD.md.
It rebuilds both discs without deployment or game launch.
