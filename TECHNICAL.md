# 当前技术结论（2026-10-18）

- **Verified / High-confidence deduction（2026-10-19）**：18个native静态描述符与Engine声明一致；SetFont/DisableCustomFont配对指令的0xe4 word及20000000 mask和0xd8写入已核实，DrawFont/覆盖位语义为高置信推断；构造/运行字体仍未证明。见 docs/NATIVE_BINDINGS.md。

- **Verified（2026-10-19）**：双盘XEX由两个AES backend分别还原同一20119552字节PPCBE虚拟映像，各自物理逆向副本完整匹配原XEX。代码页/PE注释已区分，认证和实际native字体路径未证明；见 docs/NATIVE_IMAGE.md。

- **Verified（2026-10-19）**：显式脚本模式将UIComp_DrawString全类审计推进至23/23；5个布局wrapper的736字节/242 token、字段/继承Struct、参数与跳转已完整解析。Core.Object操作符声明身份已核实，native实现及Context skip的VM含义未证明；见 docs/SCRIPTED_UI_LAYOUT.md。

- **Verified（2026-10-19）**：UIComp_DrawString直属23个Function中18个native声明只有NativeParm/Nothing/EndOfScript参数桩，NativeToken均0；SetFont、DisableCustomFont和两个样式getter的类型/返回声明已核实，但原生实现和有效字体仍未证明。另5个非native脚本显式未解析，见 docs/FUNCTION_METADATA.md。

- **Verified（2026-10-19）**：6个UI ScriptStruct定义/继承schema和4个renderer字段绑定通过；包内bOverrideDrawFont明确为0、DrawFont=null，Bool实际header偏移修正。枚举槽1的存储名为UIALIGN_Center，非运行绘制证明。见 docs/STRUCT_DEFAULTS.md。

- **Verified（2026-10-19）**：双盘搬移候选独立复核通过，5资源/18成员每盘按可信计划重新解析/回放，未调用装配构建器。实际伪候选hash/伪报告hash/多余文件/错盘/junction负对照均失败；不证明运行或显示，见 docs/CANDIDATE_REVALIDATION.md。

- **Verified（2026-10-19）**：双盘字体/文本/TOC候选依赖装配通过，5资源/盘及10份原始备份恢复均逐字节匹配；D1重复装配18个文件全hash相同。错盘/候选损坏在发布目录前失败。不信任上游成功标志，仍不证明运行绑定，见 docs/LOCALE_CANDIDATE.md。

- **Verified（2026-10-19）**：源值 UTF-8 hash 计划复现双盘相同两字文本候选，正反回写逐字节一致；全部显式 Font 的字面 remap/指标覆盖与负对照可复现。非运行绑定或显示证明，见 docs/TEXT_FONT_COVERAGE.md。

- **Verified（2026-10-19）**：三别名最小补字通用装配入口已在双盘复现全部独立构建候选 hash，并验证六份原始物理字节备份恢复；只写新目录，不部署或启动游戏。见 docs/FONT_BUNDLE_BUILD.md。

- **Verified（2026-10-19）**：完整双盘 4145 个 .xxx 的资源 hash/包表通过；每盘三份 canonical Font.General_15 候选，共用已核验 namespace GUID。三份完整字体/六图集标准化指纹相同；运行时胜出及覆盖语义未推断，见 docs/FONT_BINDING_AUDIT.md。

- **Verified**：组件与嵌套样式读取器在 62 包中解析 16279 个已选 UI 对象（分类缺口另列）；两个启动警告标签经静态 ID/六状态链指向 Startup_int 的 General_15。109 个 UIStyle/614 个 StateMap 记录结构通过；见 docs/UI_STYLE_GRAPH.md。此结论补齐序列化主链，不证明运行时绑定。

- **Verified**：双盘 XDVDFS 目录及 XEX2 身份，见 docs/RESOURCE_SURVEY.md。
- **Verified**：8 个 Coalesced 文件结构、混合端序、原字节往返及 INI 物理行提取，见 docs/COALESCED_SURVEY.md。
- **Verified**：启动登录提示的 INT 文本已由历史可见 TST 标记绑定，见 docs/RUNTIME_TEXT_BINDING.md；该结论不证明字体绑定。
- **Verified**：离线直接字体使用方扫描覆盖 62 个已有请求日志选中的包，发现 59 条顶层 ObjectProperty 字体引用，见 docs/FONT_CONSUMERS.md。组件/嵌套样式仍有明示缺口。
- **Unverified hypothesis**：启动提示的有效字体及字体副本选择尚未确定；资源名、静态引用和文件请求不等于绘制证据。

