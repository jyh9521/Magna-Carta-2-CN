# Offline locale candidate assembly — 2026-10-19

## Status and purpose

**Verified offline:** tools/build_locale_candidate.py assembles the original-
path-shaped Font/text/TOC dependency set into a new directory, with original
controls, guarded backup-restoration copies and independently computed reports.
The current versioned locale plans contain only the existing two-glyph/one-entry
technical prototype. This is not an installer, release patch, ISO merge or proof
of Chinese display. No XEX, emulator, game input, configuration or deployment
operation is involved. All game acceptance remains with the user.

The assembler consumes the reproducible font bundle from FONT_BUNDLE_BUILD.md
and the source-hash text plan from TEXT_FONT_COVERAGE.md. It does not re-rasterize
or re-read the external Noto font file. Its expected source-font hash is recorded
as an expectation with source_font_file_rechecked=false, not a fresh source-font
verification claim. Instead, every supplied candidate package must match its
locked complete binary SHA256 and full expected font semantic fingerprint.

## Inputs from a clean checkout

- Explicit original resource root containing exactly the needed resources (a
  larger original extraction is also readable). No executable is required:

```text
MC2Game/CookedXenon/font.xxx
MC2Game/CookedXenon/MC2Game.xxx
MC2Game/CookedXenon/Startup_int.xxx
MC2Game/Localization/Coalesced.int
MC2Game/Xbox360TOC.txt
```

- A freshly built font bundle for the same disc, or equivalent byte-identical
  candidate payloads matching the checked-in plan. See FONT_BUNDLE_BUILD.md for
  original extraction, source font, pinned dependencies and decoder build.
- locales/zh-Hans/candidate-disc1.json or candidate-disc2.json; each references
  exact bytes of its font-build and text-probe plans. The referenced glyph plan
  is also read from project-root and hash checked.
- Explicit LZX decoder for these compressed originals/candidates. Raw synthetic
  tests use only the self-authored stored-block decoder, not a DLL.

For a minimal D2 extraction, use disc_inventory.py with a new inventory/output
root and repeat --extract for the above five paths. This is not resource merging:
all five inputs come from that disc, and full resource hashes are rechecked.
The two Font sets and text happen to match across discs; the TOC does not.

## Commands (repository root; choose fresh output roots)

After the font bundle build, run:

```powershell
python tools/build_locale_candidate.py --plan locales/zh-Hans/candidate-disc1.json --game-root build/poc-game/disc1 --project-root . --font-bundle build/font-bundle-verification/disc1 --output-dir build/NEW-disc1-candidate --lzx-library build/lzx/native-verified/ue3_lzx.dll
python tools/build_locale_candidate.py --plan locales/zh-Hans/candidate-disc2.json --game-root build/locale-candidate-verification/disc2-inputs --project-root . --font-bundle build/font-bundle-verification/disc2 --output-dir build/NEW-disc2-candidate --lzx-library build/lzx/native-verified/ue3_lzx.dll
```

Paths above refer to local original extractions and the documented font builder
outputs, not private pre-edited files. Replace them with your own equivalent
freshly generated roots. --game-root and --font-bundle are read-only inputs,
never destinations. Output must be new and outside both input roots. An error
returns2; no original is changed. Publication failures may leave an incomplete
new directory, and an error exit never validates a manifest. Retry with a new
output directory, not by overwriting the failed one.

## What is verified before publication

1. Candidate schema1, offline kind and game_rendering_verified=false; confined
   paths, exact reference hashes and complete non-duplicate candidate label set.
2. Original Font package profiles/hashes, canonical identity and namespace GUID,
   original semantic fingerprint, exact candidate binary hashes and complete
   supplemented semantic fingerprints. Every planned alias is mandatory.
3. Original text hash/resource/ID/source-value hash, protected token order,
   encoding/re-extraction and full inverse text rebuild. Every supplied Font
   must cover all translated literals under the explicit-remap audit's scope.
4. Expected complete rebuilt text hash, not merely a filename or byte count.
5. Original disc-specific TOC hash and expected original first-size fields.
   Changes cover every actual size delta among Font and text resources. No-op
   size entries are omitted. The resulting complete TOC hash must match the plan,
   and inverse first-size updates must reproduce the entire original TOC.
