## 第十二批海底洞窟与城镇尾段（2026-10-19）

新增INT144条，累计2,246条草稿、161项candidate；字幕新增27cue，累计93/315。
Ch02_Abazet已遍历276条：274条draft、2条纯标记保留；csm02四份字幕30cue已有draft。
范围限定与重建见 [BATCH_012_RESCUE](docs/BATCH_012_RESCUE.md)；本批不更新字库/TOC/可玩入口。

## 第十一批柯塔马雷与火之KAN（2026-10-19）

新增INT213条，累计2,102条草稿、154项candidate；字幕新增9cue，累计66/315。
城镇新增18条，两条纯标记不计已译；累计220条draft，索引遍历至221，重复key分别保留。
见 [BATCH_011_KOTAMARE](docs/BATCH_011_KOTAMARE.md)；仅离线回填，字库/TOC/可玩入口未更新。

## 第十批灾祸种与独立字幕（2026-10-19）

新增INT113条，累计1,889条草稿、146项candidate；城镇202/276条。另新增相邻字幕8cue，累计57/315。
一条新未知转义保留待查，不计已译；精华提取条件/换行及Quest:前缀保留。
见 [BATCH_010_CALAMITY](docs/BATCH_010_CALAMITY.md)；仅离线回填，不更新字库/TOC/可玩入口。

## 第九批强化与峡谷剧情（2026-10-19）

新增144条，累计1,776条INT草稿、143项candidate；当前CSMB02可提取剧情585条均有draft，
不包括独立动画字幕等资源，也不代表整章完成。城镇182/276条，营救任务及关联名称同步推进。
详见 [BATCH_009_CANYON](docs/BATCH_009_CANYON.md)；旧1,632条不变，本批不更新字库/TOC/可玩入口。

## 第八批军议与炸弹运送（2026-10-19）

新增131条，累计1,632条INT草稿、134项candidate；剧情接至CSMB02_41，城镇162/276条。
旧1,501条和字幕不变，任务混合key及QUEST:前缀保留；见 [BATCH_008_COUNCIL](docs/BATCH_008_COUNCIL.md)。
本批仅离线文本回填，不更新字库/TOC/可玩入口；验证推送核对后继续下一批。

## 第七批司令部与新命令（2026-10-19）

新增112条，累计1,501条INT草稿、131项candidate；剧情含CSMB02_38_1/2分支，城镇142/276条。
旧译1,389条保持不变，狩猎任务保留功能换行、QUEST%s前缀与占位符。
范围与重建见 [BATCH_007_ORDERS](docs/BATCH_007_ORDERS.md)，不更新字库/TOC/可玩入口；推送核对后直接接续。

## 连续推进与第六批（2026-10-19）

用户要求每批整理、验证、清理、提交推送并核对后直接继续，不等待反复确认；接续点见
[TRANSLATION_QUEUE](docs/TRANSLATION_QUEUE.md)。第六批新增272条，累计1,389条INT草稿、124项candidate。
范围和重建见 [BATCH_006_TEAM](docs/BATCH_006_TEAM.md)，本轮不更新字库/TOC/可玩入口。

## 第五批阿巴泽特到访（2026-10-19）

新增276条，累计1,117条INT草稿，102项candidate术语。包含6场剧情、城镇前84条NPC、
首任务21条及关联名称11条；选择分支和任务段落保留功能性换行。
重建与证据见 [BATCH_005_ABAZET](docs/BATCH_005_ABAZET.md)。本轮不更新字库/TOC/可玩入口。

## 第四批洞窟与海岸防卫（2026-10-19）

新增308条，累计841条INT草稿，75项candidate术语。上述Coalesced开场两章剧情427条均有draft，
对应NPC155/156条，异常反斜线1条继续保留。范围和重建见 [BATCH_004_ISLAND](docs/BATCH_004_ISLAND.md)。
本轮仍为文本离线回填；不生成ISO/整盘副本、不更新字库/TOC/可玩入口。

## 第三批开场剧情（2026-10-19）

新增217条开场/NPC/关联名称，累计533条草稿；59项术语仍为candidate。
构建、场景覆盖与回滚证据见 [BATCH_003_OPENING](docs/BATCH_003_OPENING.md)。
本轮只回填文本，不更新字库/TOC/可玩入口；继续沿用现有测试目录，不生成ISO或完整游戏副本。