工具独立迁移与旧研究版本见 NOTICE.md。没有迁入 ReXGlue、SDK 或运行时。已实现受 hash 保护的文本副本回写、TOC 大小更新及字体候选构建，尚未验证中文显示，尚无发布补丁。游戏测试由用户进行；后续自主工作继续离线分析与自动化。

## 原始通用技术规范（示例不代表已验证）

---

# Technical Notes

This document records technical findings, reverse-engineering results, implementation details, and unresolved technical questions for the localization project.

The purpose is to preserve knowledge so future contributors do not need to rediscover the same behavior from scratch.

---

# 1. Evidence Classification

Important technical claims should be classified as one of:

- Verified
- High-confidence deduction
- Unverified hypothesis

Do not present speculation as established fact.

When possible, include the evidence used to reach a conclusion.

Examples:

```text
Verified:
Changing byte 0x1234 from 0x15 to 0x2B increases the accepted input length.

High-confidence deduction:
Field 0x18 appears to store the string byte length because all observed entries match.

Unverified hypothesis:
Control code $D04 may select a speaker portrait.
```

---

# 2. Supported Game Build

Record the exact analyzed version.

Include when applicable:

```text
Game:
Platform:
Region:
Distribution:
Version:
Executable:
File size:
SHA-256:
```

Any documented address, offset, binary patch, or file structure should be assumed valid only for the tested versions unless otherwise verified.

---

# 3. Text Resource Map

Document every known location that contains user-visible text.

Example:

| Resource | Purpose | Encoding | Editable | Notes |
|---|---|---|---|---|
| UI.DAT | menus | CP932 | yes | fixed slots |
| SCRIPT.BIN | dialogue | custom | yes | offset table |
| GAME.EXE | system text | ASCII | patch | hard-coded |

Include:

- menus
- dialogue
- subtitles
- item names
- descriptions
- tutorials
- names
- system messages
- credits
- hard-coded strings

Do not assume all visible text comes from the same source.

---

# 4. File Format Overview

For each custom format, document:

- filename or extension
- magic
- header structure
- entry count
- pointer tables
- string tables
- length fields
- alignment
- compression
- checksums
- indexes
- unknown fields

Detailed structures should be moved to:

```text
docs/FILE_FORMATS.md
```

Use this file for high-level relationships and implementation notes.

---

# 5. Text Encoding

Document the actual runtime encoding.

Possible cases include:

- ASCII
- UTF-8
- UTF-16
- Shift-JIS / CP932
- GBK / CP936
- CP949
- custom multibyte encoding
- glyph-index encoding
- mixed encoding

Record:

- byte ranges
- lead-byte rules
- trail-byte rules
- terminators
- invalid sequence behavior
- control-code interaction
- fallback behavior

If decoding occurs in executable code, document the relevant function or patch point.

---

# 6. String Storage

Determine how each string is stored.

Possible forms:

- null-terminated
- fixed-slot
- offset + length
- pointer table
- record structure
- compressed block
- script token stream
- executable constant

Document whether the stored length represents:

- bytes
- characters
- code units
- glyphs

Also note whether the length includes:

- null terminator
- control codes
- padding
- headers

---

# 7. Text Extraction

Document how source text is extracted.

Include:

- tool name
- source files
- parsing rules
- output format
- stable IDs
- ordering guarantees
- duplicate handling

If extraction requires heuristics, describe them.

If some strings cannot currently be extracted automatically, list them explicitly.

---

# 8. Text Reinsertion

Document how translated text is written back.

Include:

- target resource
- encoding conversion
- offset recalculation
- length recalculation
- pointer updates
- checksum updates
- archive rebuilding
- fixed-slot handling
- overflow behavior

If reinsertion is not fully reversible, explain the limitation.

---

# 9. Control Codes

Document known control codes.

Example table:

| Code | Meaning | Status |
|---|---|---|
| `$n` | line break | Verified |
| `$D04` | unknown | Unverified |
| `{0}` | format placeholder | Verified |

Record whether control codes:

- consume display width
- affect line count
- change speaker
- change color
- trigger animation
- select portrait
- insert variables

Unknown codes should remain preserved.

---

# 10. Font System

Document the font implementation.

Investigate:

