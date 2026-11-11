# Function string-boundary closure (phase369)

## Verified offline result

The 198 `vm-unicode-token-candidate` records in the phase366 census are **not
Unicode string instructions**. They represent193 distinct byte positions; five
positions produced both UTF-16LE and UTF-16BE hypotheses. All198 rows remain in
the report; their IDs include the hypothesized encoding rather than collapsing
the five pairs. All198 exact candidate bytes and owning export
paths were rebound to the phase368 recipe before classification. The complete
owning function bodies, plus the 15 phase364 metadata-profile gaps, were parsed:

| Scope | Result |
| --- | --- |
| Selected unique functions | 96: Core 9, Engine 27, MC2Game 60 |
| Complete script bytes / tokens / nonoverlapping atoms | 39,668 / 9,776 / 23,468 |
| Candidate `0x34` bytes in metadata | 54 |
| Candidate `0x34` bytes inside script operands | 144 |
| Distinct source positions / duplicate endian hypotheses | 193 / 5 |
| Actual `UnicodeString` instructions | 0 |
| Actual narrow string literals | 182; all ASCII |
| Metadata gaps resolved / still unparsed | 15 / 0 |
| Confirmed Korean omissions / game bytes changed in this scope | 0 / 0 |

Every function ends at its exact final `EndOfScript`; unknown opcodes, truncated
operands and ambiguous native declaration bindings fail rather than resynchronize.
All 96 owning payload hashes equal their census-bound payload hashes. Core,
Engine and MC2Game package hashes themselves also equal the census inputs; the
older phase364 metadata report supplies only the 15 IDs/paths, not current bytes.

### Input binding

The phase368 recipe SHA-256 is
`7fc7aca33b52a1f2cbf0c9d70e90181de26aafecd4b2362a49f52f8a9224a0fc`.
All three packages are big-endian version446/licensee25:

| Package | Effective SHA-256 |
| --- | --- |
| Core | `1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815` |
| Engine | `67ad212cb85233b1c1524c11ac7ad6bbbf393c61fdfbb399430130fd0c07aef9` |
| MC2Game | `9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7` |

The candidate rows preserve both original census identity and current logical
offset, exact bytes/hash, export ID/path, field/operand span, and consuming token.
Local evidence is in `build/phase-369-coverage-closure/vm/`: `inputs.json`,
`candidates.json`, `functions.json`, `metadata-gaps.json`, `literals.json`,
`summary.json`, and `errors.json` (empty).

### Why the scan matched Korean-looking bytes

The census searched for byte `0x34` followed by a terminated wide-looking byte
sequence. The same byte occurs in integer operands and serialized metadata.
Examples (all offsets are logical-package positions, not native addresses):

| Candidate | Owner | Offset | Verified containing field |
| --- | --- | ---: | --- |
| vm-001 | Core Function198 `Object.Not_PreBool` | 113915 | Function flags; candidate bytes `34 11 00 00 00` |
| vm-011 | Engine Function743 `Actor.EffectIsRelevant` | 2016121 | Property reference operand `00 00 00 34` |
| vm-024 | Engine Function15379 `SavedMove.SetMoveFor` | 3190149 | Jump target operand `00 34` |
| vm-045 | MC2Game Function13022 `MC2ItemManager.CheckWeaponCollect` | 7915936 | `IntByte` value `34` (decimal52) |
| vm-076 | MC2Game Function13485 `MC2KismetHook.OnFadeTime` | 7966020 | Children reference `00 00 34 ac` |

The144 script-operand candidate rows (139 distinct positions) comprise130 property references, five jump targets,
three function-name indices, two context-skip words, two name-literal indices,
one byte literal and one function reference. The 54 metadata matches comprise
ten children references, ten next references, ten friendly-name indices, eight
flag words, eight text-position words, six script sizes and two line numbers.
Changing these Korean-looking byte sequences would corrupt references/control
data. No translation entry or binary replacement is appropriate for them.

## The 15 metadata gaps

The older `ue3_function_metadata`/scripted-UI reader intentionally has a narrower
profile. It is **unchanged**. The new opt-in storage reader accepts these exact
serialization cases while still validating the owner, references, export name,
payload size and final byte:

