# Pitfalls

## 2026-10-19: initialized native pointers are not cold descriptor rows

Font/MultiFont/Canvas store name/code pairs eight bytes apart, while the earlier
UI component profile has cold12-byte descriptors. Preserve the initialized
code words and indexed native tokens464/470 instead of zeroing or relabelling
metadata to satisfy the cold reader. Canvas's complete header inventory must
retain12 omitted scripted functions; partial successful native parsing is not
whole-scope evidence. See INITIALIZED_NATIVE_TABLES.md.

## 2026-10-19: a local Font Class is not an unresolved imported Engine.Font

Engine's SmallFont uses an exact local Font Class definition. A reader that
requires only the imported display path Engine.Font rejects it before coverage
analysis. Resolve the class reference, not an arbitrary *.Font suffix. Both
SmallFont aliases are non-remapped: the39 warning literals remain explicitly
mode-unverified, not missing-remap or passed direct-index coverage. The
supplementer must retain its explicit-remap guard. See STYLE_REFERENCE_HELPER.md.

## 2026-10-19: fallback names and output-zero stores do not prove font defaults

The style-reference helper associates three native class-name operand chains
with default text/image/combo tag literals. Its two cleared output words and
optional flag stores are not Font initialization. A registration window does
not establish its function's returned runtime class; repeated parent+3C loads
do not establish termination. Preserve external-call and serialized/native
layout unknowns; see STYLE_REFERENCE_HELPER.md.

## 2026-10-19: a conditional selector is not a constant default-style route

All four supplied component tables share slot124's actual36-word predicate.
Its entry+104 gate, four-word OR and helper-result gates prevent interpreting
the getter's alternate-owner route as unconditional. Static offset equality
between the predicate and getter does not assign serialized fields to native
memory. Preserve the SmallFont CDO and General_15 component observations until
the identities/values are proved; see STYLE_SELECTION_PREDICATE.md.

## 2026-10-19: component StringStyle does not exhaust label style candidates

The two warning labels omit their own PrimaryStyle, while the independent CDO
plane contains a DefaultComboStyle tag. Six nested text objects omit StyleFont;
their separate class-default plane observes EngineFonts.SmallFont. Retaining
those observations must not merge defaults or identify the native alternate
owner pointer by assumption. The original twelve General_15 component paths
remain unchanged; neither route proves effective font selection. See
OWNER_PRIMARY_STYLE.md.

## 2026-10-19: physical Font copies need not have different runtime identities

**Verified:** standalone font.xxx and forced-export Font roots in MC2Game/Startup
share canonical Font.General_15 and the original Font package GUID. Whole raw
payload hashes differ, while complete normalized glyph/remap/decoded-atlas data
is equal. A one-package probe can therefore leave another same-namespace copy
untouched; source metadata does not prove which copy wins. The new diagnostic
marks all three planned copies together. A null archetype/missing override field
also does not establish false/zero native defaults. See FONT_BINDING_AUDIT.md.

## 2026-10-18: component prefix and nested-ID pitfalls resolved

**Verified for 446/25:** the extra component header precedes NetIndex; it is not
a universal twelve-byte skip. Ordinary instances use 8-byte prefixes, templates
under class-default outers 16, and class-default objects themselves 4. Raw flags
are two LO/HO words. STYLE_ID is tagged A/B/C/D, not native GUID bytes. All these
branches have synthetic regression tests and original-package verification;
see UI_STYLE_GRAPH.md. The earlier no-guessing entry below remains valid history.

## 2026-10-18: a failed component prefix is not an absent Font reference

**Verified:** the current NetIndex-plus-tags consumer reader cannot parse 9703
MC2Game exports, including 954 UIComp_DrawString objects. The earlier narrow
UIStyle scan returned no direct links in that package, while the broadened
reader finds 16 on custom defaults. Neither result covers component native
prefixes or nested style structures. See FONT_CONSUMERS.md for exact counts.