## 共享译库与第二批草稿（2026-10-19）

用户决定暂缓双盘合一；不复制两套译文，也不新建整盘测试副本。
可复现工作区、独立字幕提取、统计与验证见 [SHARED_TRANSLATION_WORKFLOW](docs/SHARED_TRANSLATION_WORKFLOW.md)。
`translation-workflow.json` 显式组合既有262条与新增54条，不按文件名自动挑选“最新”。
双盘 Coalesced 输出316条一致草稿，另保留44份动画字幕目录及既有49条字幕译文。
本轮只完成文本资源离线回填，未更新字体/TOC/可玩入口；现有测试目录及其配置、存档、runs不变。

## 每轮收尾约定

- 普通翻译、字库、排版及资源修复只增量刷新现有测试目录，不逐轮生成 ISO 或完整游戏副本；需要额外整盘副本时先说明理由并征求用户同意。
- 结束前排查：执行与本轮改动相关的验证，检查差异、资源身份、入口依赖及仓库卫生；区分离线验证与真实游戏验收。
- 验证后清理：仅删除已确认可再生成、无入口依赖的临时产物和失败中间文件。先核实绝对路径及引用关系；不按目录名批量删除历史研究。
- 保留原始游戏/ISO、用户配置、存档、运行记录、当前测试包及其 manifest 引用资源，以及必要的基线、回滚和研究证据。
- 完成清理后提交并推送本轮源码/译文/文档，核对 HEAD 与远端及工作区状态；不提交完整游戏资源。
- 最终简报说明修改、验证、清理和推送结果；普通迭代沿用原一键入口。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](docs/TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## 显示修复与独立字幕资源（2026-10-19）

`display-fonts/route.json` 在七个字体别名上实际检查 alpha，而不只检查 remap；
同包生成四个带时间轴字幕 txt、262 条 Coalesced 回填和 TOC。新入口为 dist/MC2-display-repair-disc1。
完整构建命令和旧包失败/新包通过的针对性检查见 docs/DIALOGUE_DISPLAY_REPAIR.md。

## NPC、教程与菜单累计测试包（2026-10-19）

累计 231 条、三类字体七别名的新批次构建与原文对照入口见 [OPENING_BATCH_TEST](docs/OPENING_BATCH_TEST.md)。
新字形指标显式增长，不缩改译文；开发阶段仅离线构建，用户负责游戏内验收。

## 正式文本提取与首批回填（2026-10-19）

双盘原始 Coalesced 提取后，按 locales/zh-Hans/extraction-profile.json 固定 hash
导出 80 份本地目录；命令、标点规则和首批源锁定计划见 docs/TRANSLATION_PIPELINE.md。
首批容器回填不等于已生成可玩的新包，新增字符仍须重建字库和 TOC 并由用户验收。

## 正文空白后的新 Subtitle 测试入口（2026-10-19）

旧剧情样本已收到游戏内空白反馈。新增独立入口 `dist/MC2-story-subtitle-disc1/开始中文测试.cmd`，
原九句不变，补齐此前遗漏的 Subtitle 两别名；默认不装原生行宽补丁。
构建计划 `locales/zh-Hans/story-subtitle/route.json`；原候选保留作对照。
自动覆盖通过不等于画面恢复，详见 docs/STORY_DIALOGUE_SAMPLE.md 顶部更正。

## 真实剧情宽框样本（2026-10-19）

九条真实开场/NPC 对话与可编辑提取→回填流程已建立，详见 [STORY_DIALOGUE_SAMPLE](docs/STORY_DIALOGUE_SAMPLE.md)。
一键入口：`dist/MC2-story-test-disc1/开始中文测试.cmd`；同目录保留同中文无修复及原文对照。
仅离线自动验证，不启动游戏；标题警告保持原文，用户从新游戏进入开场剧情验收。

# 当前可执行流程（2026-10-18）

2026-10-19 原生强制折行宽度修复候选见 [WRAP_WIDTH_FIX](docs/WRAP_WIDTH_FIX.md)：
只补扣行起点，不改样本/字库/框体，不添加手动换行。
新入口 `dist/MC2-layout-fix-disc1/开始中文测试.cmd`；同目录有同中文资源、无修复的 A/B 对照。
新增显式 `--patch-bundle/--patch-manifest-sha256` 只在每次 run/storage/patches 下装配，原配置不变。

2026-10-19 扩展中文长句/标点/自动换行测试见 [TEXT_LAYOUT_PROBE](docs/TEXT_LAYOUT_PROBE.md)：
新入口 `dist/MC2-layout-test-disc1/开始中文测试.cmd`，旧两字入口保留。
源样本、自动收字/空位分配、显式字图扩高、构建/复核命令与用户验收步骤均在该文档。

Python 3.12+，核心工具/默认测试仅标准库；加密XEX还原的显式可选依赖另见下文。本次本地 Python 3.14.2。尚无汉化补丁构建命令。包表/字体只读解析和容器副本回写见 docs/UE3_PACKAGE_RESEARCH.md、docs/FONT_RESEARCH.md、docs/COALESCED_REBUILD.md；它们不等于完整补丁构建。

```powershell
python -m unittest discover -s tests -v
python tools/check_repository.py
python -m compileall -q tools tests
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --hash-image --output build/disc1.json --extract MC2Game/Localization/Coalesced.int --extract MC2Game/Localization/Coalesced.jpn --extract MC2Game/Localization/Coalesced.kor --extract MC2Game/Config/Xenon/Cooked/Coalesced.ini --extract-dir build/disc1-selected
```

Disc 2 同法指定独立输出及目录；首次解出后再次提取应使用新目录，工具拒绝覆盖。`--hash-files` 可为全部成员流式散列。版本、ISO SHA-256、XEX 身份见 docs/RESOURCE_SURVEY.md。

实际文本解析命令与 hash 见 docs/COALESCED_SURVEY.md；提取范围受 hash 和结构校验。现有 Coalesced 副本回写、字体候选和 TOC 大小更新工具见下文及对应研究文档；它们尚非可用汉化补丁，也没有 ISO 重封装。系列来源复现见 docs/SERIES_TERMS.md。

原件保持不变；派生资源在被忽略的 build/。最新约定为游戏测试全部由用户执行，开发阶段不自行启动模拟器或部署候选。未来中文验收应由用户在隔离副本中进行同场景前/后/回退录证。

## 字体使用方离线扫描

Font属性声明使用 `inspect_property_declarations.py --class Font --bind-structs`，可审计Array/Map引用、嵌套类型和local Next边界；不会解码容器值或计算native偏移。源hash、命令与opaque Map边界见 docs/FONT_DECLARATIONS.md。

新增显式 `font-metrics-measurement-path.json`，在13项initialized绑定后检查TextSize caller/helper/metric三窗口与常量。旧initialized计划输出不变，不解释执行指令或推断运行Font；命令与LF hash见 docs/TEXT_MEASUREMENT_PATH.md。

测量调查新增 `inspect_function_metadata.py --class ... --native-only` 与 `inspect_initialized_natives.py`；前三个Class的完整native-only报告生成方式、SHA及initialized row8计划见 docs/INITIALIZED_NATIVE_TABLES.md。它与既有cold row12 inspector分离，默认旧元数据输出不变，不调用目标代码。

新增第六个显式native计划 `references/probes/ui-style-reference-helper.json`，核对判定函数helper及三条class-name/tag参数链。旧五个计划不变；命令/计划LF hash见 docs/STYLE_REFERENCE_HELPER.md。工具仅静态读取，不调用目标函数。

native静态调查新增显式 `references/probes/ui-draw-string-selection-predicate.json`：在既有class-table证明后核验slot124完整判定函数，旧计划/CLI输出不变。命令和LF计划hash见 docs/STYLE_SELECTION_PREDICATE.md；不执行目标代码或游戏。

`inspect_ui_fonts.py --deep --audit-bindings` 现在同时输出匹配标签的 `owner_primary_style_audit`，保留 PrimaryStyle / DefaultStyleTag 及嵌套文本 CDO 的字体观察；原组件链计数不变。新默认字体观察会加入 namespace 指纹审计，可能扩大解码范围；完整证据与非运行边界见 docs/OWNER_PRIMARY_STYLE.md。默认573项合成回归通过。

继承/命名空间审计加 `--deep --audit-bindings`；双盘全 .xxx 类表扫描用 `tools/inventory_font_namespaces.py`。`tools/build_font_binding_probe.py` 按 references/probes/ 下 hash 锁定计划，一次构建三别名的 raw 对照、geometry 候选、独立反向检查及对应 TOC；只写全新隔离目录、不部署、不启动游戏。完整命令和证据边界见 docs/FONT_BINDING_AUDIT.md。

新增 `tools/inspect_ui_fonts.py --deep --text-token TOKEN`：在显式 hash 锁定的参考包间解析组件前缀、已知嵌套结构、STYLE_ID 和 UIStyle 状态表，输出静态字体候选路径。`tools/probe_ui_style_font.py` 在 raw 副本上构建同尺寸字体引用探针；不部署、不启动游戏。完整参数、原版/对照/候选 hash 与覆盖边界见 docs/UI_STYLE_GRAPH.md。

`tools/inspect_font_references.py --consumers` 枚举可解析 tagged 对象中的直接 Font/MultiFont ObjectProperty 引用，保留 import/export 身份、逻辑偏移与覆盖缺口。它与 `--inventory` / `--object` 互斥，不启动游戏、不修改资源。命令、62 包实测和组件前缀缺口见 docs/FONT_CONSUMERS.md。

## 最小补字原型（独立输出，未获游戏验收）

Xenia 测试必须基于用户提供的 `xenia/xenia-canary.config.toml`，不得静默替换为默认配置或覆盖画质、分辨率、时序及输入设置。`tools/launch_xenia.py` 保存逐字节配置快照，仅隔离 storage/content/cache/log；启动及加载核对见 [XENIA_TESTING](docs/XENIA_TESTING.md)。配置加载成功不代表中文显示通过。

可选依赖：`python -m pip install -r requirements-font.txt`。Noto 字体固定来源及 hash 在 references/font-sources.lock.json，字体原件只放本地 build/font-source。LZX 的本地构建、固定源码与许可见 docs/LZX_RESEARCH.md。

补字 CLI、hash 参数及两字计划见 docs/FONT_SUPPLEMENT.md；独立字体、Startup 与 MC2Game 驻留别名都应按锁定计划处理。补字输出只存 build，不覆盖原件。TOC 只更新明确验证的文件大小字段，见 docs/TOC_SIZE_REBUILD.md；它不证明所有运行索引均有效。四份候选文件的本地清单为 build/font-supplement/v2/deployment-plan.json，目前未部署中文试验。

## 三别名最小补字装配（2026-10-19）

`tools/build_font_supplement.py` 按 locales/zh-Hans/font-build-disc1.json 或 locales/zh-Hans/font-build-disc2.json一次构建三别名补字候选、该盘仅字体大小变更的 TOC、原始字节对照和独立备份恢复检查。完整命令、输入提取、依赖、schema 与恢复边界见 [FONT_BUNDLE_BUILD](docs/FONT_BUNDLE_BUILD.md)。要求全新隔离输出；不部署、不改文本、不运行游戏，不把两字技术候选当发布补丁。

## 文本候选与字体覆盖（2026-10-19）

通用 `tools/audit_text_font_coverage.py` 按原容器 hash、稳定 ID、源值 hash/原文和保护标记顺序验证修改计划，内存回写/反向还原后检查所有显式 Font 的字面字符 remap 与指标；只写新报告、不选运行字体。`locales/zh-Hans/text-probe.json` 已保存仅一条两字技术探针的源值 hash 计划，不需要私有 changes 文件；`build_coalesced.py` 可直接用同一计划构建独立文本副本。完整命令、双盘/负对照/逆向证据及边界见 [TEXT_FONT_COVERAGE](docs/TEXT_FONT_COVERAGE.md)。未开始批量翻译。

## 字体/文本/TOC最小候选装配（2026-10-19）

`tools/build_locale_candidate.py` 按 locales/zh-Hans/candidate-disc1.json / candidate-disc2.json 校验所有依赖真实字节，再一次生成原路径形状的5资源候选、原始对照和备份恢复检查。拒绝原件/字体输入目录内输出，不信任上游manifest成功标志，不启动或部署。命令、依赖、schema、双盘与整树复现证据见 [LOCALE_CANDIDATE](docs/LOCALE_CANDIDATE.md)。它是离线技术候选，不是完整游戏目录、安装包或发布补丁。

## 搬移候选的独立复核（2026-10-19）

`tools/verify_locale_candidate.py` 无需原游戏根目录或原字体bundle，只读候选内的已校验对照/候选/恢复文件及可信repo计划，独立重放Font、文本、TOC并比对metadata；不调用构建器、不信任成功布尔值。要求严格闭合文件集，拒绝多余文件/链接/错盘/伪报告。原manifest可信hash可显式锚定；不传时不会宣称原metadata字节身份已证明。完整命令和真实负对照见 [CANDIDATE_REVALIDATION](docs/CANDIDATE_REVALIDATION.md)。报告必须写在候选树之外，不部署、不启动游戏。

## 双盘差异报告（只读）

在两份完整哈希清单准备后，执行：

```powershell
python tools/compare_discs.py build/disc1-hashed.json build/disc2-hashed.json --output build/multidisc-research/disc-comparison.json
```

输出包含双方身份、逐文件 SHA256/大小/位置及四种分类，不执行整合。已有输出拒绝覆盖。未来整合→汉化回写的规划见 docs/MULTIDISC_RESEARCH.md；目前没有正式合盘构建命令，汉化可以独立推进。

## 原始通用规范（下列命令仅示例）

---

# Building

This document defines how to rebuild the localization project from a clean repository checkout plus user-supplied original game files.

The build process should be reproducible, documented, and independent from private local working directories or undocumented manual steps.

---

# 1. Supported Game Version

Document the exact supported game build here.

Include when applicable:

- game title
- platform
- region
- distribution or store version
- executable or ELF filename
- version number
- file size
- SHA-256
- important archive hashes

Example:

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

Binary patches must not silently modify unsupported or unknown versions.

---

# 2. Requirements

List all required tools and dependencies.

Examples:

- Python 3.x
- Visual Studio Build Tools
- CMake
- Ninja
- Pillow
- ffmpeg
- external archive tools
- original game files
- specific redistributable fonts

Do not assume dependencies are already installed.

Where practical, provide exact installation commands or version requirements.

Example:

```bash
python -m pip install -r requirements.txt
```

---

# 3. Original Game Files

Clearly list all original files that the user must provide.

Do not include copyrighted original game files in the repository unless redistribution is explicitly permitted.

Example:

```text
original/
  GAME.EXE
  DATA.PAK
```

Document where each file comes from and how its version is verified.

If the game requires files from multiple regions or releases, document each source separately.

---

# 4. Repository Preparation

A clean build should start from a fresh clone.

Example:

```bash
git clone <repository-url>
cd <repository-directory>
```

Do not require the user to copy undocumented private work directories into the repository.

If local configuration is necessary, provide a documented file such as:

```text
config.local.json
```

and include a safe template such as:

```text
config.example.json
```

Local-only configuration should normally be excluded through `.gitignore`.

---

# 5. Preferred Build Entry Point

The build process should expose one obvious entry point whenever practical.

Examples:

```bash
python build.py --locale <locale>
```

or:

```powershell
./build.ps1 -Locale <locale>
```

or:

```bash
cmake --build build
```

Avoid requiring contributors to manually run a long undocumented sequence of unrelated commands.

---

# 6. Recommended Build Pipeline

Where applicable, the build system should perform the following steps:

1. verify dependencies
2. verify original game files
3. extract source resources
4. import localization data
5. validate translations
6. collect required characters
7. generate fonts or glyph tables
8. patch executable or runtime code
9. rebuild archives or containers
10. verify rebuilt resources
11. assemble final output
12. generate checksums or manifests
13. package release files

Not every project needs every step.

The build pipeline should reflect the actual technical requirements of the game.

---

# 7. Version Verification

Before modifying original files, verify one or more of:

- SHA-256
- file size
- expected version metadata
- expected byte sequences
- archive identifiers

Example behavior:

```text
Expected:
GAME.EXE SHA-256 = ...

Found:
GAME.EXE SHA-256 = ...

Result:
Supported
```

If the version does not match, stop with a clear error message.

Do not silently continue on unknown binaries.

---

# 8. Build Output

Generated files should go into a dedicated output directory.

Preferred directories:

```text
build/
dist/
out/
```

Example:

```text
dist/
  <project-name>-<locale>/
```

Generated files should not be scattered across source directories.

Temporary intermediate files should be placed under a build directory and should normally be excluded from version control.

---

# 9. Validation

Before producing a usable or release build, validation should check as many of the following as applicable:

- unsupported original game version
- missing dependency
- missing input file
- invalid translation encoding
- unsupported characters
- missing glyphs
- placeholder mismatch
- control-code mismatch
- malformed markup
- fixed-slot overflow
- invalid string lengths
- duplicate IDs
- linked-string inconsistencies
- broken archive structure
- invalid offsets
- unexpected file sizes
- missing generated resources
- failed binary patches
- checksum mismatch

If a validation error can cause corruption or crashes, the build must stop.

Warnings may be used for non-fatal issues such as possible UI clipping.

---

# 10. Rebuilding From Scratch

A future developer should ideally be able to:

1. clone the repository
2. obtain the required original game files
3. install documented dependencies
4. place original files in the documented location
5. run the documented build command
6. obtain a functional localization build

The project should not depend on:

- old private build directories
- manually modified intermediate files
- deleted binaries
- undocumented local tools
- chat-only instructions
- one developer's filesystem layout

Any unavoidable manual requirement must be documented explicitly.

---

# 11. Locale Selection

If the project supports multiple locales, the build system should accept the locale as a parameter.

Preferred example:

```bash
python build.py --locale zh-CN
```

Potential future usage:

```bash
python build.py --locale zh-TW
python build.py --locale ja-JP
python build.py --locale ko-KR
```

Generic tooling should not assume one locale unless the game itself requires that limitation.

---

# 12. Dependency Management

Document all project dependencies.

Where practical, include standard dependency files such as:

```text
requirements.txt
pyproject.toml
CMakeLists.txt
vcpkg.json
package.json
```

Pin versions when reproducibility requires it.

If an external proprietary tool is required, document:

- tool name
- required version
- download source
- whether redistribution is allowed
- where the user should install or configure it

Do not bundle third-party tools without confirming redistribution rights.

---

# 13. Fonts

If the build requires external fonts, document:

- font name
- source
- license
- required style or weight
- expected file location
- fallback behavior

Prefer redistributable open fonts when practical.

Do not commit proprietary operating-system fonts merely because they are installed locally.

If the build uses a system font, document that dependency clearly.

---

# 14. Archive and Resource Tools

If the project depends on custom extraction or repacking tools, document whether they are:

- included in this repository
- built from source
- provided by an upstream project
- external dependencies

If a tool is custom, include enough documentation to rebuild or replace it.

Do not make the project depend on an unexplained executable with unknown provenance.

---

# 15. Binary Patching

Binary patching must be deterministic and defensive.

Patch tools should:

1. verify the target version
2. verify expected original bytes
3. patch only intended ranges
4. fail on mismatch
5. verify patched output

Where practical, generate a report such as:

```text
Patched file:
GAME.EXE

Verified version:
SHA-256 ...

Applied patches:
- text decoder
- glyph lookup
- line width calculation
```

Do not rely on undocumented manual hex editing for release builds.

---

# 16. Build Logs

Build output should clearly show:

- detected game version
- selected locale
- validation results
- generated character count
- generated files
- patch status
- archive rebuild status
- final output path

Errors should explain what failed and how the user can fix it.

Avoid vague failures such as:

```text
Build failed.
```

Prefer:

```text
Unsupported executable version.
Expected SHA-256: ...
Found SHA-256: ...
```

---

# 17. Release Build

Document a dedicated release build command when appropriate.

Example:

```bash
python build.py release --locale <locale>
```

A release build may additionally:

- clean previous output
- run strict validation
- build optimized binaries
- generate checksums
- generate manifests
- copy documentation
- assemble installation instructions
- create an archive

The exact process should be reproducible.

---

# 18. GitHub Release Packaging

The source repository should normally contain:

- source code
- translation data
- build scripts
- documentation
- patches
- reproducible assets

GitHub Releases may contain:

- ready-to-use localization packages
- installers
- prebuilt redistributable tools
- large generated files
- optional media subtitle packages

Do not use the repository root as a storage area for release archives.

---

# 19. Clean Build Test

Before a major release, perform a clean build test.

Recommended procedure:

1. create a fresh clone in a new directory
2. do not copy any old build output
3. provide only documented original game files
4. install only documented dependencies
5. run the documented build command
6. compare the result with the expected release output

This test helps detect hidden dependencies on the developer's local environment.

---

# 20. Reproducibility Notes

Perfect byte-for-byte reproducibility may not always be possible.

Possible causes include:

- archive timestamps
- compiler version differences
- non-deterministic compression
- external proprietary tools
- media encoders
- file ordering

If output is not byte-identical, document what level of reproducibility is expected.

Examples:

- byte-identical output
- functionally identical output
- identical translation resources but different archive timestamps

Do not claim deterministic output unless it has been verified.

---

# 21. Troubleshooting

Document known build failures and solutions here or in:

```text
docs/PITFALLS.md
```

Typical issues include:

- incorrect game version
- missing dependencies
- wrong file paths
- encoding failures
- font coverage failures
- archive rebuild errors
- compiler architecture mismatch
- missing external tools
- antivirus interference
- path length problems

Important troubleshooting knowledge should not remain only in chat history.

---

# 22. Project-Specific Build Notes

Use this section for project-specific information that does not belong in the generic sections above.

Examples:

- required regional assets
- special disc extraction steps
- emulator-specific testing requirements
- console image rebuilding
- source-port dependencies
- unusual asset conversion steps

Remove unused template notes when adapting this document to a real project.

---

# 23. Final Build Standard

A mature project should make it possible for another developer to rebuild the localization using:

- a clean repository checkout
- documented dependencies
- documented original game files
- documented build commands

The build process should not depend on the original author's memory or private local environment.

## Experimental runtime diagnostic copies (2026-10-18)

These commands require locally supplied originals and an explicitly built native
LZX decoder (see docs/FONT_RESEARCH.md). They are not a release pipeline:

```powershell
python tools/decompress_package.py INPUT_PACKAGE --sha256 ORIGINAL_SHA256 --lzx-library PATH_TO_DECODER --output NEW_PACKAGE --report NEW_REPORT
python tools/launch_xenia.py --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --game build/poc-game/disc1/default.xex --run-dir build/UNIQUE_RUN --keyboard-test-input --launch
```

`decompress_package.py` defaults to zero-padding to 32768 bytes, accepts only the
verified profile, preserves decoded object tables/payload and clears all three
compression states. `supplement_font.py --raw-atlas` is opt-in raw bulk output.
Neither command implies Chinese display or console compatibility. For table/TOC
updates and exact runtime boundaries see docs/RUNTIME_TEXT_BINDING.md. Keep all
originals and restore deployed resource copies before another control test.

### Existing-glyph binding probe

`tools/probe_font_mapping.py` is an opt-in same-size diagnostic for an existing
remap entry, not a font supplement or translation builder. Require the original
package hash, Font object path, codepoint and expected glyph. Never target an
unknown version. See docs/RUNTIME_TEXT_BINDING.md for the exact CLI shape and
negative-result boundaries; generated game packages remain local under build/.

### Duplicated geometry diagnostic

`probe_font_mapping.py --geometry` opts into same-size donor-metric copying in
both tagged/native records while preserving remap and texture bytes. Original
hash/mapping/donor bounds remain mandatory. Reports carry old/new patch bytes for
an independent inverse-copy check. See docs/FONT_REFERENCES.md; no diagnostic
candidate should be mistaken for Chinese display acceptance.


For embedded Font discovery, `tools/inspect_font_references.py --inventory`
accepts the same hash/decoder/output arguments as the default inspector and lists
Font/MultiFont class candidates without assuming a font-named package. It is
exclusive with `--object`. See docs/FONT_REFERENCES.md for the newly identified
MC2Game.xxx copy and its still-pending raw-package interactive control.


## UI ScriptStruct默认值与原生声明（2026-10-19）

`tools/inspect_struct_defaults.py` 只读解析明确hash锁定的446/25元数据、继承声明和持久默认值；`inspect_ui_fonts.py --deep --audit-bindings --audit-struct-defaults` 进一步按Class/outer/类型引用绑定renderer字段。Bool值偏移已修正为tag-header位置，非空payload位置；不修改游戏资源。完整命令、6定义/4绑定结果和原生运行边界见 docs/STRUCT_DEFAULTS.md。


## UI函数声明与native参数桩（2026-10-19）

`tools/inspect_function_metadata.py` 只读验证hash锁定的446/25 Function声明与精确native参数桩。`--object FULL_PATH`可重复；`--class UIComp_DrawString`清点该Class直属Function，不能与--object并用。全类23项中18项通过、5项非native脚本显式保留，返回exit1；定点11个native方法返回exit0。输出必须全新，复读后重查原包；不执行函数。命令/字段/测试及未验证边界见 docs/FUNCTION_METADATA.md。


## UI布局脚本的显式opt-in分析（2026-10-19）

在函数审计命令加`--include-scripted --reference-package Core <Core.xxx> <SHA256>`，按有界语法解析5个layout wrapper并绑定Core.Object操作符声明；全类由默认18通过/5未解析变为23通过/0未解析。输出含typed AST、source-like语句和纯语法控制边，既不执行也不部署。原/引用包hash与profile在加载可选decoder前全部校验。完整命令与Context skip、动态数组索引和native实现未验证边界见 docs/SCRIPTED_UI_LAYOUT.md。


## XEX原生映像只读还原（2026-10-19）

`tools/extract_xex_image.py` 支持hash锁定XEX2 none/basic profile，输出新分析映像/报告及可选原始容器逆向副本；不启动游戏、不补签、不写回原件。显式加密backend的可选版本在requirements-crypto.txt，默认测试仍仅标准库。双盘/双AES实现还原共同映像、原始XEX全字节恢复、PE虚拟布局及认证未验证边界见 docs/NATIVE_IMAGE.md。所有产物只放build/，不进入Git。


## 原生方法静态绑定与字段指令链（2026-10-19）

`tools/inspect_native_bindings.py` 用确切image/plan/native-report hash验证名称表、cold descriptor初始化及查找形状，不执行PPC代码。新VirtualImage只提供有界虚拟字节读取，不按PE raw pointer重映射。18项绑定、字体word/mask指令链、元数据依赖复现命令与运行未验证边界见 docs/NATIVE_BINDINGS.md；工具和20项合成回归仅标准库。

显式换用 references/probes/ui-draw-string-style-selection.json 可增加getter/双条件font overlay与CE/PPC .pdata声明范围验证；原plan输出保持兼容。完整hash/命令、两次bypass与leaf无.pdata条目的区别见 docs/NATIVE_STYLE_SELECTION.md。仍只读文件，不调用游戏函数。

进一步换用 references/probes/ui-draw-string-class-tables.json，显式启用完整U类名前缀→name+2参数→callback写入的只读table→slot128 getter关联，以及getter的双来源分支；见 docs/NATIVE_CLASS_TABLES.md。默认native/style计划保持原报告字节，不推断活动实例或未写字体字段的初值。

references/probes/ui-object-initialization.json 进一步启用metadata size/callback存储链、callback调用点和中间zero-fill调用的只读验证。区间模型只做整数几何，不运行PPC；clear之后仍有未验证初始化调用，不能将中间零值当有效字体默认值。hash/命令和合成验证见 docs/OBJECT_INITIALIZATION.md。

## 启动警告的源值锁定prefix探针

当前双盘candidate计划改用 locales/zh-Hans/text-probe-login.json，将原有两字技术marker用于真正关联两处警告MarkupString的LogIn_NewGame记录；不再把旧Kick候选当警告候选。新增通用sha256-utf8-prefix模式保留源suffix和控制码，不在locale数据中复制完整原文。构建/独立复核命令、精确作用域与未实测边界见 docs/LOGIN_PROBE.md；旧text-probe.json保留为历史独立诊断。
# Offline Font serialization inspection

`tools/inspect_font_serialization.py` consumes a hash-locked reconstructed image
and `references/probes/font-serialization.json`; see docs/FONT_SERIALIZATION.md
for exact invocation and evidence boundaries. Reports must be new. Default
self-authored tests need no game files, decoder, Capstone or target execution.
## Warning font-route candidate

See docs/WARNING_FONT_ROUTE_PROBE.md and tools/build_font_route_probe.py for
the combined five-Font/six-resource candidate, raw controls, explicit identity-
256 option, user-operated QA sequence and read-only full-byte replay. The normal
supplement path still rejects non-remapped Fonts without the exact opt-in.

The standalone `tools/verify_resource_phase.py` checks a selected packet phase
against an explicit resource directory using a mandatory trusted manifest SHA.
It needs neither the font file nor an LZX decoder. Exit0 means resource bytes
match only; exit1 gives mismatches/missing files and exit2 rejects invalid input.
The new JSON report must be outside both input directories. See the warning
probe document for the exact invocation and game-acceptance distinction.

For a player who wants double-click/drag-drop testing, use
`tools/prepare_oneclick_probe.py`. It makes two full independent copies and
publishes the two user-click CMD files only after validation. Preparation never
launches a game and never changes original resources/configuration. Exact
arguments, space needs and local-path dependency behavior are in
docs/WARNING_FONT_ROUTE_PROBE.md.
