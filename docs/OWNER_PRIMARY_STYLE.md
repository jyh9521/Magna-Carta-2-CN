# Label PrimaryStyle and nested text defaults — 2026-10-19

## Evidence boundary

**Verified offline:** serialized fields, explicit archetype chains, flag/class-
selected CDO candidates, state maps, Font payloads and decoded-atlas fingerprints.
No game, emulator, native function or target instruction was executed. All
game testing remains user-operated; no resource was deployed or configured.

**Unverified:** native getter entry+0x28 is the matched label, its alternate
source+0x174 is this PrimaryStyle, which virtual-result branch executes, runtime
default merging, skin/state selection, object loading precedence and rendering.
The native source coordinates documented in NATIVE_STYLE_SELECTION.md do not
establish any of those serialized-to-native identities.

## Why this is a distinct branch of the investigation

The original component trace remains unchanged: both LogIn_NewGame labels have
StringRenderComponent -> StringStyle.AssignedStyleID -> GeneralFont -> six
states -> nested TextStyle -> Font.General_15. These twelve paths are serialized
candidates, not a proof that General_15 is the effective drawing font.

The label itself has no serialized PrimaryStyle field. Absence is not a null
value, a zeroed native structure or evidence that the component branch wins.
The new audit keeps the label's explicit archetype plane and its class-default
plane separate, and preserves every observed selector without merging fields.

## Original-source findings

Both TitleMap_MSPT exports 1151 and 1164 are MC2Game.MC2UILabel. Each has a
four-byte NetIndex prefix and a null explicit archetype. Their independent
class-default candidate chain is:

| Package | Export | Object | PrimaryStyle observation |
|---|---:|---|---|
| MC2Game | 32492 | Default__MC2UILabel | absent |
| Engine | 19433 | Default__UILabel | RequiredStyleClass -> export20223 UIStyle_Combo |
| Engine | 6217 | Default__UIObject | DefaultStyleTag=DefaultComboStyle, FName number0 |
| Engine | 6063 | Default__UIScreenObject | absent |
| Engine | 5510 | Default__UIRoot | absent |
| Core | 2 | Default__Object | absent |

Engine export6217 also explicitly serializes zero AssignedStyleID, null
RequiredStyleClass and null ResolvedStyle. These belong to that source object;
they are **not** merged with Default__UILabel or assigned to either live label.
Relevant logical offsets: DefaultStyleTag2451267, AssignedStyleID2451335,
ResolvedStyle2451479, and Default__UILabel.RequiredStyleClass3674820.

DefaultComboStyle's tag matches one supplied UIStyle: Startup_int export1675,
DefaultUISkin.DefaultSkin.DefaultComboStyle. Its six state mappings each lead
through a UIStyle_Combo.TextStyle.CustomStyleData to a UIStyle_Text object
(exports1680,1684,1682,1679,1677,1688 in state-map order). None has its own
StyleFont field, and all have null explicit archetypes. Their separate CDO
plane reaches Engine.Default__UIStyle_Text, which explicitly references
Engine export21326, EngineFonts.SmallFont, at logical offset3735073.

The report therefore adds **twelve class-default Font observations** (six per
label), independently of the original twelve General_15 component paths. It
does not substitute these values into either label or choose a fallback.
The original 1209/1209 selected UI parses, two exact text matches, zero selected
UI parse errors and seven separately retained classification gaps are unchanged.

### Namespace candidates

| Canonical identity | Supplied candidates | Glyphs/remap entries | Complete semantic SHA256 |
|---|---|---|---|
| enginefonts.smallfont | Engine21326, Startup_int18 | 256 / 0 | 289ea3f9da29f70ae727b7ff886f003a7b87f3d9fa65d67618b9119ec22edf68 |
| font.general_15 | MC2Game34612, Startup_int21, font2 | 2608 / 2608 | f06656fc2f1364b438a924eb8115be604d45c307be4707b59692488590a05e0a |

Each group's supplied candidates share a known namespace GUID and identical
complete normalized glyph/remap/decoded-atlas data. The two groups are distinct;
matching data within a group does not resolve which physical instance loads.
SmallFont is a newly retained **default-plane candidate**, not a newly proven
active warning font. Existing General_15 diagnostic plans are not silently
expanded, and neither font is changed by this read-only audit.

## Reproduction and report contract

Use the existing hash-locked deep graph command in UI_STYLE_GRAPH.md with
`--audit-bindings`, adding Core as documented in FONT_BINDING_AUDIT.md.
The same command and inputs work; only the new output path must be fresh.
No new dependency or proprietary asset enters Git.

`tools/owner_style_audit.py` is locale-neutral. Each text match now contains
`owner_primary_style_audit` with:

- the complete label `prototype_audit`, including observed field absence;
- separate `selector_observations` for every explicit AssignedStyleID and
  DefaultStyleTag across both planes;
- all supplied matching UIStyle definitions, including ambiguous matches;
- per-state nested text-data prototype audits and `font_source_plane` /
  `font_source_owner` on each Font observation;
- independent unresolved/catalog errors, without treating null/missing fields
  as success or synthesizing inheritance;
- false `inherited_values_merged`, `fallback_order_verified`,
  `native_owner_pointer_identity_verified` and `runtime_binding_verified`.

FName matching folds name case but preserves its numeric suffix. Zero STYLE_ID
and FName None/0 remain explicit observations, not catalog lookup requests.
Indexed/duplicate or wrong-typed selector fields fail that observation. Null
font references, unresolved prototypes and unsupported inherited/source-style
data remain diagnostic errors; a CDO Font is never silently substituted.

`font_namespace_audit` includes all Font observations from both routes. Existing
top-level `candidate_paths` and CLI candidate count still refer only to the
component's direct serialized route; count label observations separately.

Sixteen new self-authored tests cover absent/zero fields, indexed/duplicate
guards, exact FName number matching, ambiguous styles, distinct instance/CDO
fonts, explicit null handling, nested combo/state failures and CLI readback.
Full default suite: 573 tests, OK (skipped=1); the optional LZX case requires
the explicit verified decoder. This remains offline evidence only.

## Next investigation

Corroborate the native alternate-owner pointer and its style offset against
class/property evidence before connecting it to this serialized route. Keep
both sources and all namespace instances visible. No SmallFont patch or bulk
translation follows merely from the newly discovered CDO reference.
