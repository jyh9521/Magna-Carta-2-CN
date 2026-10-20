## 字面控制符保留证据与字体coverage分离（2026-10-20）

Verified / offline：audit_control_retention以源SHA/完整计划canonical SHA、entry源/译文SHA、有序category-C列表及segment占用形状核查原样保留。四条实际尾TAB的sequence[9]/shape[true,false]在双盘均匹配；缺失/移动/重排/hash漂移拒绝。仅证明保留，不证明语义，原font_coverage/audit分支不改；真实14,082 INT/七字体coverage仍exit1且唯一未核U+0009。报告font_coverage_verified/unknown_control_syntax_resolved/game_rendering_verified=false，路由和字幕16上限未放宽。详见PHASE_126_LITERAL_CONTROL_RETENTION。

## 累计字体七别名合成与控制门禁（2026-10-20）

Verified / offline：cumulative-font-route精确组合drawable+blank新增2390/2389/2390，绑定124完整候选semantic。既有raw route builder顺序编辑共享包后再核七字体；七字体2450非控制remap、2448非布局ink及U+3000 alpha0通过。十局部资源TOC逆变换、独立controls重放与rollback字节通过。TAB仍unverified，all_literal_coverage_verified=false；原262文本/四字幕路由不冒充14,082/315累计回填。当前测试目录/TOC未刷新，见PHASE_125_CUMULATIVE_FONT_ROUTE。

## 显式blank-advance与源空白证据（2026-10-20）

Verified / offline：glyph.layout=blank-advance仅接受Zs+正metric_width，生成零alpha且BC3解码整个cell严格透明，不借原SPACE/TAB remap，不替换已有映射。原普通空白/TAB/换行拒绝保持。三族U+3000候选27/20/32，原4997/2644/3648增4998/2645/3649，旧记录/像素保持。2451累计remap无缺、2448非布局字形均有ink，仅选定三族而非全部别名/游戏验收。源TAB矩形ink像素0/36/0、SPACE均0，不能推出运行TAB语义。SmallFont派生计划不得重复identity-256转换。源链/复现/门禁见PHASE_124_EXPLICIT_BLANK_ADVANCE。

## 显式新增字计数与累计drawable探针（2026-10-20）

Verified / offline：glyph_limit显式上限4096，默认128；prepare与writer共用常量，原几何/控制/空白/重复/保护检查保持。三族2389/2388/2389 drawable重建通过，旧记录/像素/未选remap保持；透明修复分别1/0/5个remap有意转向新记录，不宣称全部旧remap不变。原glyph count2608/256/1259变4997/2644/3648，最大新alpha误差18、视觉质量及运行仍未验证。仅三族选定源，不是七别名/完整字库；U+3000未解决、U+0009保持，未刷新TOC或测试资源。计划/源/Noto/output身份见drawable-demand-probes/manifest.json，复现与边界测试见PHASE_123_DRAWABLE_FONT_DEMAND。

## 显式宽度增长与BC3地址重排（2026-10-20）

Verified / offline：supplement计划可显式atlas_width=128..2048二次幂，并须raw_atlas；不缩小/不无变化/不多mip。宽变化时复用既有UEViewer派生Xenos块地址函数搬移原16字节块（含对齐padding），不重编码旧BC3，更新SizeX/SizeY、native mip宽高和raw bulk长度后重解析。原解码矩形逐行按新stride裁回比较；宽未变仍走旧grow_atlas字节兼容路径。
宽变报告original_tiled_bytes_retained=false及original_block_values_relocated=true，不混淆像素相同与物理前缀相同。原字形/未选remap与其余export保护不变；三族仅各1字真实包探针通过，非累计字库或运行验收。真实bulk offset必须绑定实际export serial_offset，合成测试传0应失败，不能放宽原offset检查。详见PHASE_122_ATLAS_AXIS_GROWTH。

## 源基线需求与普通字形生成布局门禁（2026-10-20）

Verified / offline：累计2451码点以三族原始基线核算，可绘制新增2389/2388/2389；未映射U+3000单列布局需求，不删除或伪画。SmallFont空remap实际是受支持的256-glyph identity conversion，不能当零覆盖。透明字修复1/0/5纳入新增集合，不重复计数。
通用prepare_text_sample.classify_font_demand提前区分可绘制/布局控制/BMP外；普通生成明确遇到U+3000即停止，无资源或计划目录输出。原glyph_limit2048和单atlas高度2048合同未放宽；三族当前宽度与模板在最大高度也分配失败，非引擎上限证明。详见PHASE_121_FONT_DEMAND_GATES。

## 累计译文字形覆盖缺口（2026-10-20）

Verified / offline：当前262条测试包hash/资源依赖完整，但不含累计14,082条译文。累计INT需要2446码点、加315字幕共2451；当前七别名在联合范围五个各缺1616 remap、字幕两个各缺1615，另U+0009是未核控制字面量。显式remap正面积不等于像素/运行选字验收。
既有覆盖工具累计范围返回exit1作为覆盖门禁，非解析异常exit2；未刷新资源，也不把未知tab删掉或绘成可见glyph。详见PHASE_120_COVERAGE_READINESS；补字/像素/TOC/独立回滚验证后方可按原hash保护增量流程继续。