- font file format
- texture format
- atlas layout
- glyph order
- character map
- glyph dimensions
- advance width
- kerning
- baseline
- line height
- fallback
- missing-glyph behavior
- proportional vs fixed-width behavior

If the font system uses multiple files, document their relationship.

Example:

```text
font texture
+ glyph map
+ width table
+ renderer logic
```

Do not assume one component is sufficient.

---

# 11. Glyph Mapping

Document how characters map to glyphs.

Possible methods:

- direct byte index
- code page lookup
- Unicode table
- custom character table
- two-byte lookup
- hash table
- executable mapping function

Record:

- input code
- lookup process
- glyph index
- fallback behavior

If custom mappings are introduced by the localization, document the format.

---

# 12. Font Metrics

Document how text width is calculated.

Possible data includes:

- advance width
- left bearing
- right bearing
- kerning
- fixed cell width
- scaling factor

Record whether width is stored as:

- integer pixels
- fixed-point value
- normalized value
- texture-relative value

Incorrect metrics can cause:

- clipping
- overlap
- wrong alignment
- broken wrapping
- oversized dialogs

---

# 13. Text Rendering Pipeline

Describe the rendering pipeline as far as known.

Example:

```text
resource string
→ decoder
→ control-code parser
→ glyph lookup
→ metrics lookup
→ layout
→ vertex generation
→ renderer
```

If the localization hooks or replaces part of this pipeline, document exactly where.

Include:

- function names if known
- module names
- vtable entries
- RVA or file offsets where useful
- calling convention
- input/output expectations

Only record addresses for verified game versions.

---

# 14. UI Layout

Document text-layout constraints.

Examples:

- fixed-width boxes
- hard-coded pixel widths
- menu row height
- subtitle region
- maximum lines
- logical resolution
- physical resolution scaling
- alignment rules
- clipping regions

Note any mismatch between:

- logical coordinates
- actual resolution
- font pixel size
- renderer scale

---

# 15. Binary Patches

For every executable patch, document:

- target file
- supported hash/version
- offset or RVA
- original bytes
- replacement bytes
- purpose
- validation rule
- failure behavior

Example:

```text
Target:
GAME.EXE

Offset:
0x00123456

Original:
15 00 00 00

Replacement:
2B 00 00 00

Purpose:
Increase maximum text input length.
```

Patch tools must verify expected original bytes before writing.

---

# 16. Runtime Hooks

If the project uses runtime hooking, document:

- proxy DLL strategy
- import redirection
- function hook
- vtable hook
- trampoline
- patch location
- loader behavior

Record:

- target function
- reason for hook
- expected call flow
- thread-safety concerns
- initialization order
- compatibility risks

---

# 17. Archive Formats

Document all relevant archive/container formats.

Examples:

- AFS
- POD
- VPP
- RES
- PAK
- custom container

Record:

- header
- file table
- offsets
- lengths
- alignment
- compression
- checksums
- filename table
- manifests
- secondary metadata

Do not assume archive TOC data is the only metadata the engine uses.

---

# 18. Secondary Manifests

Some games store duplicated file-size or index data outside the primary archive table.

Document any such files.

Examples:

- size manifests
- file indexes
- path tables
- hash tables
- lookup databases

Failure to update secondary metadata may cause:

- truncated reads
- out-of-bounds reads
- missing resources
- crashes

---

# 19. Linked Resources

Document resources that must be updated together.

Examples:

```text
item name
pickup message
inventory name
document title
scene reference
```

or:

```text
base character name
prefixed character name
abbreviated character name
```

If changing one without another breaks logic, record the dependency explicitly.

---

# 20. Hard-Coded Strings

Maintain a list of known hard-coded strings.

Possible locations:

- EXE
- ELF
- DLL
- scripts
- compiled UI data
- resource metadata
- shader constants

Document:

- location
- encoding
- length limit
- patch method
- whether resizing is safe

Hard-coded strings should not be assumed to participate in the normal translation pipeline.

---

# 21. Save Data and Identifiers

Determine whether visible strings are also used as internal identifiers.

Do not translate identifiers that affect:

- save loading
- quest state
- inventory keys
- script references
- network protocol
- resource lookup

Document cases where display text and logic identifiers share storage.

---

# 22. Script Logic Risks

Some text resources may contain executable script data or branching identifiers.

Document:

- commands
- labels
- jump targets
- variable names
- condition tokens
- function names

Do not translate script logic tokens.

