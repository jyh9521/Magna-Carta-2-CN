## 子集字符需求不等于相等需求（阶段162）

demand-equivalence证据明确before2446/after2445、added=[]、removed=[23574]及旧字体需求为超集，不把文件名误读成字集相等。scope/route历史实验字段保留，workflow supersession说明当前修订；composition/comparison验证实际新计划和现有组件。旧目标锁取代只有已观察00_120_00一项，数字项此前未观察，本轮修复后作为新context；335理由注释与目标hash取代分开核。见[阶段162](PHASE_162_ABAZET_HOSTAGE_AND_CONSISTENCY.md)。

## scope所有权迁移仍使用原schema（阶段161）

Default明确keys从donor移到recipient时，entries同步按原容器顺序重分配；按id验证跨profile不重叠，禁止把重复key的不同occurrence合并。保护分隔不随非相关名称迁移丢失。新报告60处reason变化与source/target/邻序/策略的相等投影分开核；无新增通配字段，complete_section=false保持，未计划原文与已计划待修字面数字分别列出。见[阶段161](PHASE_161_EARLY_ISLAND_NPC_QUESTS.md)。

## context scope整合不改变schema（阶段160）

仍使用既有scopes[document,section,complete_section,keys,reason]，没有新增通配、范围或绕过字段。同profile同document/section明确keys取并集，complete_section保持false；原scope理由连接保留。报告context的reason因此可变，82项只注释取代与2项目标hash取代分表核对；其余身份/顺序/策略字段逐项比较。原始profile与计划由Git历史48a7214及阶段160隔离baseline恢复。见[阶段160](PHASE_160_PRONOUN_AND_ANIMAL_DRAMA.md)。

## source-order scene queue（2026-10-21）

schema1/kind=source-order-scene-context-queue，document、target_entries、source_order_sections[section,source_entries,planned_drafts,unplanned_original_ids]、scene_entries、planned_scene_entries和deferred_unplanned_sections；CLI另锁source/plan canonical、profiles与计划成员source/translation摘要。status仅preflight，translation_edits=0、人工/运行批准false。按实际rows顺序，不按section字符串排序。见PHASE_138_MARE_RESCUE_ORDER.md。

## context suite report（2026-10-21）

schema1/kind=read-only-line-context-suite-audit，继承单profile报告字段，增加profiles[profile_canonical_sha256,scope_count,context_entries]；显式1–16份，每份仍32 scopes/1000成员及源/计划/逐项hash合同。跨profile重复ID拒绝；context/protected_breaks按源序，policy全局唯一并重算pending，不累加每份全局计数。所有批准/运行字段仍false。见PHASE_134_BOUNDED_CONTEXT_SUITE.md。

## context observations profile（2026-10-20）

schema1/kind=source-locked-context-observations，resource/input_sha256/plan_canonical_sha256，human_finalized/runtime_layout_approved=false；scopes精确document/section、complete_section或keys及reason，entries按源顺序锁id/document/section/key/occurrence/source/translation SHA；protected_breaks锁功能分隔对照。report区分context pending和runtime pending，观察不构成换行批准/改译。见PHASE_132_OPENING_CONTEXT_REVIEW.md。

## refresh审计与还原凭据（2026-10-20）

read-only-refresh-journal-audit列journal_status及每项目标before/after/conflict，严格3..35项、三个已装元数据和局部candidate许可路径；缺失/第三态为冲突。hash-guarded-refresh-restore-receipt记录源journal SHA、root/backup、restored_files/already_before/all_journal_targets_before；新输出在根外，原journal不改写。只支持已知散列字节的显式逆恢复，无自动前滚或断电耐久声明。见PHASE_131_GUARDED_REFRESH_RECOVERY.md。

## 显式enrollment与refresh journal（2026-10-20）

enrollment schema1/kind=explicit-resource-enrollment，disc、prepared_sha256、old/new_packet_manifest_sha256及additions[path,original_sha256,original_size]全部锁定；game_rendering_verified=false。清单须严格等于new-old，32上限、不删除，新增raw与两live根皆原文。REFRESH.json含files[path,before,after]、root、status=prepared/committed/rolled-back、登记计划SHA和数量；原件相对路径备份，journal不等于自动断电恢复。见PHASE_130_EXPLICIT_RESOURCE_ENROLLMENT.md。

## 分盘raw comparison manifest（2026-10-20）

schema1 kind=offline-disc-locale-raw-comparison；继承128的来源/coverage/控制/资源合同，另含composition_manifest_sha256、comparison_plan_canonical_sha256、raw_package_outputs=true、raw_control_method=source-derived-uncompressed-fonts-original-text-disc-toc；各行raw_sha256/raw_size锁定raw-controls。raw-rollback-check是实际保留原件恢复，不是压缩逆算。新kind受只读inspector显式检查，未适配composition kind仍拒绝；不声称运行成功。见PHASE_129_DISC_RAW_COMPARISON.md。

