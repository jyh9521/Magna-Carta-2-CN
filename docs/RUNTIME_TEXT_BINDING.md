# Runtime text binding and font experiments (2026-10-18)

## Verified inputs and boundaries

All runs use Canary `50e9c715d`, Disc 1 title `4E4D0811`, and an unchanged
`xenia/xenia-canary.config.toml` snapshot (SHA256
`7c89cfb8c2a0435cbe2e0764581b032cf17c0bb50fc4d721459b5b7b2508962b`).
D3D12, 2x1 and VSYNC remain as supplied. Original ISO/XEX files are unchanged.
Only the ignored extracted working directory was deployed. Saves/content/cache
are isolated per run. There is no save/progression/console acceptance yet.

Keyboard controller emulation is disabled in the supplied configuration. The
controlled runs explicitly add `--keyboard-test-input` (see XENIA_TESTING.md).
This is a recorded input-only deviation, not an exact effective-settings baseline.

## Real UI text binding: Verified

Target: embedded `MC2UI_TCR.int`, `[GameStart] LogIn_NewGame` in
`MC2Game/Localization/Coalesced.int`. Stable record identifier:
`coalesced:8c6e837c9ff729ebde4418d1e1c0e51a0a9dce429775a0677dfffd7c82fd14b0`.

The original interactive warning was captured. Replacing only its first three
UTF-16 code units by `TST` changed six bytes, retained size 1495972 and preserved
all remaining text/control tokens. The same warning visibly starts `TST`.
This proves this INT record is used by this warning; it does not prove priority
for every locale/resource or prove which Font object draws the warning.

| Copy | SHA256 |
|---|---|
| Original | `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c` |
| ASCII marker | `c23576313bf8301fa97a84b551d57d017e979c4000360351fc08ddc0193b91c2` |
| Chinese marker | `349968ee05e4199e7aa7c557fe6cab86720f9e872813d6885ae2d98d928f05f7` |

Local evidence: `build/binding-20261018-original-input/original-login.png`,
`build/binding-20261018-ascii-special/ascii-login.png`, and hash-guarded change
records in `build/binding-resource-experiment/`. Original assets/screenshots stay
local, not in the public repository.

## Font / package experiment matrix

The Chinese marker is `踢击!`. With original fonts the two Chinese characters
are absent while `!` and the remaining Korean text render normally. The same
absence persists in the following captured interactive warnings:

| Candidate | Actual result |
|---|---|
| Original fonts, changed text only | Missing Chinese: negative control |
| General_15 resident only, raw outer package | Boots; Chinese absent |
| General_15 resident + external, raw atlas | Boots; Chinese absent |
| EngineMedium_Subtitle external only, raw atlas | Boots; Chinese absent |
| EngineMedium_Subtitle resident + external, raw atlas | Boots; Chinese absent |
| Subtitle remap pairs sorted, resident + external | Title/movie observed; warning outcome pending, not counted as a result |

General_15 count 2608→2610 and Subtitle count 1259→1261 passed static append,
metrics, old-pixel preservation and package-table checks. **Neither Font binding
nor Chinese rendering is established by these tests.** The locale plans remain
`in_game_verified: false`. Next probe should alter an existing visible glyph's
mapping in isolation, rather than add more new glyphs on an assumed font path.

### Compressed-package controls

Resident Font objects are duplicated inside Startup_int.xxx. Stored-LZX rebuilds
passed the independent native decoder, but the game guest crashed. Re-encoding
only the first chunk of the ORIGINAL package, with identical decoded logical
bytes and no font change, also crashed. A makecab LZX17 control decoded exactly
but crashed too; padding it to 32768 bytes did not resolve that failure.

| Control | Guest observation |
|---|---|
| Stored-LZX font candidate / original first-chunk no-op | PC `82488884` read fault |
| CAB first-chunk no-op / aligned control | PC `8286B9B0` write fault |
| Raw outer package, compression flags/count zero but package bit retained | PC `823C0144` read fault |
| Raw outer package, also clear package bit `0x02000000` | Title and interactive warning load |

These controls narrow the failure independently of atlas additions; they do not
identify the exact compressor incompatibility. Movie playback on another thread
after a guest fault is not successful boot. Do not ship the stored/CAB candidates.

## Experimental raw-copy tool

`tools/decompress_package.py` accepts only the parsed big-endian 446/25 LZX
profile, requires input SHA256 and the package compressed bit, decodes all logical
bytes, clears compression flags/count AND package bit `0x02000000`, and validates
all object tables and payload preservation before writing a new aligned copy.
The package-flag offset is parsed from the header (21 for this sample), not used
as a blind patch offset. Outputs/report must be new and distinct from inputs.

The real General_15 raw candidate is 13336576 bytes, SHA256
`cae2f933eb168588953354c235633a4c627b996354eb312e089bb3cbc2c962bf`.
It loads the warning but still does not render Chinese. Larger uncompressed copies
are research outputs, not an accepted game release format or Xbox 360 validation.
`--raw-atlas` separately emits local raw texture bulk data instead of stored-LZX;
this does not remove the need to verify runtime resource selection.

## Recovery and next gate

All four deployed files were hash-guarded and restored from retained originals:
Coalesced.int, Startup_int.xxx, font.xxx and Xbox360TOC.txt. Exact before/after
hashes are in `build/binding-resource-experiment/rollback-resource-hashes.json`.
File recovery passes. Same-warning final recovery capture is still pending until
recorded explicitly; a restored hash alone is not visual rollback acceptance.

Next: complete that capture, then identify the live Font using an existing-glyph
sentinel, establish runtime mapping/atlas selection, and repeat the Chinese
negative/candidate/recovery sequence. No bulk translation or formal ISO merge
starts on the basis of these partial results.

## Same-size mapping sentinel tool (2026-10-18)

`tools/probe_font_mapping.py` changes only one existing remap glyph-index uint16
field in a selected Font export. It requires the complete package SHA256, exact
object path, codepoint, expected original glyph index and bounded existing target
index. Compressed packages are rejected; make a separate raw copy first when
needed. Glyph count, tables, tagged/native geometry and texture bytes stay intact.
This is a diagnostic probe, not translation data or a release patch.

```powershell
python tools/probe_font_mapping.py INPUT_PACKAGE --sha256 INPUT_SHA256 --font-object OBJECT_PATH --codepoint 0xB85C --expected-glyph ORIGINAL_INDEX --target-glyph 65 --output NEW_PACKAGE --report NEW_REPORT
```

The original warning starts with U+B85C. Static data maps it to General_15 glyph
959 and Subtitle glyph 595. An isolated candidate redirects General_15 to its
existing ASCII A (65) and Subtitle to B (66), in external font.xxx and the resident
Startup copy. Only two remap fields change per package relative to its appropriate
original/raw baseline; text and atlases are unchanged. A visible A or B replacing
the original first syllable would identify a font candidate, but runtime outcome
must be recorded separately. Missing or unchanged text is not positive binding.

Five synthetic tests cover exact inverse recovery, field-only changes, hash,
object/mapping/index guards, compressed-input rejection and CLI output protection.
Local static outputs: build/font-mapping-probe/. Runtime binding remains pending.

The fresh `binding-20261018-recovery-hb2` run reverified the supplied config dump
and reached the original title. Sent Start key events did not yield a captured
interactive warning before the idle movie resumed. This is an inconclusive input
attempt, not visual recovery acceptance. No sentinel package was deployed during
this run; the extracted game remains at the original four resource hashes.