Do not infer no font use from an empty result, search for arbitrary plausible
tags, or guess a universal 12-byte skip from a few component samples. Preserve
coverage, object indices, failure reasons and logical offsets. A malformed later
ObjectProperty must discard earlier candidate links from the same object.
The new synthetic consumer tests lock this object-level atomicity.

This document records failed approaches, misleading assumptions, fragile workflows, compatibility traps, and other technical mistakes discovered during development of the localization project.

The purpose is to preserve negative knowledge.

A failed approach can be as valuable as a successful one if it prevents future contributors from repeating the same work.

---

# 1. How to Use This Document

Add an entry whenever a problem meets one or more of these conditions:

- it consumed significant investigation time
- the obvious solution turned out to be wrong
- the failure can corrupt data or crash the game
- the issue is easy to reproduce accidentally
- the cause is not obvious from the symptoms
- the workaround has important side effects
- the problem is version-specific
- the problem is tool-specific
- future contributors are likely to repeat the same mistake

Do not use this file for ordinary TODO items.

Use `docs/KNOWN_ISSUES.md` for unresolved player-visible limitations.

Use this file for technical traps and lessons learned.

---

# 2. Entry Template

Use the following structure for each pitfall.

```markdown
## Short descriptive title

**Status:** Verified / High-confidence / Unverified

**Affected area:**
- resource format
- font
- executable patch
- archive
- build system
- translation
- runtime hook
- toolchain

**Symptoms:**
Describe what happens.

**Initial assumption:**
Describe what seemed likely at first.

**Actual cause:**
Describe the verified or suspected root cause.

**Failed approach:**
Describe what was tried and why it failed.

**Working solution:**
Describe the correct workaround or fix.

**How to detect it:**
List checks, hashes, logs, or behaviors that reveal the problem.

**Regression test:**
Describe how to make sure the problem does not return.

**Related files:**
List relevant source files, scripts, resources, or documentation.
```

---

# 3. Preserve Failed Approaches

Do not delete a failed experiment merely because a better solution was found.

Useful failed approaches include:

- replacing only a font texture
- changing encoding without changing the decoder
- rebuilding an archive without updating secondary metadata
- patching only one copy of a linked string
- increasing a buffer without updating a length check
- converting all text files to UTF-8
- using system locale as a hidden runtime dependency
- copying generated files from an old project directory
- manually editing binary data without reproducible tooling

Record what failed and why.

---

# 4. Binary Patch Pitfalls

Typical risks include:

- patch offsets differ between game versions
- executable packing changes file offsets
- RVA and file offset are confused
- expected bytes are not verified
- patch writes cross instruction boundaries
- branch displacement is calculated incorrectly
- patched code assumes the wrong calling convention
- stack cleanup differs between versions
- instruction cache or loader behavior differs by platform

For every binary patch problem, record:

- target version
- target hash
- address or offset
- original bytes
- patched bytes
- exact failure behavior

Never record only "the patch crashed."

---

# 5. Encoding Pitfalls

Common mistakes include:

- assuming visible Korean, Japanese, or Chinese text implies a standard code page
- treating byte length as character length
- treating character length as glyph count
- converting runtime files to UTF-8 without verifying parser support
- trimming bytes that are actually part of a multibyte sequence
- interpreting control codes as text
- applying Unicode normalization that changes expected byte sequences
- confusing encoded text with direct glyph indexes

When an encoding issue is found, record:

- sample source bytes
- expected display
- actual display
- decoding rule
- terminator behavior
- control-code interaction

---

# 6. Font Pitfalls

Common failures include:

- replacing the atlas without replacing the character map
- replacing glyphs without updating width metrics
- using a font that does not cover all translated characters
- exceeding texture size limits
- exceeding glyph count limits
- using the wrong baseline
- changing line height unintentionally
- assuming monospaced behavior in a proportional system
- generating glyphs in a different order than the runtime expects
- using proprietary fonts that cannot be redistributed

Record both visual symptoms and technical cause.

---

# 7. UI Layout Pitfalls

