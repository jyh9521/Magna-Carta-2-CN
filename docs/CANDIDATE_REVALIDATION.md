# Independent moved-tree revalidation — 2026-10-19

## Purpose and proof boundary

**Verified offline:** tools/verify_locale_candidate.py independently verifies a
copied/moved candidate tree against trusted project plans. It never invokes the
candidate producer's build function and never writes inside the input tree.
No original game extraction, upstream font bundle or external raster source font
is needed: the candidate's retained original controls are checked against the
trusted source hashes, not trusted merely because they are called controls.
The optional native decoder is still required for the real compressed payloads.

This validates resource/metadata integrity and deterministic text/TOC replay,
not runtime font selection, fallback/shaping, UI clipping, Chinese display or
whole-game acceptance. No game/emulator/input/configuration/deployment operation
occurs. This is not installation or a game test.

## Trusted inputs, not producer success flags

The verifier reads the explicit candidate plan and exact-hash font/text/glyph
plans from project-root. Resource roles, expected original/candidate hashes,
canonical Font identity, namespace GUID and expected semantic fingerprints come
from those plans. It derives every resource path; producer manifest paths are
only compared to this independently derived contract, never followed as input
instructions. A success boolean or forged package hash cannot replace bytes.

The expected file set is closed. For the current three-alias prototype it is:
three groups of five resources (controls/candidate/rollback-check), two reports,
and manifest.json: **18 regular files**. Missing/extra files, unknown directories,
non-regular descendants, symlinks and Windows junctions are errors. An explicit
selected root may resolve through its own mount/junction; linked descendants
inside the portable tree are rejected. Confined-path resolution also prevents
escaping a declared root.

## Commands (repository root; report outside candidate tree)

Use the trusted original producer manifest hash, not a checksum obtained only
from a suspect copy. The following anchors were retained before relocation:

```powershell
python tools/verify_locale_candidate.py --plan locales/zh-Hans/candidate-disc1.json --candidate-root build/candidate-audit-verification/relocated-disc1 --project-root . --manifest-sha256 598d7b4b57fd48c200dcdd914858c3764308ac8a2db597b7e8b8ee0fb7003df3 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-disc1-revalidation.json
python tools/verify_locale_candidate.py --plan locales/zh-Hans/candidate-disc2.json --candidate-root build/candidate-audit-verification/relocated-disc2 --project-root . --manifest-sha256 3102a86b03279357af684b3ae38c9dd75c71adcb00c2cccf390a33eb4f4cac73 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-disc2-revalidation.json
```

Replace roots with your copied/moved trees and use a fresh report filename.
To rebuild a candidate from a clean checkout and user-supplied originals, see
LOCALE_CANDIDATE.md. Revalidation itself uses only the tree and trusted plans;
it does not reconstruct missing files or silently choose another disc.

--manifest-sha256 is optional. With it, exact raw manifest bytes must match the
trusted anchor before asset parsing. Without it, resources must still match the
trusted plans and all replayed metadata contracts, but **the original producer
manifest's exact byte identity is not proven**. The report records its actual
hash and trusted_manifest_sha256_verified=false. This distinction is not hidden.

Producer additional_input_hashes are validated declarations, not fresh reads of
historical external inputs. They may refer to a decoder or raw plan no longer
at its old location. The report explicitly keeps
producer_additional_inputs_reopened=false and
raster_source_font_file_reopened=false. Without a trusted manifest anchor,
well-formed edits to these non-replayed provenance declarations cannot be
identified as edits to the original manifest. The actual verifier plan/decoder
snapshots are separately rehashed and listed as verifier_additional_input_hashes.

## Independent checks

1. Validate plan schema, exact dependency bytes, complete Font label set and
   text/Font/TOC resource separation. Fail on unsupported versions or aliases.
2. Require the closed portable member set, then check every original, candidate
   and restored file against hashes derived from trusted plans. Restored bytes
   must equal original controls in full, not only in changed fields.
3. Reparse all original/new Font packages, canonical identities and complete
   glyph/remap/decoded-atlas fingerprints. No producer Font report is proof.
4. Resolve source-hash text edits from checked controls; independently rebuild
   text, verify exact candidate bytes and full reverse reconstruction, preserve
   source/ID/token/encoding invariants, and audit literals in every supplied Font.
5. Recompute TOC first-size changes from actual Font/text lengths, compare the
   complete candidate TOC bytes and reverse the changes to the complete original.
6. Compare both reports with independently computed values. Reconstruct the
   schema1 manifest contract from actual checked bytes and trusted plans.
   Strict canonical JSON comparison distinguishes False from0, 1 from1.0,
   rejects duplicate keys/NaN and unknown fields, and retains deliberate list order.
7. Rehash all observed members and project/CLI dependencies and recheck tree
   membership. After the external report is written/reopened, the CLI rechecks
   members and dependencies again. An error exit never validates a report.

The verifier reuses the existing bounded parsers/semantic/text primitives but
not the assembly function or its success flags. It writes only a new external
metadata report. Exit0 means these offline checks passed; exit2 means failure.
No fallback, repair, deletion, renaming or installation is performed.

## Real relocation and adversarial evidence

Both real disc trees were copied to different directories. All18 source/copy
file hashes matched before verification and remained unchanged afterward.
Each independent replay verified5 resources/18 members using the retained trusted
manifest anchor. The old game extraction and old font-bundle paths were not
arguments or dependencies of revalidation.

The following controls were exercised on a separate generated copy, never a game
installation or the validated original candidate:

| Negative control | Observed failure | Exit |
|---|---|---:|
| Corrupt Font + forged corresponding manifest hash, no anchor | Trusted candidate byte hash mismatch | 2 |
| Forge glyph-pixel success + recompute declared report hash, no anchor | Independent report replay mismatch | 2 |
| Add an unapproved file | Closed member-set mismatch | 2 |
| Select D2 plan against D1 tree, no anchor | Original-control TOC hash mismatch | 2 |
| Move a generated payload to a checked sibling and link it back by Windows junction | Linked descendant rejected | 2 |

The first four negative invocations left their deliberately arranged input bytes
unchanged; they did not repair or remove the failing inputs. The junction test
only moved a directory within the isolated generated evidence root, with both
absolute paths checked before moving. No original game directory was moved.
Exact commands, outputs and resource hashes remain local under
build/candidate-audit-verification/.

Baseline367 -> modified381 -> independent source rollback367; native-enabled381.
Fourteen new self-authored tests cover relocation with only trusted JSONs,
non-invocation of the producer, manifest anchors, forged payload/report metadata,
closed membership, strict typed flags/unique JSON keys, declared path/size/duplicate attacks,
explicitly unproven producer provenance, links/confinement, dependency changes,
late member mutation, CLI output confinement and report-readback faults.
Default CI needs neither original resources, raster dependencies nor a native
DLL. Current positive reports still set runtime/rendering/deployment=false.

## Next research gate

Packaging and relocated-tree integrity do not settle the remaining UI/native
questions. Continue the existing serialized/native-default and linker/font-
selection investigation in FONT_BINDING_AUDIT.md/UI_STYLE_GRAPH.md, while keeping
all actual game acceptance with the user and avoiding bulk dialogue translation.