## 跨容器同payload与补零尺寸反证（2026-10-20）

Verified / 仓库工具静态字节：extraction-profile八份源hash均匹配。两盘INT/MC2Game.int和JPN/MC2Game.jpn的去终止符宽payload均390字节/hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7，11候选相对偏移相同；JPN内容头偏移801126，INT895017。另四份INI/KOR零候选，不借JPN同key当修复原稿。
给每个0D 0A 00候选增加一个零字节的统一假设导致390+11=401奇数；这不是完整UTF16字节长度。只读工具只报告尺寸，不生成修复字节；偶数也不代表语义/边界正确。统一UTF16BE虽能解码，所获四个键仍有乱码前缀、section均空，不能认定端序翻转修复。原生产提取ID/值和所有held不变。
原名扫描仅覆盖selected中不大于32MiB的文件，发现两份INT容器自出现；不是压缩/完整包的引用分析，不证明孤立笑声不存在运行引用。详见PHASE_118_BOUNDARY_COMPARISON。

## MC2Game.int宽字符串边界只读观察（2026-10-20）

Verified / bytes：源INT容器179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c双盘相同；MC2Game.int宽内容长度字段偏移895017，payload895021，去终止符390字节，hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7。
通用审计报告11处0D 0A 00候选，payload相对偏移28/59/92/143/146/165/194/235/264/269/288，奇偶交替。容器按现行解析/序列化仍逐字节往返；这不证明内部INI语义正确。
Unverified：是否源生成器漏字节、不同换行序列混接、运行时如何读取；不能仅凭模式断言整段改用另一端序。模式亦可能来自合法U+0A0D，工具只观察，不修复/改ID/重划section。原三条提取值保持源hash不变；详见PHASE_117_REMAINDER_AUDIT。

## 第三批剧情回填（2026-10-19）

**Verified / offline：** 217条新增与316条既有译文组合为533条，双盘源容器回填相同；
逐条检查键位顺序、数字、换行策略及NPC重复key的occurrence。未知转义条目保留原值，
INT/JPN同剧情key实测错位，不做跨容器机械对齐。详见 docs/BATCH_003_OPENING.md。
新增字集尚未构建字体/TOC，不表示本轮游戏显示验收完成。

## 双盘共享译库与独立字幕（2026-10-19）