Typical symptoms include:

- clipping
- overlapping labels
- buttons expanding incorrectly
- subtitles leaving the visible area
- menu rows colliding
- dialog boxes becoming too small
- text scaling differently at high resolution

Possible causes include:

- logical resolution differs from physical resolution
- text measurement uses physical pixels
- UI layout uses fixed coordinates
- font scale and layout scale are independent
- string width is calculated before localization replacement
- line wrapping occurs before runtime substitution

Record which coordinate system each relevant component uses.

---

# 8. Archive Rebuild Pitfalls

Common mistakes include:

- updating the archive TOC but not a secondary manifest
- ignoring alignment
- changing entry order
- recompressing with incompatible settings
- forgetting checksums
- using a generic packer that does not match the game's variant
- failing to update filename indexes
- producing correct-looking archives that crash only at runtime

When documenting an archive problem, include:

- archive type
- tool used
- original structure
- rebuilt structure
- relevant offsets
- alignment requirements
- secondary metadata

---

# 9. Linked Resource Pitfalls

Some text may appear in multiple locations.

Failure to update all copies may cause:

- invisible items
- missing documents
- broken quest progression
- crashes
- wrong labels
- broken resource lookup

Record linked groups explicitly.

Where possible, replace manual duplication with one source-of-truth translation entry.

---

# 10. Translation Data Pitfalls

Common problems include:

- duplicate IDs
- source and target columns swapped
- spreadsheet software changing encoding
- CSV delimiter corruption
- automatic quote escaping
- line endings altered unexpectedly
- placeholders removed by machine translation
- tabs inserted into TSV fields
- leading zeros removed from IDs
- formulas evaluated by spreadsheet software
- strings normalized unintentionally

Document safe editing tools and unsafe workflows.

---

# 11. Spreadsheet Pitfalls

If translation data is edited in spreadsheet software, watch for:

- automatic date conversion
- numeric ID conversion
- scientific notation
- encoding changes on CSV export
- dropped leading zeros
- escaped quotes
- line break conversion
- formulas replacing literal text

Prefer TSV, JSON, PO, or other formats that preserve text predictably.

If spreadsheet software is supported, document the exact import/export procedure.

---

# 12. Build System Pitfalls

Common problems include:

- build scripts assuming absolute local paths
- hidden dependencies on old output directories
- stale generated files masking failures
- release builds using untracked local resources
- tools found through PATH on one machine but not another
- case-sensitive paths working on Windows but failing on Linux
- different Python versions changing output
- different compiler architectures producing incompatible binaries

Record clean-build failures and their causes.

---

# 13. Dependency Pitfalls

Document external tools that:

- changed behavior between versions
- are no longer downloadable
- have incompatible licenses
- require GUI interaction
- depend on system locale
- produce non-deterministic output
- silently overwrite files
- do not support long paths
- do not support Unicode paths

Where possible, pin known-good versions.

---

# 14. Runtime Hook Pitfalls

Common problems include:

- hook runs before the target module is loaded
- hook runs too late
- thread-safety problems
- recursive hook calls
- hook conflicts with other mods
- proxy DLL name conflicts
- function signature mismatch
- renderer-specific assumptions
- anti-cheat or integrity systems blocking injection

Document initialization order and compatibility limitations.

---

# 15. Emulator Pitfalls

When testing console games, distinguish:

- game bugs
- patch bugs
- emulator bugs
- renderer bugs
- timing bugs

Record:

- emulator version
- backend
- settings
- whether the issue reproduces on hardware or another emulator

Do not diagnose emulator-specific behavior as a game-format fact without evidence.

---

# 16. Save Data Pitfalls

Localization changes can sometimes affect save compatibility.

Possible causes include:

- translated identifiers
- changed resource indexes
- string length changes in serialized structures
- locale-specific save paths
- checksum differences
- version tags

Never assume visible text is safe to translate if it is also used as an internal key.

---

# 17. Subtitle Pitfalls

Common problems include:

