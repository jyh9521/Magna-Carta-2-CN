# Warning-scoped two-glyph candidate — 2026-10-19

## Correct the candidate scope

The retained `text-probe.json` edits MC2UI.int `[ButtonA] Kick`, ID
`coalesced:eca4c3906a7e3d00fe0ff6838f0fb2f5bc920c96065b0c8641fec559d5ad8d14`.
Its prior coverage/assembly proofs are valid for that entry, not the warning
whose component/style graph was investigated. Preserve its history; do not
silently re-label its packets as warning candidates.

Active `candidate-disc1.json` / `candidate-disc2.json` now reference
`text-probe-login.json`, with this exact source selector:

```text
resource: MC2Game/Localization/Coalesced.int
embedded_path: ..\MC2Game\Localization\INT\MC2UI_TCR.int
section: GameStart
key: LogIn_NewGame
occurrence: 1
id: coalesced:8c6e837c9ff729ebde4418d1e1c0e51a0a9dce429775a0677dfffd7c82fd14b0
```

**Verified offline:** this is the selector named by both stored TitleMap
MarkupString values `<Strings:MC2UI_TCR.GameStart.LogIn_NewGame>`. Fresh read-only
graph analysis yields1209 parsed UI objects, two matching labels and12
state-specific Font.General_15 paths. Seven non-UI classification gaps remain
separate, not silently counted as complete package coverage.

**Historical evidence only:** RUNTIME_TEXT_BINDING.md records the prior ASCII
marker observation for this same record. This work does not replay that game
test. **Unverified now:** active instances/font selection, Chinese pixels,
clipping/layout, fallback, precedence and game recovery. All game QA is user-run.

## Locale-neutral source-hash prefix mode

The explicit `source_mode=sha256-utf8-prefix` uses schema1 entries with:

```json
{
  "id": "STABLE_ID",
  "source_sha256": "EXACT_SOURCE_UTF8_SHA256",
  "source_prefix_codepoints": 3,
  "replacement": "TARGET_PREFIX",
  "preserve_utf16_units": true,
  "selector": {
    "embedded_path": "EXACT_EMBEDDED_PATH",
    "section": "EXACT_SECTION",
    "key": "EXACT_KEY",
    "occurrence": 1
  }
}
```

Container/source hashes and stable ID are checked before prefix resolution.
Counts are Unicode codepoints, not UTF-16 units or grapheme clusters. The
explicit boolean can require equal UTF-16 code-unit length of source/replacement
prefixes; false permits variable length. No normalization, trimming or case
conversion occurs. An optional exact selector is enforced when present; the
active warning plan supplies all four fields.

The prefix boundary may not split a recognized TOKEN. The complete target must
retain original TOKEN content/order; unknown syntax is not broadly stripped or
declared understood. The exact suffix is copied from the hash-locked source,
so the locale plan contains no original warning text. Mixed literal/full-value/
prefix fields, invalid ranges, bool-as-int counts, nonboolean flags and selector
mismatches fail. Existing valid literal/sha256-utf8 plans retain their behavior.

Prefix coverage reports add verified `edit_scope` selector/counts/suffix hash.
Coverage checks the whole resulting value, not just inserted characters. The
builder CLI additionally rejects duplicate/non-finite JSON, bounds plan size,
rechecks source/plan before/after publication and reopens output bytes. Failure
cleanup removes only its own unchanged new output, not externally changed bytes.
The coverage CLI uses the same strict JSON reader. Neither overwrites inputs,
deploys a resource or launches anything.

## Exact warning resource result

Original Coalesced SHA256:
`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`.
Warning source-value UTF-8 SHA256:
`433b88e1ab8a02514102f0bce9bd48ce787e55dd76ef5d0cc8fffc25d8003282`.
The value has66 UTF-16 units. Its first three codepoints are BMP, so replacing
them with the existing technical marker `踢击!` preserves three units.

- Result Coalesced SHA256:
  `349968ee05e4199e7aa7c557fe6cab86720f9e872813d6885ae2d98d928f05f7`.
  This reproduces the historical Chinese-marker resource bytes, not a new
  rendering observation.
- Size1495972; only6 bytes and exactly one of18176 extracted records change.
  The old Kick entry and all other values remain unchanged.
- The retained63-codepoint suffix hashes to
  `99e5ac25f770688042f0502446efaed030323aa8430633067eedbd88f8c52b20`.
  All three literal `\n` tokens retain content/order. Inverse edits reproduce
  every original container byte.
- All39 result literals are covered by each supplemented General_15 alias.
  Each original alias lacks the two Chinese characters. Remap/metric coverage
  does not verify pixels, shaping, fallback or active runtime font selection.

The prefix plan uses exact LF bytes, SHA256
`1da8e98b28dfb9e4d30fb28faae7fbb418861d0598c9585cf98cea8537845e05`.
Both candidate plans lock those bytes. No extra glyph or dialogue row is added.
The three Font binaries/semantic identities stay unchanged from
FONT_BUNDLE_BUILD.md; only the active text experiment's scope changes.

## Offline build and independent replay

Supply originals and verified Font bundles as in LOCALE_CANDIDATE.md. Use fresh
output paths, for example:

```powershell
python tools/build_coalesced.py build/poc-game/disc1/MC2Game/Localization/Coalesced.int locales/zh-Hans/text-probe-login.json --output build/NEW-login-Coalesced.int
python tools/build_locale_candidate.py --plan locales/zh-Hans/candidate-disc1.json --game-root build/poc-game/disc1 --font-bundle build/font-bundle-verification/disc1 --output-dir build/NEW-login-disc1 --lzx-library build/lzx/native-verified/ue3_lzx.dll
python tools/verify_locale_candidate.py --plan locales/zh-Hans/candidate-disc1.json --candidate-root build/NEW-login-disc1 --manifest-sha256 EXACT_MANIFEST_SHA256 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-login-disc1-independent.json
```

Disc2 uses its own original-root/TOC and bundle. Retained D2 input copies are
rehashed against source plans, not described as a fresh whole-ISO verification.
Each packet has five resources/18 files, including controls/restored backups and
relative metadata. These are resource packets, not a bootable game/installer.
Artifacts remain ignored under build/; originals/user configuration stay intact.

Both discs assemble and independently replay with the corrected prefix plan;
ten resource backup restorations match their respective original inputs. Equal
text size leaves both TOCs at their previous font-only hashes. Old Kick packets
must fail under the new trusted warning plan, despite earlier successful
integrity/coverage checks. Historical plans are required to replay old packets.

Twenty new synthetic tests cover Unicode/unit semantics, token boundaries,
selector/source/ID guards, full-suffix coverage/inverse recovery, strict JSON,
input mutation/reopening/cleanup, legacy compatibility, locale contracts and
assembler/independent-verifier replay. Full source regression537 ->557 ->
isolated rollback537; optional decoder557. Default CI needs no game, original
font or native decoder.

The prepared experiment now agrees with the investigated UI/nested-style scope.
Native default/property and measurement leads remain separate unresolved work;
none of these offline results grants display acceptance or starts bulk dialogue
translation.