## 独立分盘locale资源合成计划（2026-10-20）

工具schema1 kind=offline-disc-locale-composition，disc、game_rendering_verified=false及hash锁定font_route_plan/font_component/subtitle_plan/subtitle_component/text_plan，存在字面控制时须control_ledger。组件只选字体包与本盘字幕，不复制其INT/TOC；从本盘原TOC统一变化并逆验证。输出controls/candidate/rollback-check及字体像素、INT coverage、控制保留、组合TOC报告；all_noncontrol_literals_covered与all_literal_coverage_verified分开，未知TAB保持未核。此kind当前不是旧one-click packet，尚无raw-controls，不伪装成font-route或部署成功。见PHASE_128_DISC_LOCALE_COMPOSITION。

## 独立单盘字幕bundle计划（2026-10-20）

工具schema1 kind=offline-disc-subtitle-bundle，disc严格正整数、profile为path/SHA锁定ref、toc为path/SHA、game_rendering_verified=false。来源由profile.sources[disc].members闭合选取，禁止跨盘输入；每盘1..64字幕、每资源<=8MiB。候选只含字幕+本盘TOC，独立controls/candidate/rollback-check，manifest声明无INT/字体/投放。逐cue正逆重建及TOC逆size更新验证字节，不推断零自引用或未知TOC字段。见PHASE_127_DISC_SUBTITLE_BUNDLES。

## 源锁定字面控制保留ledger（2026-10-20）

工具schema1 kind=source-locked-literal-control-retention：resource/input_sha256/changes_canonical_sha256与entries；每entry仅id/source_sha256/translation_sha256/control_sequence/segment_nonempty。canonical是原changes dict按sort_keys=True,separators=(',',':') JSON UTF8后SHA256。控制序列使用精确TOKEN之外的保守category-C，segment bool数量为sequence+1，用于保持头/尾/连续位置形状，不声明字符offset或运行语义。1..16384项、1..4096 scalar/序列，禁止重复/额外/缺失和漂移。它不是游戏二进制字段或coverage豁免，见PHASE_126_LITERAL_CONTROL_RETENTION。

## 显式blank-advance计划字段（2026-10-20）

Verified / offline：supplement glyph可选layout="blank-advance"，限定BMP Zs separator且必须显式metric_width（1..cell width）。这是工具的候选元数据，不是新引擎字段；序列化仍append tagged/native/remap记录，在不重叠独立cell写透明BC3。完整cell解码alpha必须0。普通空白/控制仍拒绝，report单列explicit_layout_glyphs，不与ink字形混淆。详见PHASE_124_EXPLICIT_BLANK_ADVANCE。

## 显式宽度增长与BC3地址重排（2026-10-20）

Verified / offline：supplement计划可显式atlas_width=128..2048二次幂，并须raw_atlas；不缩小/不无变化/不多mip。宽变化时复用既有UEViewer派生Xenos块地址函数搬移原16字节块（含对齐padding），不重编码旧BC3，更新SizeX/SizeY、native mip宽高和raw bulk长度后重解析。原解码矩形逐行按新stride裁回比较；宽未变仍走旧grow_atlas字节兼容路径。
宽变报告original_tiled_bytes_retained=false及original_block_values_relocated=true，不混淆像素相同与物理前缀相同。原字形/未选remap与其余export保护不变；三族仅各1字真实包探针通过，非累计字库或运行验收。真实bulk offset必须绑定实际export serial_offset，合成测试传0应失败，不能放宽原offset检查。详见PHASE_122_ATLAS_AXIS_GROWTH。

## 跨容器同payload与补零尺寸反证（2026-10-20）

Verified / 仓库工具静态字节：extraction-profile八份源hash均匹配。两盘INT/MC2Game.int和JPN/MC2Game.jpn的去终止符宽payload均390字节/hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7，11候选相对偏移相同；JPN内容头偏移801126，INT895017。另四份INI/KOR零候选，不借JPN同key当修复原稿。
给每个0D 0A 00候选增加一个零字节的统一假设导致390+11=401奇数；这不是完整UTF16字节长度。只读工具只报告尺寸，不生成修复字节；偶数也不代表语义/边界正确。统一UTF16BE虽能解码，所获四个键仍有乱码前缀、section均空，不能认定端序翻转修复。原生产提取ID/值和所有held不变。
原名扫描仅覆盖selected中不大于32MiB的文件，发现两份INT容器自出现；不是压缩/完整包的引用分析，不证明孤立笑声不存在运行引用。详见PHASE_118_BOUNDARY_COMPARISON。