- subtitle text exceeds safe width
- hard line breaks conflict with automatic wrapping
- subtitle timing shifts after video re-encoding
- subtitle renderer does not support target glyphs
- pre-rendered subtitles use the wrong font
- line count exceeds engine limits

Record exact timing and rendering constraints.

---

# 18. Media Re-Encoding Pitfalls

If video or audio must be regenerated, document:

- codec
- encoder
- version
- bitrate
- dimensions
- frame rate
- audio format
- muxing requirements

Generated media may differ across tool versions.

Do not assume functional equivalence implies byte-identical output.

---

# 19. Path and Filesystem Pitfalls

Common problems include:

- Unicode paths
- spaces in paths
- very long paths
- case sensitivity
- slash direction
- reserved Windows filenames
- read-only installation directories
- Steam or launcher auto-repair
- antivirus quarantine

Build tools should quote paths correctly and avoid unnecessary path assumptions.

---

# 20. Git Pitfalls

Common repository mistakes include:

- committing generated output
- committing proprietary game files
- committing local-only instructions unintentionally
- tracking files that should remain ignored
- losing executable bits
- line-ending conversion
- Git LFS pointer mistakes
- renaming only by case on case-insensitive filesystems

Document project-specific Git requirements if needed.

---

# 21. Release Pitfalls

Before release, verify that the package does not accidentally include:

- original game binaries
- private paths
- debug logs
- temporary files
- proprietary fonts
- test assets
- developer-only configuration
- untranslated debug strings
- stale build output

A release should be built from a clean output directory.

---

# 22. Regression Prevention

Whenever a significant pitfall is fixed, add a regression check where practical.

Possible checks include:

- unit tests
- hash verification
- expected-byte checks
- translation validation
- font coverage checks
- archive parser checks
- clean-build CI
- smoke-test scripts

A documented pitfall is useful.

A documented pitfall plus an automated regression test is better.

---

# 23. Project-Specific Pitfalls

Add project-specific entries below this line.

Remove unused template text when adapting this document to a real project.

---

# 24. Final Pitfall Standard

This file should make it possible for a future contributor to answer:

- what looked correct but was actually wrong
- what caused crashes or corruption
- which tools or versions were unsafe
- which assumptions were disproven
- which resources must be changed together
- how to detect recurring failures
- how to avoid repeating previous research

Negative knowledge should be preserved as carefully as successful implementation details.


## 2026-10-18 已验证的项目陷阱

- Coalesced 长度大端但宽载荷 UTF-16LE；单凭 Xbox 字节序整体按 BE 解码会得到错误文本。回归测试 test_utf16_roundtrip_and_code_units。
- INT 后缀不是英语证明；当前 MC2UI.int 实际存在韩文。
- 候选中有 UnrealEd 编辑器字段，NewGame 命中不是启动菜单可见证据。
- 只加 gitignore 不会移除既有索引；本目录原无 .git，本轮新建索引并运行 check_repository，原件保留。
- 本机控制台默认 cp932，打印中文研究内容发生 UnicodeEncodeError；设置 PYTHONIOENCODING=utf-8，磁盘文件始终 UTF-8。原始读取记录不改成成功。

- 首次 git diff --check 发现 CRLF 与模板硬换行/TSV 空字段。索引通过 .gitattributes 归一 LF，Markdown 仅豁免 blank-at-eol，保留原有硬换行和空列；Python 文件尾多余空行已修复。默认 diff 检查随后重跑。

## 2026-10-18 字体推进中的已验证陷阱

- MCARTA bulk flag0x40对应LZX，不直接套通用UE3标志语义；原版resident Startup同一图集是raw0，独立font是LZX0x40。原始平铺字节hash一致，仍分别保留存储模式。
- Startup驻留Font.General_15，单改外部font.xxx不是完整补字方案。
- 24×24 BC3存储格不要求glyph指标高度24；本次保持23，避免改变字体全局最大高度。原字符/填充不得为了补字删除。
- 标题待机演示可进入村庄，看见HUD或启动进程不是受控游戏输入与资源绑定证明。未见KCK的尝试按未建立结果保留。
- 物理Esc会中止当前窗口控制工具，但用户明确它只表示退出游戏，不暂停工程；不把工具事件冒充用户暂停项目。
# Xenia launcher CI: Windows short TEMP paths (2026-10-18)