If source text and logic are mixed in one file, extraction tools should separate them safely.

---

# 23. Compression

Document compression used by localization-relevant resources.

Record:

- algorithm
- header
- decompression tool
- recompression requirements
- alignment
- size limits

If exact recompression is not possible, document acceptable differences.

---

# 24. Checksums and Hashes

Document integrity checks such as:

- CRC32
- MD5
- SHA variants
- custom checksums
- hash tables

Record:

- what data is covered
- where the checksum is stored
- how it is recalculated
- whether the engine verifies it

---

# 25. File Alignment

Document alignment requirements.

Examples:

```text
4-byte
16-byte
2048-byte sector
0x800-byte block
```

Incorrect alignment can break resource loading even if offsets appear correct.

---

# 26. Platform-Specific Notes

Record platform-specific behavior.

Possible platforms:

- Windows
- Linux
- PS2
- PS3
- PSP
- Xbox
- Switch
- other consoles

Examples:

- endianness
- executable format
- filesystem case sensitivity
- sector layout
- emulator behavior
- platform font APIs

Do not assume behavior from one platform applies to another.

---

# 27. Emulator and Runtime Testing

If emulators or compatibility layers are used, record:

- emulator name
- tested version
- renderer/backend
- known compatibility differences
- debugging features used

Examples:

- PCSX2
- RPCS3
- Wine
- Proton

Do not confuse emulator-specific bugs with game-engine bugs without verification.

---

# 28. Known Failures

Record reproducible technical failures.

Examples:

- crash on long translated string
- missing glyph
- archive read failure
- font metrics corruption
- save incompatibility
- broken subtitle timing
- invalid pointer table
- unsupported game build

Detailed troubleshooting history should go in:

```text
docs/PITFALLS.md
```

---

# 29. Failed Approaches

Preserve meaningful failed experiments.

For each failed approach, record:

- goal
- method
- observed result
- why it failed
- whether the conclusion is verified

Example:

```text
Attempt:
Replace only the font texture.

Result:
Characters displayed, but layout was incorrect.

Conclusion:
The game uses a separate width table.
```

Failed research may save future contributors significant time.

---

# 30. Open Questions

Maintain unresolved technical questions.

Example:

```text
- Unknown meaning of field 0x18 in SCRIPT.BIN.
- Control code $D04 may be speaker-related.
- Width table may use fixed-point values.
```

Do not remove unresolved questions simply because the current patch works.

---

# 31. Upstream Research

Record external technical work used by the project.

Include:

- project name
- author
- URL
- commit/tag/release
- reused components
- independently verified findings
- license

Do not present upstream discoveries as original work.

---

# 32. Tool Inventory

Maintain a list of technical tools used by the project.

Example:

| Tool | Purpose | Source |
|---|---|---|
| extractor | text extraction | project |
| packer | archive rebuild | upstream |
| font builder | glyph atlas | project |
| disassembler | binary analysis | external |

Document proprietary dependencies separately.

---

# 33. Test Cases

Maintain minimal technical test cases where practical.

Useful cases include:

- ASCII-only string
- multibyte string
- punctuation
- long string
- line break
- placeholder
- control code
- unsupported character
- fixed-slot boundary
- archive replacement

These help detect regressions.

---

# 34. Regression Testing

When technical changes affect rendering, archives, encoding, or patching, retest previously working cases.

At minimum, verify:

- game boots
- menus render
- dialogue renders
- saves load
- scene transitions work
- patched resources load
- no new missing glyphs
- no new validation errors

---

# 35. Documentation Update Rule

When a verified technical discovery changes, update this document or the relevant specialized document in the same change whenever practical.

Do not leave obsolete technical claims in documentation.

---

# 36. Final Technical Standard

A mature technical implementation should allow future contributors to understand:

- where text lives
- how it is encoded
- how it is rendered
- how fonts work
- how archives are rebuilt
- how binaries are patched
- which resources are linked
- which assumptions are verified
- which questions remain unresolved

The goal is to preserve enough technical knowledge that future localization work can build on the project rather than repeat the same reverse engineering.


## Native style getter/overlay follow-up (2026-10-19)

See docs/NATIVE_STYLE_SELECTION.md for the two-guard font word overlay, shared virtual slot/call-site association, and CE/PPC metadata-declared extents. Persistent UICombinedStyleData declarations do not recover native offsets or effective state. Constructor/base-style/copy helper semantics and active rendering remain unverified.
