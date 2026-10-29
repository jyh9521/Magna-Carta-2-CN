# Phase 330: metric-bound text layout revision

## Reproducible inputs and tools

`locales/zh-Hans/gameplay-text-layout-v9.json` is the locale data. The compiler is
`tools/build_text_layout_revision.py`; locale punctuation, bracket pairs, selected
entry IDs, requested literal changes, reviewed paragraph reflow, consumer
contracts and source hashes live in the profile, not in generic Python rules.

Inputs are the current Coalesced and all 44 timed subtitle resources from both
discs, the v9 numeral font candidate, and the current UI/tutorial packages.
Coalesced's exact input SHA-256 is
`95f2f7dde775b2fc539379820366aa9dcc538a20eb64d976bb8d5ae9fe3212d9`.
Each resource records independent per-disc source identities. A shared path is
not assumed to be shared content: all listed source hashes must match the actual
input bytes. The two-disc Coalesced input is byte-identical. The only changed
timed-text resource, `MC2Game/Movies/csm13-50.txt`, belongs to disc 2.

Example (substitute directories containing the hash-matched game resources):

```powershell
python -B -X utf8 -m tools.build_text_layout_revision `
  --profile locales/zh-Hans/gameplay-text-layout-v9.json `
  --text-root TEXT_RESOURCE_ROOT --font-root V9_FONT_ROOT `
  --consumer-root CURRENT_UI_RESOURCE_ROOT --lzx-library LZX_LIBRARY `
  --output NEW_OUTPUT_DIRECTORY
```

`--mode baseline` runs the identical contracts against the retained input text
and returns a nonzero status for the reproduced defects. The font metrics are
the same final v9 measurement reference in both modes. This text-only comparison
does not pretend to roll back the independently changed numeral font.

The compiler writes reopened candidate resources, a Coalesced edit plan and
inverse plan, timed-cue plans, an audit and a manifest. Existing output trees and
overlapping input/output roots are rejected. A clean checkout can run this
compiler from the versioned profile and the supplied, hash-matched resources;
the development-only classification cache is not an input.

## Coverage and measured results

* All **18,176 Coalesced fields** are enumerated and checked for orphaned explicit
  line-start punctuation. This does **not** mean every field has a proven UI
  width. Unassigned field IDs are written separately in the audit.
* **10,416 body fields** have declared layout contracts: 5,499 scene dialogue /
  narrative fields; 4,593 balloon-family fields; 127 quest descriptions;
  117 mail bodies; and 80 tutorial bodies.
* **10,411** of those fields are measured and checked. The other **5** are
  source-locked explicit holds described below. Any new unsupported assigned
  field counts as a failure and makes the CLI return nonzero.
* **51 tutorial packages**, both foreground and shadow widgets, provide 160
  direct string consumers for the 80 body fields. The compiler reopens the
  packages and verifies each label payload, string binding, width, height and
  renderer payload / wrap setting. With the three shared UI extent contracts,
  this is **323 object contracts across 52 packages**.
* All **315 cues in 44 timed-text files**, including disc-2-only files, are
  measured. Cue start/end times, classes, clear events, BOM and framing are
  unchanged. One cue in `csm13-50.txt` rejoins an old ellipsis-leading line with a count-locked `<br>` change (1 to 0); it fits in one native-width line.
* **2,994 Coalesced fields** change. Requested literal edits remove the final
  full stop from `MC2UI_TCR.GameStart.NoFileToLoad` and replace **87** uppercase
  `QUEST` literals with `任务`. Format tokens such as `%s` retain their exact order.
* The same-contract static comparison is **2,995 baseline failures → 0 modified
  failures**, with **0 unknown unsupported fields** and the **5 explicit holds**
  visible separately. This is offline evidence, not game rendering acceptance.

## Budgets and their evidence level

**Verified serialized values:** `Default__MC2UIBalloon.WidthExtentMax` is 400;
the balloon renderer enables vertical autosizing with a minimum of 80, but does
not serialize a proven maximum height. Tutorial bounds come from each direct
consumer's `Position.Value[2/3]`; the tighter foreground/shadow bounds win. The
quest-body viewport is 596 × 240; the mail-body viewport is 612 × 304. The final
General font's maximum glyph `VSize` is 25 and Subtitle's is 31. Font advance
tables and maximum glyph heights are hash/identity checked at build time.