## MC2Game.int宽字符串边界只读观察（2026-10-20）

Verified / bytes：源INT容器179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c双盘相同；MC2Game.int宽内容长度字段偏移895017，payload895021，去终止符390字节，hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7。
通用审计报告11处0D 0A 00候选，payload相对偏移28/59/92/143/146/165/194/235/264/269/288，奇偶交替。容器按现行解析/序列化仍逐字节往返；这不证明内部INI语义正确。
Unverified：是否源生成器漏字节、不同换行序列混接、运行时如何读取；不能仅凭模式断言整段改用另一端序。模式亦可能来自合法U+0A0D，工具只观察，不修复/改ID/重划section。原三条提取值保持源hash不变；详见PHASE_117_REMAINDER_AUDIT。

## 库布邮件的主题/正文值（2026-10-19）

Verified / source：当前INT MC2QubeMail的E04_001–029共29个section，每节有对应的_Sub和_Con两字段；
源ID仍由resource/embedded_path/section/key/occurrence绑定，不按主题文字去重。正文有248个字面\n，
包括连续\n形成的空段落；E04_018_Sub尾随一个空格。batch-023按mail_subject/mail_body显式分类，
全部保留这些结构，不对邮件套用对白去硬换行策略。是否每行都具有游戏内功能及实际排版仍未验收，
因此此处是保守保留规则而非运行机制结论。源hash/数字/ASCII括号/方括号/段落布局逐值核对；详见BATCH_023_MAIL04.md。

## 共享译库与字幕catalog（2026-10-19）

`translation-workflow.json` schema_version1显式锁定提取profile、样式规则、术语及各batch
plan/review的路径和SHA256；同resource+容器hash共享，保留discs，不做同词面合并。
work catalog在现有selected-coalesced-catalog记录上增加work_queue；只叠加显式draft，
review分类ID集必须与plan完全相同；重复batch ID拒绝，不采用后写覆盖。