The initial launcher tests passed locally and on Linux but failed two path-string
assertions on Windows hosted runners. TEMP used `RUNNER~1`, while `Path.resolve()`
correctly recorded the long `runneradmin` path. The launcher behavior was correct;
the fixture compared noncanonical spellings. Canonicalize the fixture root before
constructing expectations. Keep full configuration and no-tuning checks unchanged.
Failed run: 39109395945, commit 6bd840d; do not report it as successful.

## Runtime controls: LZX, raw packages and font selection (2026-10-18)

Native decoder roundtrip is not game compatibility: original first-chunk no-op
stored/CAB re-encodes guest-faulted too. Alignment alone did not fix them. A raw
outer package needs package bit 0x02000000 cleared as well as compression flags
and chunk count. Derive the header field; do not blind-patch offset 21 on other
builds. General_15 and Subtitle append tests still omit Chinese, so do not assume
these are the warning's live font. See RUNTIME_TEXT_BINDING.md for controls and
remaining hypotheses. Movie playback after a guest fault is not a passing boot.

## Do not discard editor-named packages by filename

Default__Engine Tiny/Small FontName fields refer to MC2EditorResources, whose
three Korean Fonts were absent from the earlier three-package study. Cooked
MC2Engine.ini and Xe-MC2Engine.ini disagree on Tiny/Small; serialized defaults
are not proof of runtime priority. See FONT_REFERENCES.md.

## Fonts can be embedded in the main game script package

Do not limit a font search to font.xxx, Startup or editor resources. The actual
MC2Game.xxx class table also contains Font.General_15 plus 12 font_ui.Font
exports. Earlier geometry candidates did not cover this copy. Use the guarded
class inventory described in FONT_REFERENCES.md. NtCreateFile debug requests
identify candidates, not successful loads or actual draw selection. A raw
MC2Game control reached title/movie only; its warning compatibility is pending,
so the MC2Game geometry candidate was not deployed in that trial.

### Core.Component is not the root of the class hierarchy

A class walker may stop at Component when Core is absent, but must continue to
Object when Core is supplied. Otherwise the real Component CDO's Object
archetype fails a false class-compatibility check. Keep optional boundaries
explicit; reject malformed supplied definitions. Closing the CDO chain still
does not establish native initialization or the font selected during drawing.

### Multi-alias supplement restoration and raster drift

Controls in the supplement bundle retain original physical compressed bytes;
geometry probe controls are decompressed/raw. Do not interchange these meanings.
Backup-restoration equality does not demonstrate recovering an original compressed
first header chunk from the candidate alone. Raster dependency changes can alter
atlas pixels despite unchanged glyph count; the full expected supplemented
fingerprint is a deliberate guard. Never silently refresh it on mismatch.

### Windows short temp names can make a fault injector miss its target

The first multi-alias builder CI passed both Linux jobs but failed the Windows
readback-injection test: the builder canonicalized its output root, while the
injector compared an unresolved TemporaryDirectory name. RUNNER~1 versus
runneradmin identified the same directory with unequal path spellings. Compare
resolved identities in the injector and assert that exactly one read was
corrupted. An isolated junction-temp reproduction fails with the original test
and passes with the corrected test; production readback guards are not relaxed.

### Literal remap coverage is not a widget binding or display proof

A placeholder's characters are not its expanded runtime content. Exclude only
exact protected TOKEN matches, retain unknown syntax, and report dynamic coverage
as unverified. Explicitly mapped whitespace may have no pixels, but an empty
visible glyph is not sufficient coverage. Do not guess no-remap/direct-index,
non-BMP or fallback behavior. Keep every supplied font's failures, not just one
passing alias. A source-value UTF-8 hash is not a serialized UTF-16 range hash;
retain the separate whole-container hash and reject unknown source modes.

