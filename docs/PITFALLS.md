# Pitfalls

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