`subtitle-profile.json` schema_version1记录两盘path/size/sha256、完整Movies/*.txt成员及
已有timed-subtitle-text计划依赖锁。导出`timed-subtitle-catalog` schema_version1，
记录resource/input_sha256/discs与entries；每条有start/end/cue_class、原文/source_sha256、
translation/status/reviewer/text_kind。ID为`subtitle:`加JSON序列[resource,start,end]的SHA256。
时间、class、清屏及br不作为可翻译正文；源全文只在忽略的build输出。
详见 [SHARED_TRANSLATION_WORKFLOW](SHARED_TRANSLATION_WORKFLOW.md)。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## 显式透明字形修复、采样宽度和字幕格式（2026-10-19）

补字可选 replace_blank_codepoints：必须有旧映射且源字图实际 alpha 为零；旧 remap 的指定 value 改指附加 glyph，不添加重复 key。
可选逐 glyph metric_width 为 1..cell width，仅改变新增 glyph USize；越界 alpha 仍拒绝，旧 glyph 不变。
Coalesced 可选逐行 line_break_policy={source_count,target_count}，只豁免数量锁定的字面换行，其他 token 仍逐项有序相等。
开场 Movies/*.txt 实测为 UTF16LE BOM、header 1、CRLF 和成对 SYNC Start/P Class=KRCC，后半 cue 为清屏 nbsp。
subtitle_text.py 保留全部时序/class/清屏/br；公开 timed-subtitle-text schema1 仅保存资源/hash/起止时间/源值hash/译文。详见 DIALOGUE_DISPLAY_REPAIR.md。

## 较大字集和显式指标增长选项（2026-10-19）

补字 schema1 可选 glyph_limit（整数 1..2048，默认 128）；可选
metric_height_growth={original,candidate} 必须是严格整数且 original<candidate<=128，
candidate 必须等于 metric_height，original 必须匹配源 Font 全部字形的最大 VSize。
保留旧 tagged/native 字形、旧 remap 和非目标像素；透明 cell padding 不算可见指标。
未开启选项的旧行为不变，alpha 超出指标仍拒绝；见 OPENING_BATCH_TEST.md。

## Selected Coalesced catalog（2026-10-19）

`sample_catalog.py` 的 `selected-coalesced-catalog` schema1 记录容器 SHA/resource 和
非空选定 entries；每条保留原提取器字段及 embedded_path/section/key/occurrence/source_sha256。
只编辑 translation。导入逐项比对真实源行、严格 selector 类型和源值 hash，拒绝重复 ID、
坏 token 顺序、物理换行/NUL、空译文和未知版本，再调用现有容器回填器。
输出公开计划采用 sha256-utf8 模式，不嵌入完整原文。源文本 catalog 属本地 build 数据。

# File Formats

## Property container declaration tails (2026-10-19)

For the source-locked446/25 big-endian metadata profile, ArrayProperty adds one
int32 property-definition reference after the common declaration header;
MapProperty adds key/value int32 references. Font's map stores0/0 and remains
opaque. Nonnull types are exact local/owned Core property exports, not guessed
native element widths. These tails are declarations, not Array/Map value data.
See FONT_DECLARATIONS.md for scope, guards and complete Font source findings.

## Native metric glyph records versus stored Font records (2026-10-19)

The source-locked metric code computes a20-byte runtime record stride, reads
width/height-like words at+8/+C and a texture-index byte at+10. Existing Font
serialization still stores17 bytes per native glyph entry. The code's map-like
entry stride is8, next-link word+0/key-u16+4/value-u16+6. These observations do not
prove the serialized/native layout bridge or change the file writer. See
TEXT_MEASUREMENT_PATH.md for exact branches, hashes and limits.

## Initialized Font/Canvas native rows (2026-10-19)

For the hash-locked reconstructed PPC image, the Font/MultiFont/Canvas tables
store big-endian u32 name-address/code-address pairs (8 bytes), followed by an
8-byte zero sentinel. Their complete native scopes have2/1/10 rows. Function
native tokens live in the separate Engine declaration metadata, not an invented
third table word. This format is distinct from the earlier cold12-byte UI
descriptor profile. Coordinates are virtual-image addresses, not PE raw file
offsets; names/code words and .pdata-declared entries do not prove live dispatch.
See INITIALIZED_NATIVE_TABLES.md for source/plan/report hashes and reproduction.

## Cooked namespace metadata (2026-10-19)

For this profile, export flag bit0 (value1, EF_ForcedExport) identifies forced
exports. An outermost exported Package provides their uncooked namespace name
and GUID; standalone objects use the physical package's summary GUID and label.
Matching path/class/GUID is namespace-candidate evidence, not loaded-instance
precedence. Three General_15 representations have identical full normalized
glyph/remap/decoded-atlas data despite different table-local payload bytes.
See FONT_BINDING_AUDIT.md for hash-locked sources, complete-disc scope and limits.

## Verified 446/25 UI serialization (2026-10-18)

The component template header precedes NetIndex: class defaults use 4 bytes,
ordinary component instances 8, components under a class-default outer chain 16.
Flags are serialized LO u32 then HO u32; ClassDefaultObject is HO 0x200.
STYLE_ID is four tagged IntProperty A/B/C/D values. UIStyle's native tail holds
an int32 count followed by state/style-data int32-reference pairs. Full schema,
guards, offsets, fixed source references and coverage: UI_STYLE_GRAPH.md.

This document records reverse-engineered file formats used by the localization project.

Use this file for concrete binary or structured format documentation such as headers, offsets, field sizes, alignment, compression, checksums, string tables, pointer tables, and archive metadata.

High-level implementation notes belong in `TECHNICAL.md`.

---

# 1. Documentation Rules

For every documented format, include as much of the following as known:

- filename or extension
- purpose
- platform
- endianness
- magic
- version
- header size
- entry count
- offsets
- lengths
- alignment
- compression
- checksum behavior
- string encoding
- pointer tables
- filename tables
- secondary manifests
- unknown fields
- parser or builder implementation
- confidence level

Important claims should be classified as:

- Verified
- High-confidence deduction
- Unverified hypothesis

Do not assign meanings to unknown fields without evidence.

---

# 2. Format Entry Template

Use this template when documenting a new format.

```markdown
## FORMAT_NAME

**Purpose:**
Describe what the file stores.

**Platform:**
Describe where it is used.

**Status:**
Verified / High-confidence / Unverified

**Known files:**
- example.ext
- another.ext

**Endianness:**
Little-endian / Big-endian / Mixed / Unknown

**Encoding:**
ASCII / UTF-8 / UTF-16 / CP932 / CP936 / CP949 / Custom / Unknown

**Magic:**
`XX XX XX XX`

**Header size:**
`0x00`

**Alignment:**
4 bytes / 16 bytes / 0x800 bytes / Unknown

**Compression:**
None / algorithm / Unknown

**Structure:**

| Offset | Size | Type | Meaning | Status |
|---|---:|---|---|---|
| 0x00 | 4 | u32 | magic | Verified |
| 0x04 | 4 | u32 | entry count | Verified |

**Entry structure:**

| Offset | Size | Type | Meaning | Status |
|---|---:|---|---|---|
| 0x00 | 4 | u32 | data offset | Verified |
| 0x04 | 4 | u32 | data length | Verified |

**Notes:**
Additional behavior.

**Unknown fields:**
- offset 0x10
- offset 0x14

**Tools:**
- `tools/extract_format.py`
- `tools/build_format.py`
```

---

# 3. Integer Types

Use consistent notation.

Recommended types:

```text
u8
s8
u16
s16
u32
s32
u64
s64
f32
f64
char[n]
bytes[n]
```

If a field uses fixed-point representation, document it explicitly.

Examples:

```text
u16 8.8 fixed-point
s32 16.16 fixed-point
```

---

# 4. Endianness

Always document endianness where binary integer fields are involved.

Possible values:

- little-endian
- big-endian
- mixed-endian
- platform-native
- unknown

Do not infer endianness solely from the platform if the format has not been verified.

---

# 5. Offsets

For every offset, specify what it is relative to.

Possible bases include:

- file start
- current structure start
- current entry start
- data section start
- archive start
- decompressed block start

Example:

```text
string_offset:
u32 little-endian
relative to the beginning of the string table
```

Do not write only "offset" when the base is ambiguous.

---

# 6. Length Fields

Document what each length represents.

Possible meanings:

- byte length
- character count
- code-unit count
- glyph count
- compressed size
- decompressed size
- aligned size
- size including terminator
- size excluding terminator

Example:

```text
text_length:
number of encoded bytes
does not include trailing 0x00
```

This distinction is especially important for multibyte localization.

---

# 7. Alignment

Document alignment rules precisely.

Examples:

```text
entries aligned to 4 bytes
payloads aligned to 0x10 bytes
files aligned to 0x800-byte sectors
```

Record whether padding bytes are:

- zero
- 0xFF
- preserved from original
- ignored
- unknown

Incorrect alignment may break loading even when offsets appear valid.

---

# 8. String Storage

Document how strings are represented.

Possible forms:

- null-terminated
- fixed-width field
- offset + length
- string-table index
- pointer
- inline script token
- compressed string block
- glyph index stream

Record:

- encoding
- terminator
- length semantics
- alignment
- duplicate-string behavior
- whether empty strings are allowed

---

# 9. String Tables

If the format uses a string table, document:

- table start
- entry count
- indexing method
- duplicate handling
- encoding
- alignment
- offset base
- whether strings are sorted

Example:

```text
entry.name_offset
→ relative to string_table_start
→ null-terminated CP932
```

---

# 10. Pointer Tables

If pointer-like values exist, determine whether they are:

- file offsets
- virtual addresses
- relative offsets
- indexes
- sector numbers
- runtime pointers

Do not assume an integer that increases monotonically is a file offset without verification.

---

# 11. Record Arrays

For fixed-size record arrays, document:

- record size
- record count
- padding
- field order
- unused slots

Example:

```text
record_size = 0x20
record_count = header.entry_count
```

If the final record differs from the others, note it explicitly.

---

# 12. Variable-Length Records

For variable-length records, document how boundaries are determined.

Possible methods:

- length prefix
- next offset
- terminator
- sentinel value
- block table
- parser state machine

If malformed input causes unsafe reads, document the failure behavior.

---

# 13. Archive Formats

For archives, document at minimum:

- file count
- TOC location
- filename table
- data offsets
- file lengths
- alignment
- compression
- ordering
- checksums
- secondary metadata

Also determine whether the game relies on:

- an external index
- a size manifest
- hash table
- path database
- fixed file ordering

Do not assume rebuilding the primary archive alone is sufficient.

---

# 14. Secondary Metadata

Some formats use metadata outside the main container.

Examples:

- size manifests
- lookup indexes
- filename hashes
- dependency tables
- scene indexes

Document these relationships explicitly.

Example:

```text
DATA.AFS
↔ DATA_INDEX.BIN
```

If both must be updated together, record the dependency in `TECHNICAL.md` as well.

---

# 15. Compression

Document compression behavior.

Include:

- algorithm
- header
- block size
- compression flags
- decompressed size
- recompression requirements
- tool compatibility

If decompression is understood but compression is not, state that clearly.

Do not describe a format as "supported" if only extraction works.

---

# 16. Checksums

Document checksums and hashes.

Possible algorithms include:

- CRC16
- CRC32
- Adler-32
- MD5
- SHA variants
- custom hash
- rolling checksum

Record:

- covered byte range
- stored location
- byte order
- initialization value
- final XOR
- whether padding is included

If the algorithm is unknown, preserve the field and mark it unknown.

---

# 17. Filename Hashes

If filenames are hashed, document:

- normalization
- case handling
- slash direction
- encoding
- hash algorithm
- collision behavior

Example:

```text
input:
lowercase ASCII path with backslashes

algorithm:
FNV-1a 32-bit
```

Do not infer a hash algorithm from a small number of examples.

---

# 18. Compression Flags

If entries use flags, document each verified bit separately.

Example:

| Bit | Meaning | Status |
|---:|---|---|
| 0 | compressed | Verified |
| 1 | encrypted | Unverified |
| 2 | streaming | High-confidence |

Do not assign meanings to unknown bits.

---

# 19. Script Formats

For script-like formats, document:

- opcode size
- argument encoding
- string references
- jump targets
- labels
- control flow
- embedded text
- variable references

Translation tools must distinguish text from executable script logic.

Do not rewrite script tokens as natural-language text.

---

# 20. Font Formats

For font resources, document:

- texture format
- atlas dimensions
- glyph order
- character map
- width table
- metrics
- baseline
- line height
- fallback glyph
- maximum glyph count

If the font system spans multiple files, document the relationship.

---

# 21. Texture Formats

If localization requires editing textures, document:

- dimensions
- pixel format
- palette
- swizzling
- alpha format
- mipmaps
- container header
- alignment

If standard formats are embedded inside custom containers, note both layers.

---

# 22. Subtitle Formats

For subtitle resources, document:

- timing units
- time base
- line structure
- text encoding
- speaker metadata
- style metadata
- line-count limits

If timing is frame-based, document frame rate assumptions.

---

# 23. Video Containers

If localization requires video processing, document:

- container type
- video codec
- audio codec
- subtitle handling
- multiplexing behavior
- alignment
- platform-specific constraints

Do not confuse container format with codec format.

---

# 24. Audio Formats

If text references audio assets, document relevant metadata such as:

- event ID
- filename mapping
- index tables
- sample rate
- codec
- channel count

Do not translate internal audio identifiers unless verified safe.

---

# 25. Save Formats

If localization touches save-related data, document:

- text fields
- identifiers
- checksums
- version fields
- string encoding

Visible names may also be logic identifiers.

Do not modify save structures without understanding compatibility impact.

---

# 26. Executable Data Tables

If strings or font tables are embedded in executables, document:

- file offset
- RVA
- virtual address
- section name
- record size
- relocation behavior

Clearly distinguish:

```text
file offset
RVA
runtime virtual address
```

Do not mix these concepts.

---

# 27. Sector-Based Formats

Console formats may use sector-relative addressing.

Document:

- sector size
- base sector
- offset calculation
- padding
- filesystem relationship

Examples:

```text
sector size = 0x800
byte_offset = sector_index * 0x800
```

Verify rather than assume.

---

# 28. Platform Notes

Record platform-specific format behavior.

Examples:

- PS2 DMA alignment
- little-endian MIPS data
- Xbox sector alignment
- PC filesystem paths
- console disc image constraints

Keep platform assumptions separate from format facts.

---

# 29. Unknown Fields

Unknown fields should remain visible in documentation.

Example:

| Offset | Size | Meaning |
|---|---:|---|
| 0x10 | 4 | unknown |

Do not delete unknown fields from diagrams just because the current tooling preserves them.

Preserving unknown bytes may be necessary for safe rebuilding.

---

# 30. Rebuild Strategy

For each format, state whether the project uses:

- in-place patching
- full rebuild
- append-and-repoint
- block replacement
- archive reconstruction
- runtime override

Document why the chosen strategy is safe.

---

# 31. Round-Trip Testing

Where possible, test:

```text
original file
→ extract
→ rebuild without modification
→ compare
```

Possible outcomes:

- byte-identical
- structurally equivalent
- functionally equivalent
- not yet reproducible

Document the expected level.

A non-byte-identical rebuild may still be valid if differences are understood.

---

# 32. Sample Data

Use minimal samples where legally and practically appropriate.

Prefer:

- synthetic examples
- short byte sequences
- structure diagrams
- tiny excerpts

Avoid embedding substantial copyrighted game content.

---

# 33. Parser Safety

Custom parsers should validate:

- file size
- header bounds
- entry count sanity
- offsets within file
- lengths within bounds
- integer overflow
- truncated data
- malformed records

Do not trust game files blindly.

---

# 34. Builder Safety

Custom builders should validate:

- encoded string lengths
- alignment
- offset range
- checksum generation
- required metadata
- entry count
- output size

Fail clearly rather than generating ambiguous broken files.

---

# 35. Version Differences

If format behavior differs between game versions or regions, document each variant separately.

Example:

```text
US version:
record size = 0x20

JP version:
record size = 0x24
```

Do not merge incompatible variants into one undocumented assumption.

---

# 36. Tool Mapping

For each documented format, list the tools that operate on it.

Example:

```text
Format:
SCRIPT.BIN

Extractor:
tools/extract_script.py

Builder:
tools/build_script.py

Validator:
tools/validate_script.py
```

This makes technical documentation directly actionable.

---

# 37. Open Questions

Keep unresolved format questions visible.

Example:

```text
- Unknown meaning of header field 0x18.
- Entry flag bit 2 may control streaming.
- Final 4 bytes may be a checksum.
```

Do not erase unanswered questions when the current implementation works.

---

# 38. Project-Specific Formats

Add actual game-specific format documentation below this line.

Remove unused template examples when adapting the file to a real project.

---

# 39. Final File Format Standard

A mature format document should allow another developer to understand:

- how the file is structured
- which fields are verified
- how text is stored
- how offsets and lengths work
- how alignment works
- which metadata must be updated
- how to extract and rebuild the file
- which parts remain unknown

The goal is to preserve enough knowledge that future localization work does not require repeating the same binary-format reverse engineering.


## 2026-10-18 当前实测索引

XDVDFS / XEX2：见 RESOURCE_SURVEY.md；Coalesced：见 COALESCED_SURVEY.md。二者为本轮真实字节验证，前文模板示例不是本作格式。

## Font / Texture / Stored LZX 新增实测

Font tagged/native双份指标和remap见FONT_RESEARCH.md；Texture2D的MCARTA LZX flag0x40与resident raw0变体、Xbox BC3布局见TEXTURE_RESEARCH.md及FONT_SUPPLEMENT.md；stored LZX帧及第三方decoder验证见LZX_STORED_RESEARCH.md。均为固定源字节/本地工具验证，不代替游戏显示证明。


## Source-hash edit manifest (tool schema1, not a game binary format)

Coalesced change plans retain the literal source mode and add explicit
source_mode=sha256-utf8 with entries id/source_sha256/translation. The source hash
covers exact extracted value UTF-8 bytes; whole input_sha256 locks the serialized
container independently. No normalization or implicit mode fallback is permitted.
See TEXT_FONT_COVERAGE.md for fields, example workflow and verification limits.


## Offline candidate assembly metadata (tool schema1)

Candidate plan references exact font/text plan bytes plus every expected Font,
text and TOC binary hash. Output manifest uses relative resource/report paths
for candidate, original-control and backup-restored copies. It is not an
installer format or a game archive. See LOCALE_CANDIDATE.md for the contract and
which original/raster/runtime properties are actually checked.


## 446/25 ScriptStruct/UProperty/UEnum metadata

Native serialized metadata layouts, explicit persistent defaults, inherited Guid
schemas and scoped property references are documented in STRUCT_DEFAULTS.md.
This profile retains zero editor header fields and no script bytes. BoolProperty
size0 stores its value in the tag header: logical bool-word and empty-payload
offsets differ by4. These are logical serialization offsets, not runtime member
or native bool-bit offsets. Unknown layouts fail instead of scanning for tags.


## 446/25 native Function declarations and parameter stubs

See FUNCTION_METADATA.md for retained Line/TextPos/FriendlyName fields, native token/flags and exact `(NativeParm + i32 reference)* Nothing EndOfScript` stub recognition. This is a bounded native-only subset, not general bytecode or executable decompilation. UIComp_DrawString has18 recognized methods and5 explicit non-native unparsed records; unknown tokens are rejected. Shared declaration-chain validation retains all parameter/return types and checks owned reference order.


## Opt-in 446/25 scripted UI wrapper subset

SCRIPTED_UI_LAYOUT.md records the bounded grammar and exact5-body/736-byte/242-token result. StructMember retains property/struct references and copy/modification bytes; inherited owner ancestry is checked. Static arrays retain enum/type identity, not runtime index proof. Default/Skip spans and forward statement targets are checked; Context raw skip5 is preserved without VM-meaning inference. Core.Object numeric operator declarations are scoped/unique, not executable registrations. This is not a general VM or bytecode dialect claim.


## XEX2 none/basic offline image profile

NATIVE_IMAGE.md records the hash-locked dual-disc originals, exact basic stored/zero extents and common virtual-image identity. XEX/security fields are big-endian, reconstructed PE metadata little-endian and native code/data words big-endian. CBC spans the concatenated stored data; zero extents are inserted afterward. PE raw pointers/declared image size are annotations, not remapping instructions. Stored page extents are checked; RSA/page-digest authentication remains unverified.


## Hash-locked PPC native row12 cold-initializer profile

NATIVE_BINDINGS.md records18 rows (name pointer +8-byte descriptor), zero sentinel, typed Engine metadata identity, bounded constant/symbolic-stack def-use recovery and exact lookup structure. Descriptor code words and zero adjustment words are recovered without modifying image bytes. Native object-relative0xd8/0xe4 word operations and packed mask0x20000000 are distinct from serialized tagged properties; semantic field labels are high-confidence deductions, not complete struct/runtime layout proof.

## CE/PPC exception-directory and guarded style profile

NATIVE_STYLE_SELECTION.md records the PE little-endian directory3/virtual .pdata
contract and big-endian8-byte CE records. Packed prologue8/function-length22
fields count four-byte words; two raw flags are retained without unwind claims.
All44484 records are checked, not silently skipped by flag. Exact declared ends
and absent leaf entries remain distinct from next-start guesses and runtime code
coverage. The opt-in style profile verifies four code windows and the font
bit/nonzero-pointer guards before the unique output+0x20 store.

## Native class-name/table opt-in profile

NATIVE_CLASS_TABLES.md records full UTF-16BE U-prefixed names with the verified
name+2 call operand, bounded16-word registration/21-word leaf templates and
81-word .rdata table windows. Shared callback/table aliases preserve separate
class names. Slot128 points to a checked61-word getter; slot124's result selects
entry+E8 vs the pointer loaded at entry+28 plus174. These are static operands,
not serialized offsets or active runtime field values. Table window size and
leaf BLR boundaries do not imply full table/function extent.

## Object-initialization static contract

OBJECT_INITIALIZATION.md records metadata size+50/callback+11C word transfers,
checked save/base/constructor helpers, the metadata table's slot120 size getter,
selected wrapper/allocator sites, and the40-word zero-fill template. Its integer
geometry uses prefix/16-byte blocks/4-byte words/tail partitions, not memory or
CPU execution. Wrapper/allocation whole-function hashes and declared extents
are distinct from their partially checked instruction windows; later call
effects and callback-entry/render values remain unverified.

## Source-hash prefix Coalesced edits (schema1)

Explicit source_mode=sha256-utf8-prefix uses id/source_sha256,
source_prefix_codepoints/replacement/preserve_utf16_units and optional exact
selector(embedded_path/section/key/occurrence). The source hash covers the whole
unmodified UTF-8 value; replacement operates at Unicode codepoint boundaries,
with a separately typed UTF-16-unit length guard. Protected-token splits and
content/order changes fail. Resolved output retains the exact suffix; reports
record selector/unit counts/suffix hash, not original text. Literal/full-value
hash modes are unchanged for valid inputs. See LOGIN_PROBE.md.
# Selected Font serialization/native distinction (2026-10-19)

See FONT_SERIALIZATION.md for hash/structural guarded registration and six
selected PPC functions. Glyph element transfers4+4+4+4+1 bytes from offsets
0/4/8/C/10 while native array arithmetic uses20-byte stride. Map elements
transfer2+2 bytes from offsets4/6 while native arithmetic uses8-byte stride;
next-link at0 is not in the element transfer sequence. Word+6C precedes map,
word+68 follows it. Kerning/IsRemapped identity is high-confidence deduction,
not a verified archive-call/runtime bridge; container type refs remain opaque.
## Explicit 256-glyph identity-remap candidate

The opt-in supplement mode identity-256 retains the old glyph records and
introduces256 u16/u16 identity map pairs, then new supplement pairs. Tagged
IsRemapped and the final native word both become1. Required FNames must already
exist. This is a checked serialization transformation, not proof of a loaded
Font state or equivalence of the actual drawing path. See WARNING_FONT_ROUTE_PROBE.md.

## Explicit vertical atlas growth (2026-10-19)

Supplement plans may opt into `atlas_height`: an increasing power-of-two height
within 128..2048, unchanged width, one mip and explicit raw-atlas output only.
The writer retains existing tiled bytes, zero-extends aligned storage, checks
original decoded rows, and updates tagged SizeY, native mip height, bulk element
count, stored size and relocated inline offsets. All old glyph coordinates and
metrics stay unchanged. Sample plans remain bounded to 128 glyph additions;
placement validation still rejects any overlap with original BC3 blocks.
This serialization profile is offline verified, not runtime texture compatibility.
See TEXT_LAYOUT_PROBE.md for the 512x64 -> 512x128 candidate and replay commands.

## Per-run PPC runtime patch bundle (2026-10-19)

`runtime_patch.py` accepts a schema1 source/image-hash-locked plan with equal-size,
aligned, nonoverlapping expected/replacement writes and complete context-window
hashes. An explicit cave is checked against original XEX executable pages, .pdata
non-overlap and zero .text alignment padding. The bundle contains a standard Xenia
`.patch.toml` and a manifest pinning the game, emulator, image and patch file bytes;
original/modified complete images remain ignored local evidence, not source assets.
Launcher optional bundle/hash arguments are paired and explicit. Files are copied
into a new run's storage/patches, checked before launch, and never installed globally.
Module hash matching follows the pinned Xenia version; expected-byte validation
occurs at build time and source-XEX SHA is checked before each launch. See WRAP_WIDTH_FIX.md.
