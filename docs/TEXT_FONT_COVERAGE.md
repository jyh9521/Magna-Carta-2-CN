# Source-locked text edits and literal Font coverage — 2026-10-19

## Scope

**Verified offline:** tools/audit_text_font_coverage.py validates a Coalesced
edit plan against original bytes, rebuilds/re-extracts it in memory, constructs
an inverse edit plan and requires full original-byte equality. It then checks
all supplied Font objects for the literal translated Unicode codepoints.
It writes only a new metadata report; build_coalesced.py separately writes an
isolated text candidate when explicitly requested. Neither tool installs files,
launches a game, edits configuration or changes original resources.

The audit does not select an active UI font. The three supplied General_15
aliases are serialized namespace candidates, not a runtime binding assertion.
The technical [ButtonA] Kick edit is not one of the LogIn_NewGame warning
widgets; their known static style chain does not prove Kick uses that font.
Chinese display, UI layout, runtime fallback and font selection remain user-run
verification gates. No bulk dialogue translation is introduced here.

## Versioned source-hash edit plan

locales/zh-Hans/text-probe.json contains only one technical display edit. It
records original container SHA256, stable entry ID, exact source-value SHA256,
target literal and technical-prototype/unverified status. It does not contain
original source text. Both retained original disc inventories give the same
Coalesced.int SHA256, but each input is checked independently.

build_coalesced.py schema1 now supports two explicit source verification modes:

- Omitted source_mode or literal: existing entries carry id/source/translation.
- sha256-utf8: entries carry id/source_sha256/translation; source is forbidden.

The second mode hashes the **exact extracted source value encoded as UTF-8**,
not its original UTF-16 byte range. No trimming, normalization, case conversion
or token removal occurs before hashing. The whole-container hash independently
locks the original serialized bytes. The original value is resolved only after
container hash, resource identity, stable ID and source hash agree. Duplicate
or unknown IDs, mixed source fields, invalid hashes and unsupported modes fail;
there is no guessed or empty-source fallback. Boolean/floating schema versions
are rejected instead of accepting Python's True==1 behavior.

After resolution, the existing exact source/token/encoding/re-extraction checks
remain mandatory. Plans and inputs are not mutated. No-op rebuilds retain the
existing byte-identical behavior. Source-hash plans work with both the ordinary
text builder and the read-only coverage auditor.

## Clean-checkout workflow

Supply the original four Font/TOC resources as in FONT_BUNDLE_BUILD.md, plus
MC2Game/Localization/Coalesced.int from the selected disc. Build the Font
bundle first. No private pre-generated changes plan is needed: the checked-in
text-probe manifest is sufficient with the original resource.

The example below uses the verified D1 bundle output. Replace its directory
with your newly built bundle; do not copy resources into an installation.

```powershell
python tools/audit_text_font_coverage.py build/poc-game/disc1/MC2Game/Localization/Coalesced.int locales/zh-Hans/text-probe.json --font-package font build/font-bundle-verification/disc1/candidates/font.xxx 91dd68f7a2048d7f3a71b3af56f7e6dae326744c6f37e9f136e4528f5fec51be General_15 --font-package MC2Game build/font-bundle-verification/disc1/candidates/mc2game.xxx 0614f916c20e1166fb21517037cfa431cf6a570fedb0eb4a825412def151cc23 Font.General_15 --font-package Startup_int build/font-bundle-verification/disc1/candidates/startup_int.xxx a95821ee7a5cf41d92f4cc92d436dc1cf1bd104106a014ba42c7894358067d75 Font.General_15 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-text-font-coverage.json
python tools/build_coalesced.py build/poc-game/disc1/MC2Game/Localization/Coalesced.int locales/zh-Hans/text-probe.json --output build/NEW-Coalesced.int
```

D2 uses its own original text extraction and D2 bundle paths. The versioned text
plan and three candidate Font hashes match both discs; the Font bundles' TOCs
remain distinct. Hash mismatch aborts rather than borrowing D1 data silently.
Fresh extraction uses the existing disc_inventory.py with an explicit
--extract MC2Game/Localization/Coalesced.int and a new extraction directory.
Original source font/raster/decoder requirements remain in FONT_BUNDLE_BUILD.md.