6. All dependency bytes are rehashed before and after publication. Resource
   controls/candidates/restored copies and reports are reopened; resources are
   rehashed again after reports are written. The CLI also snapshots/rechecks its
   raw candidate plan and decoder, recording their names/full hashes.

An upstream font-bundle manifest is intentionally not trusted or needed. The
assembler derives candidates/<validated-label>.xxx paths, checks actual bytes,
and independently parses payloads. Fake success booleans or an omitted source
list cannot substitute for missing/corrupt packages. It does not automatically
rediscover all Font aliases; completeness comes from the versioned research
plans and separately verified whole-disc inventory.

## Output tree and portable metadata

```text
candidate/<original resource path>      3 Font packages + text + TOC
controls/<original resource path>       original physical resource bytes
rollback-check/<original resource path> guarded restored candidate copies
reports/font-validation.json            full original/new font fingerprints
reports/text-font-coverage.json         source/inverse/literal coverage evidence
manifest.json                          emitted last; relative payload/report paths
```

There are five resources in each tree and eighteen files total. These are not
complete game directories and contain no executable/configuration. Do not treat
the tree as a bootable game or copy it into an installation automatically.
Manifest paths are relative slash-separated paths, not machine-specific build
locations. Reports contain hashes/structural identities, not full source text
or glyph tables. Metadata carries runtime/rendering/deployment=false explicitly.
The source-font hash expectation is not falsely presented as a re-read font file.

Restoration is a real new candidate-copy -> hash preflight -> retained original
backup replacement -> full byte comparison. It proves isolated backup recovery,
not compressed-original reconstruction without backups or in-game rollback.
Text and TOC additionally pass reverse-edit/size logic against original bytes.
No complete original or generated resource enters Git; all outputs stay under
ignored build/. Source/tests/locale plans/documentation remain reusable.

## Candidate plan schema1

Required fields: kind=offline-locale-candidate, game_rendering_verified=false,
font_plan(path/sha256), text_plan(path/sha256), text_resource, font_candidates
(label/sha256 for every font plan source), expected_text_sha256 and
expected_toc_sha256. The project-root confines referenced JSON. The original
resource hashes/canonical identity and expected semantic fingerprints remain in
the referenced font plan; the original text hash/ID/source hash remains in its
text plan. Text cannot alias a Font or TOC path. Unknown/missing/duplicate source
labels and wrong hashes fail rather than selecting a subset or another disc.
Shared read_locked_json lives in font_binding_plan.py and rejects escaping
references, hash mismatches and non-object JSON payloads.

## Real reproduction and negative controls

Both disc builds produce five validated resources with ten total byte-identical
original backup restorations. Both text candidates retain the earlier complete
SHA256 and all Font candidates retain their individually verified hashes; no
new glyphs or translation rows are added. The text remains equal-length, so the
real TOCs change only the three Font first-size fields. A self-authored variable-
length text fixture proves the text size is also updated when it changes.

D1 was assembled twice in different output directories: all eighteen file
contents, including both reports and manifest, have identical SHA256 values.
This checks repeatability on the tested platform with the same dependencies;
it is not a claim about timestamps/ACLs or an untested cross-platform archive.
D1 final manifest SHA256
`598d7b4b57fd48c200dcdd914858c3764308ac8a2db597b7e8b8ee0fb7003df3`;
D2 `3102a86b03279357af684b3ae38c9dd75c71adcb00c2cccf390a33eb4f4cac73`.

Using the D2 plan against D1 originals fails its TOC source hash before output
creation. Supplying a corrupted Font copy plus a fake success manifest fails
the actual candidate hash, also before output creation. Negative commands,
full output hashes/restoration checks and repeat proof are local under
build/locale-candidate-verification/. Neither test touches deployed resources.

Baseline355 -> modified367 -> independent source rollback355; native-enabled367.
Twelve new synthetic tests cover reference/object/hash guards, all-alias input
requirements, ignored fake manifests, original version/TOC conflicts, missing
literals/tokens, output confinement/readback, late input/output mutation,
variable text sizes, portable repeatability, CLI and both locked disc plans.
No native decoder, source font/raster dependency or game is needed by default.

A valid candidate assembly is still not a display/binding/whole-game acceptance
result. The next offline step is independent revalidation of a moved/copied tree
against its trusted plans; the user's game tests remain untouched.