### Packaging must validate actual dependencies, not a producer's success flag

A font-bundle manifest can be stale, omitted or forged. Derive confined payload
paths from a trusted exact-hash plan, verify every candidate's complete bytes,
then independently check original/new Font identity/semantics and text coverage.
Recompute TOC changes from actual lengths, including text when variable-length;
do not reuse a font-only TOC blindly. Keep original compressed controls distinct
from raw geometry controls, and never call an incomplete candidate tree a game.

### Python JSON object equality is weaker than a typed metadata contract

False==0 and 1==1.0 make ordinary dict equality accept altered metadata types.
Independent candidate replay rejects duplicate JSON keys/non-finite constants
and uses strict canonical JSON,
while computing every resource/report value from trusted plans and actual bytes.
A self-consistent forged report hash is still not report truth. Historical
producer extra-input hashes are only declarations unless separately reopened;
without a trusted original manifest anchor, do not claim their original byte
identity. Candidate descendants must remain a closed regular-file set, not
junction/symlink shortcuts that happen to point at currently matching bytes.


### Do not skip editor-shaped fields just because a package is cooked for Xenon

The inspected 446/25 data-only ScriptStructs retain ScriptText/CppText/Line/TextPos
zero fields before script size/flags/defaults. A guessed console omission shifts
all later data. Also distinguish persistent ScriptStruct default records from
C++ initialization and effective instance memory. STYLE_ID has no own default
records but inherits Guid declarations/explicit parent defaults; missing is not
zero. Bool size0 means a header value, not a four-byte payload: the former
flattened bool offset was four bytes late and is now corrected. REA's general
binary opener did not admit UE3.xxx; repeated renaming/provider setup is not a
format decoder. Use the version/hash-locked reader and retain this boundary.


### Native parameter stubs are not the font-selection algorithm

UIComp_DrawString.SetFont/DisableCustomFont and the two style getters are declared native; their stored scripts only name parameters and terminate. NativeToken=0 does not identify a C++ implementation or prove no native behavior. Do not claim setters/flags/call order from names or these stubs. Functions also retain nonzero Line/TextPos and FriendlyName, unlike zero-valued data-only ScriptStruct fields. Five sibling non-native methods remain explicit unparsed records, not empty successful functions; do not silently extend native-stub size rules to general v446 bytecode.


### Preserve bytecode boundaries without inventing native behavior

The5 scripted siblings are now fully decoded only with explicit --include-scripted and hash-locked Core input. In these bodies short-circuit Skip spans include the enclosing EndFunctionParms, while default-value spans include EndParmValue; an off-by-one shifts the following statement. Core operator FriendlyName aliases differ from export leaves when the operator flag is set. Preserve Context raw skip/property-type fields without assigning an unverified VM meaning. Enum-typed Orientation does not prove runtime index bounds; source-like expressions and syntactic control edges are not executions. See SCRIPTED_UI_LAYOUT.md.


### XEX virtual images are not ordinary raw PE files or authenticated signatures

A XEX basic image retains PE raw pointers/size that do not describe its virtual bytes: .text raw0x2c8c00 is not code RVA0x2d0000; .reloc is partly absent. Do not feed those raw offsets into native-address claims. CBC chaining continues across stored basic extents; inserted zero bytes do not enter ciphertext or reset the IV. Exact inverse re-encryption and dual AES agreement do not verify RSA or stored digest semantics: direct plaintext-page SHA1 matched0/307 digest fields, so that hypothesis stays rejected. REA rejected the XEX format and the genuinely reconstructed PE architecture; no provider/architecture spoofing or native session was used.

Wide name searches also need actual NUL boundaries and big-endian alignment. A one-byte-shifted UTF16LE ASCII match is not a second string encoding. The full native-registration leads start with intUUIComp_, not the interior UIComp_ substring; four unique data pointers were found only after using full names. They are not yet verified native entry points. See NATIVE_IMAGE.md.