| IDs in MC2Game | Resolution |
| --- | --- |
| 9380 `AddPawnDieEvt_2`; 13416 `CircleSpawnKan_2` | FName instance3 expands to suffix `_2` |
| 25902–25907 `Timer_ShowPlayerMember_0` through `_5` | FName instances1–6 expand to suffixes0–5 |
| 27540 `Reverse_2_1` | Base `Reverse_2`, instance2 expands to `Reverse_2_1` |
| 24772 `ClientSetCinematicMode`; 24908 `ClientSetRotation`; 24919 `ClientRestart`; 25596 `ClientCommitMapChange`; 26076 `ClientUpdateAchievement` | Net flag `0x40` adds a big-endian `u16 RepOffset` after FunctionFlags; all five store `ffff` |
| 19297 `MC2PawnInterfaceBattle.DisplayDebug` | Script is10244 bytes, two bytes beyond the older10242-byte wrapper limit |

The new default size cap is65535 serialized bytes and may be reduced explicitly.
FName instance expansion is exact `base + '_' + (number-1)`, not a mismatch
exception. Non-operator names must still equal the canonical export leaf.
Networked functions retain their complete17-byte metadata tail rather than
being misread as the15-byte non-Net tail. Every resolved ID has exact tail bytes,
payload hash, script hash and complete token/atom boundaries in the local report.

## Reusable interface and validation

- `tools/ue3_script_boundaries.py`: `function_storage`, `native_declarations`,
  `decode_boundaries`, `function_boundary_report`, `classify_export_offset`.
- `tools/inspect_script_boundaries.py`: read-only package CLI, explicit SHA-256
  guards for the main and reference packages, repeatable exact `--object` scope,
  a new/distinct report path, reopening comparison and unchanged-input checks.
- `tests/test_script_boundaries.py`:21 self-authored tests with no game assets.

Example, substituting actual supported input files and hashes:

```powershell
python tools/inspect_script_boundaries.py HOST\MC2Game.xxx --sha256 SHA256 --object MC2PawnInterfaceBattle.DisplayDebug --reference-package Core HOST\Core.xxx CORE_SHA256 --reference-package Engine HOST\Engine.xxx ENGINE_SHA256 --lzx-library HOST\ue3_lzx.dll --output build\NEW-function-boundaries.json
python -m unittest discover -s tests -p test_script_boundaries.py
```

Exit0 means every selected function parsed; exit1 means explicit unparsed
functions; exit2 means input/profile/report failure. Native opcodes bind to203
unique source declarations across these three packages (zero ambiguous tokens
and zero metadata-header errors). References retain validated table bounds and
class categories, including the actual `ComponentProperty` references used by
Actor and UI component consumers. Native parameter stubs additionally retain
exact owned declaration-chain/order verification. Scripted function declaration
types are not a complete type checker.

The atom reader was independently implemented using Eliot van Uytfanghe's
MIT-licensed Unreal-Library commit
`8236c39b79e30887a487ecf9b018204e430a5ebc`; the pinned original paths, URLs and
SHA-256 values are in `references/script-boundaries-research.lock.json`.
No upstream runtime/source or complete proprietary asset is included.

## Interpretation and remaining boundary

**Verified source syntax:** `literals.json` records all182 actual literals and
their enclosing call expressions. Most belong to `Actor.DisplayDebug` and
`MC2PawnInterfaceBattle.DisplayDebug`, including `Canvas.DrawText`/`DrawDebug`
calls. Other literals occur in comparisons, sequence-variable lookups, logs or
name construction. None contains Hangul or any non-ASCII code point.

**Not established by this reader:** execution/reachability, native dispatch
registration or implementations, dynamic display values, complete runtime
types, Context-skip semantics, font/pixel behavior or in-game acceptance.
`runtime_execution_observed` and rendering acceptance remain false. This96-body
closure is not a claim that every script in the game has been decompiled. Future
unknown opcodes remain explicit errors; the reader never promotes a raw text
scan to a display string merely because it resembles a language.