**Explicit conservative static envelopes:** wide scene/cinematic text uses
1,078 native pixels (1,280 minus two 101-pixel margins), at most three lines.
This is not a recovered live widget rectangle. Balloon-family routing uses the
serialized 400-pixel class width and an additional ten-line screen-budget
ceiling; that ceiling is not a measured maximum of every native balloon. File
families are declared in the profile rather than presented as individually
traced native call sites.

Vertical checks use the font's native maximum glyph height with the default
unit scale. Consumer payload locks prevent silently changing the measured
template, but dynamic native scaling, positioning, paging and clipping still
need in-game acceptance. Mail scrolling/paging has not been proven; its
viewport is therefore not silently treated as unbounded.

Six previously over-tall mail bodies and `Tutorial_Scene_12.Text_0` receive
reviewed paragraph reflow: only isolated soft line breaks are recomposed;
empty paragraph separators, all visible characters and all non-break tokens
remain intact. The longest mail, `E04_008.E04_008_Con`, prioritizes the longest
legal line and fits twelve native 25-pixel lines in the 304-pixel viewport.
No text is shortened or omitted. The screenshot tutorial
`Tutorial_CSMB_00_15_00.Text_1` prefers its comma boundary and keeps `[A键]` intact.

## Line-breaking rules and protected data

`tools/text_line_layout.py` measures exact native advances. It does not emulate
the complete engine tokenizer. It emits hard breaks before the declared width
is exhausted, binds bracket groups and style-icon spans atomically, and avoids
locale-specified closing punctuation at new line starts. Double ellipses and
dashes are not split. An intentional ellipsis at a new blank-separated paragraph
is distinguished from an orphan produced by wrapping.

Ordinary hard breaks and empty paragraphs remain unless a profile explicitly
opts a source-locked field into paragraph recomposition. The before/after text
with break tokens removed must match exactly. The only other visible changes
are the 88 explicitly requested literal edits above.

Coalesced break changes carry exact source/target `\n` counts. Timed text now
supports an optional `break_policy` restricted to the exact token `<br>` and its
exact counts. All other protected markup stays ordered and unchanged. Reverse
timed-text rebuilding swaps those counts and must recover the original bytes.

## Five retained original control ambiguities

These current translated entries contain bare backslashes already present in
the pristine game entry. Their native meaning has not been verified. The
profile pins each current ID and UTF-8 source hash and leaves the complete
field unchanged, rather than deleting or reinterpreting the marker:

* `MC2CSMB.int / CSMB03_20 / voc_csmb_0320_50`
* `MC2NpcTalk.int / Ch00_1 / 00_101_00`
* `MC2Quest.int / 06_603_0 / 603_0`
* `MC2Quest.int / 06_zepi_1 / order_2`
* `MC2_com_Zephi.int / Celestin / Abnormal_bad_ch3_01`

These are an explicit unresolved boundary, not five additional passes. The
audit also separates the **7,760 unassigned fields** (names, machine/editor
strings and other UI categories) from the width-checked body population.

## Regression and rollback

```powershell
python -B -X utf8 -m unittest discover -s tests -p 'test_text_*layout*.py' -v
python -B -X utf8 -m unittest discover -s tests -p 'test_*subtitle*.py' -v
```

The new layout suite covers punctuation, atomic brackets/styles, explicit
paragraph preservation, missing/dynamic tokens, height failures, count-locked
timed breaks, inverse-byte equality, strict unsupported-field failure, exact
holds, CLI status, output confinement and guarded rollback. The existing
subtitle regression suite remains compatible with plans without break policies.

`tools.rollback_text_layout_revision` validates **all** retained baseline,
candidate and copy hashes before restoring an isolated copy. It reopens every
restored file and verifies that the authoritative candidate remains changed.
It rejects using the retained candidate or baseline tree as the rollback target.

```powershell
python -B -X utf8 -m tools.rollback_text_layout_revision `
  --build-root VERIFIED_BUILD --baseline-root TEXT_RESOURCE_ROOT `
  --copy-root ISOLATED_CANDIDATE_COPY
```

The isolated restored text must reproduce the baseline audit and original
resource hashes. No executable, game installation or ISO is modified by these
text tools, and the game is not launched.