**Verified / offline：** 八份源容器重验后导出80份共享catalog，共35,901条候选，
原两盘合计71,802条；316条累计INT草稿双盘重建hash相同，17,860条其余原值不变，
独立副本回滚到原hash。完整ISO hash验证后提取44份独有动画字幕、315cue，保留49条已有draft。
**Unverified / runtime：** 新增54条菜单/属性未重新构建本轮字体/TOC或验收画面。
用户已决定暂缓合盘；具体构建、来源和覆盖边界见 docs/SHARED_TRANSLATION_WORKFLOW.md。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](docs/TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## 映射存在不等于标点可见（2026-10-19）

旧 EngineMedium_Subtitle 的 U+FF1F / U+2026 remap 目标 alpha 像素数均为 0；
U+00B7 和 U+2014 亦有透明映射。新 font_ink.py 检查解码像素，显式空白字形重映射不改旧 glyph/非目标 remap。
新 glyph metric_width 把可见采样宽度和 BC3 cell 分离，降低标点后的透明横向占位。
两张截图的标点/换行不是字符串检查能排除的问题；证据、SAMI 字幕格式和候选入口见 docs/DIALOGUE_DISPLAY_REPAIR.md。

## 扩展收字与显式指标增长（2026-10-19）

本批 673 个不同字面字符驱动三类字体补字。生成器保留默认 128 字上限，
新增显式 glyph_limit（最多 2048）和原高度锁定的 metric_height_growth。
General_15 新字指标 23→25、SmallFont 16→18、Subtitle 29 不变；旧字指标不改，
新增字图/TOC/覆盖与原像素保护均离线校验，运行行距与裁切待测。见 docs/OPENING_BATCH_TEST.md。

## 剧情正文空白反馈与 Subtitle 覆盖（2026-10-19）

旧版本两种字体覆盖未包含 EngineMedium_Subtitle。用户有/无行宽补丁同场景正文均空白；
这不支持把行宽修复当作空白的必要条件。新增 Subtitle 两别名 source/hash/namespace/语义锁定计划，
仅补 101 字、同一文本，无新扩图；完整证据边界见 docs/STORY_DIALOGUE_SAMPLE.md。

## 真实剧情样本绑定与往返（2026-10-19）

详见 docs/STORY_DIALOGUE_SAMPLE.md。MC2Game 的 Balloon/YesNoBal Dialogue 模板引用
`MC2CSMB.CSMB00_10.voc_csmb_0010_04`，六状态序列化字体候选为 General_15；
模板引用不等于已执行剧情或已测活动宽度。九句原文提取→catalog→hash 计划→回填→
重新提取、独立逆向还原通过；与标题警告互不覆盖。

# 当前技术结论（2026-10-18）

- **Verified（2026-10-19，声明/序列化类型）**：Engine.Font五个本地属性现完整盘点；Characters/Textures的local inner分别绑定FontCharacter完整schema/Texture2D Class，CharRemap的两个类型ref确为null、保持opaque。未从Next顺序计算native偏移或改写Map类型；见 docs/FONT_DECLARATIONS.md。

- **Verified / High-confidence deduction（2026-10-19）**：Canvas.TextSize尾部38-word、47-word helper与122-word call-free metric窗口完整模板通过；word+68两模式、u16读取、native stride20及fallback7F已核实。Font字段名称为高置信推断，serialized/native桥接和绘制等价未证明；不改变SmallFont mode-unverified覆盖状态。见 docs/TEXT_MEASUREMENT_PATH.md。

- **Verified（2026-10-19，静态表与元数据）**：Font/MultiFont/Canvas三张preinitialized row8表共13个code指针与完整native声明、sentinel和精确pdata入口关联；Canvas22个Function header中10 native/12脚本单列，保留464/470等索引，不套用cold row12。尚非绘制/测量实现证明。见 docs/INITIALIZED_NATIVE_TABLES.md。

- **Verified / High-confidence deduction（2026-10-19）**：style-reference helper的90-word代码、三种完整UIStyle类名与DefaultTextStyle/ImageStyle/ComboStyle字面tag参数链已核实；class-based fallback为高置信推断，不证明实际类返回值、callee保存或序列化/native布局。见 docs/STYLE_REFERENCE_HELPER.md。

- **Verified（2026-10-19，静态代码）**：四个组件类表 slot124 均指向0x826a8e70，新增36-word完整模板校验其+104 word门、四word OR门、helper调用和五条条件边；已补齐静态表项到判定函数的关联，未证明运行dispatch或序列化字段/native布局对应。见 docs/STYLE_SELECTION_PREDICATE.md。

- **Verified（2026-10-19，离线序列化证据）**：警告标签 PrimaryStyle 的 CDO 平面经 DefaultComboStyle 六状态/嵌套文本默认对象保留 EngineFonts.SmallFont；Engine/Startup 两份候选完整指纹相等。它与已有 General_15 组件链并列，不合并字段、不选择有效字体，也未证明 native owner 指针对应。见 docs/OWNER_PRIMARY_STYLE.md。

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


## Native class-prefix and static table association (2026-10-19)

See docs/NATIVE_CLASS_TABLES.md for four full native class-name/registration operands, three leaf table initializers and the slot128 getter's two source-base branches. Static class-associated target identity is now checked with the new opt-in profile; active vptrs, allocator/constructor defaults and external helper effects remain unverified. In particular, those leaves do not write font wordsD8/E4.


## Constructor metadata and intermediate clear (2026-10-19)

See docs/OBJECT_INITIALIZATION.md for the checked metadata size/callback chain, selected callback invocation and zero-fill geometry. The small metadata chain now verifies its own argument preservation rather than assuming external helpers preserve those registers. Allocator/post-callback helpers still have unverified effects; an intermediate clear is not a component font default or runtime drawing value.


## Warning probe scope correction (2026-10-19)

See docs/LOGIN_PROBE.md: the previous valid Kick diagnostic was unrelated to the investigated LogIn_NewGame labels. Active disc candidate plans now use a selector/source-hash guarded prefix edit on the warning record, preserve its exact suffix/tokens and revalidate all39 literals against all three Font aliases. This corrects experiment scope without changing native/font conclusions or running a game. Native property/default core0x823b0f98 remains a retained offline lead.
# Font serialization research

See docs/FONT_SERIALIZATION.md: explicit UFont/UMultiFont registration operands
and callbacks link bounded slot34 windows to six complete static templates.
Native glyph/map strides20/8 differ from transferred disk widths17/4. Native
6C/68 order is observed; property identity and archive/helper return contracts
remain separate confidence levels. Existing parser/coverage rules are unchanged.

## 中文布局样本推进（2026-10-19）

后续用户截图确认窄标题弹窗长句自动折行但前两行左溢、末行居中。
静态发现826c8e50强制分割漏扣行起点，普通分支826c8ca0会扣；
新增运行时修复候选、原始/修改/逆向指令回放与宽框非折行对照，见 docs/WRAP_WIDTH_FIX.md。
用户强调游戏内剧情框比此弹窗宽，故剧情宽框保持独立未验收状态。

用户截图已确认 Disc1 标题警告中两字探针实际可见；未区分两种同时补字的字体路线。
扩展样本与通用显式单 mip 字图增高的字节/像素保护见 docs/TEXT_LAYOUT_PROBE.md。
布局、扩图运行兼容与自动断行仍等待扩展样本的用户游戏验收，不从静态指纹推断。