## Report and failure contract

- Source container/profile, stable entry ID, exact original source and protected
  TOKEN sequence are validated through build_coalesced. A reverse plan must
  reproduce every original container byte, not only the edited field.
- Every --font-package binds label, path, complete SHA256 and exact Font object.
  Expected class is Engine.Font. Missing, duplicate, malformed or unsupported
  objects do not disappear from a successful subset. All supplied fonts must
  cover the requested literals; no loaded-object winner is chosen.
- Codepoints come from translated literal spans outside exact matches of the
  repository's existing TOKEN regex. Recognized placeholders/markup/control
  tokens keep their exact source sequence, but their dynamic contents are not
  expanded or checked. Unknown syntax is not broadly stripped.
- Only explicit BMP remap data is supported. No-remap fonts, non-BMP scalars,
  control/format literals, missing mappings and zero-area non-whitespace glyphs
  produce uncovered statuses. An explicitly mapped whitespace glyph may have
  zero area. Neither glyph0 nor any other glyph is guessed to be .notdef.
- Metric/remap agreement and texture-index bounds are checked by the Font
  parser. This audit does **not** validate atlas rectangles, actual glyph pixels,
  shaping, fallback, clipping, dynamic text expansion or UI/runtime font choice.
  These limits remain explicit false fields in each report.
- Empty edit sets/empty translations are errors. Token-only edits do not yield
  a successful literal coverage claim. Per-entry failed codepoints are retained.
- Reports contain entry IDs, target hashes, codepoint/metric status and resource
  identities, not original text or full Font tables. No game assets enter Git.
- The CLI rehashes original text, raw plan, every Font package and optional
  decoder before/after report publication; reports are reopened and compared.
  Existing/aliased output is rejected. An error exit never validates a report.

Exit0: all supplied fonts cover all requested literals (within the above scope).
Exit1: a readable diagnostic report records incomplete/unsupported/no-literal
coverage. Exit2: invalid plan/source/font/output or failed integrity check.
The report's positive literal coverage field is never game/display acceptance.

## Real positive, negative and inverse evidence

The locale plan produces exactly the prior two-glyph technical text candidate:
SHA256 `58c6f12ab4408c600cf9167a54e8038ad42b875d7e9319f797863a15c3cfcebb`.
Both separately extracted original text resources hash to
`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`.
Each candidate remains1495972 bytes and changes only6 bytes. Both written
inverse copies equal the original complete hash and bytes. Original input hashes
remain unchanged. Font-only TOC candidate lengths need no additional text-size
change for this equal-length probe; that is not a general variable-length rule.

The one entry's literal codepoints are U+0021/U+51FB/U+8E22:

| Supplied fonts / experiment | Result | Exit |
|---|---|---:|
| All3 original aliases | Each lacks U+51FB/U+8E22 | 1 |
| All3 D1 supplemented aliases | All3 literals map to positive-area glyphs | 0 |
| All3 D2 supplemented aliases | Same coverage, own text input checked | 0 |
| Candidate negative control with U+6587 | All3 report only that missing remap | 1 |

The original one-entry plan has no protected tokens. Placeholder/order failures,
recognized-vs-unknown syntax, controls, non-BMP/no-remap/zero-area cases are proven
by self-authored tests, not claimed to occur in that real entry. Reports/commands
and inverse proofs remain local under build/text-font-coverage-verification/.

Baseline337 -> modified355 -> independent source rollback337; native-enabled355.
Eighteen new synthetic tests need no game, font raster dependencies or DLL.
They cover source-hash resolution, strict schemas/modes, token/ID/source guards,
raw/compressed aliases, all-font coverage failures, glyph boundary cases,
inverse equality, report/readback/input mutation, CLI and locale-plan consistency.


For a single guarded original-path-shaped Font/text/TOC candidate tree, see
[LOCALE_CANDIDATE](LOCALE_CANDIDATE.md). It requires every binary candidate hash
and full Font identity/semantics, reruns this source/literal audit, updates all
actual resource-size deltas and independently checks backup restoration. This
adds packaging integrity, not runtime/display acceptance.