### Static native descriptor reconstruction is not runtime registration or defaults

The intUUIComp_DrawStringexec* cold rows contain zero descriptors until initialization; those zeros are not UI component defaults. Constant values must be traced through reused symbolic stack slots and sign-extended lis/addi address materialization, not the last textual register assignment. Reject unknown reads/calls/interior branches, DS update forms, duplicate/incomplete writes and nonzero adjustors in this profile. The lookup comparator-zero and row+4/stride12 shape is checked separately; its helper is not executed or assumed to compare strings a particular way.

Object-relative font words0xd8/0xe4 and PPC packed bit0x20000000 do not replace logical package tag offsets/BoolProperty0-or-1 headers. Paired setter/disable instruction chains support field-name deductions but do not prove constructor values, caller order, active font, complete struct layout or Chinese pixels. See NATIVE_BINDINGS.md.

### An override flag alone does not select a font; next-start is not an end

The checked overlay tests both bit0x20000000 and a nonzero pointer word before
writing output+0x20. Null bypass preserves the existing output even with the bit
set. Do not infer an effective Font from a setter/flag without this second guard.
Similarly, CE .pdata packed length—not the next listed start—declares function
extent. Real gaps occur after the initializer and getter helper. The overlay leaf
has no covering record; that absence neither removes its code nor extends the
preceding record over it. See NATIVE_STYLE_SELECTION.md for confidence levels.

### Keep class-name prefixes, initializer phases and object contexts distinct

The checked native registrations pass full-U-name address+2; do not generalize
that one code-unit adjustment into a resource-name normalization rule. A table
write with surrounding cleanup calls is not enough to name a default constructor.
The actual selected leaf callback windows do not write component font wordsD8/E4;
their silence is not zero-initialization evidence. Registration helper writes at
its own object-relativeD8/E4 belong to another object, not the component instance.
Pointer scans also find code addresses inside .pdata: restrict table candidates
to typed read-only .rdata rather than scoring isolated aligned matches. See
NATIVE_CLASS_TABLES.md for the separate static/semantic/runtime evidence planes.


### Git EOL rules do not canonicalize an already-written working file

Windows Path.write_text may create CRLF even when Git stores LF. A local plan
SHA can then pass local CLI checks but fail the documented command in a clean
checkout. Pin the exact shipped LF source bytes, write hash-bearing JSON with
write_bytes or explicit newline='\n', and test doc hashes against repository
plan bytes. Do not normalize arbitrary inputs inside a verifier or weaken exact
hash guards. Old raw-plan identity remains different; reports may legitimately
change only their plan_sha256 when the semantic plan is unchanged. See the
native probe byte-contract regressions and canonical CLI proof in build/.

### Do not promote a clear call or a Class metadata zero to an instance default

The same fill helper clears both a stack buffer and an allocation destination;
its target register/context matters. At the allocation destination call, r4 is
zero and r5 comes from metadata slot120, but additional initialization calls
occur before allocation returns. An intermediate zero does not establish a
callback-entry or rendered font value. Metadata result+11C is a direct callback
field, not the unrelated virtual slot11C in every table. Metadata's ownD8/E4
zeros belong to a different object. See OBJECT_INITIALIZATION.md; do not extend
zero runs over nonzero metadata fields such as14C=8.

### Coverage of a marker is not coverage of the investigated UI experiment

The retained Kick marker had valid byte/inverse/remap proofs but targeted another
record than the LogIn_NewGame warning's known MarkupString. Correct the active
source selector before extending engine research or calling the packet a warning
probe. A prefix edit can preserve the guarded original suffix without publishing
its full text. Do not count Unicode codepoints as UTF-16 units for astral text,
split recognized control tokens, or audit only inserted glyphs while ignoring
the retained body. Current Login prefix packets audit all39 literal codepoints;
old successful Kick manifests still fail against the newer trusted plans.
