## 第十一批柯塔马雷与火之KAN（2026-10-19）

新增INT213条，累计2,102条草稿、154项candidate；字幕新增9cue，累计66/315。
城镇新增18条，两条纯标记不计已译；累计220条draft，索引遍历至221，重复key分别保留。
见 [BATCH_011_KOTAMARE](BATCH_011_KOTAMARE.md)；仅离线回填，字库/TOC/可玩入口未更新。

## 第十批灾祸种与独立字幕（2026-10-19）

新增INT113条，累计1,889条草稿、146项candidate；城镇202/276条。另新增相邻字幕8cue，累计57/315。
一条新未知转义保留待查，不计已译；精华提取条件/换行及Quest:前缀保留。
见 [BATCH_010_CALAMITY](BATCH_010_CALAMITY.md)；仅离线回填，不更新字库/TOC/可玩入口。

## 第九批强化与峡谷剧情（2026-10-19）

新增144条，累计1,776条INT草稿、143项candidate；当前CSMB02可提取剧情585条均有draft，
不包括独立动画字幕等资源，也不代表整章完成。城镇182/276条，营救任务及关联名称同步推进。
详见 [BATCH_009_CANYON](BATCH_009_CANYON.md)；旧1,632条不变，本批不更新字库/TOC/可玩入口。

## 第八批军议与炸弹运送（2026-10-19）

新增131条，累计1,632条INT草稿、134项candidate；剧情接至CSMB02_41，城镇162/276条。
旧1,501条和字幕不变，任务混合key及QUEST:前缀保留；见 [BATCH_008_COUNCIL](BATCH_008_COUNCIL.md)。
本批仅离线文本回填，不更新字库/TOC/可玩入口；验证推送核对后继续下一批。

## 第七批司令部与新命令（2026-10-19）

新增112条，累计1,501条INT草稿、131项candidate；剧情含CSMB02_38_1/2分支，城镇142/276条。
旧译1,389条保持不变，狩猎任务保留功能换行、QUEST%s前缀与占位符。
范围与重建见 [BATCH_007_ORDERS](BATCH_007_ORDERS.md)，不更新字库/TOC/可玩入口；推送核对后直接接续。

## 第六批未完成游戏显示验收（2026-10-19）

新增272条，累计1,389条INT草稿，仅离线回填，字库/TOC/可玩包未更新。
城镇NPC122/276条已译，124项术语仍为candidate；不把机制说明静态校验当游戏实测。
三条奖励/任务/选择换行保留，原1,117条不变，旧未知转义1条继续待查。见 BATCH_006_TEAM.md。

## 第五批未完成游戏显示验收（2026-10-19）

新增276条，累计1,117条INT草稿，仅离线回填，未更新字库/TOC/可玩包。
城镇NPC仅前84/276条已译，不表示整城完成；102项术语均待审核。选择与任务换行保留，画面仍待验收。
旧“给库布的信”UI标签保留待专项校对，本批未覆盖；旧未知转义1条继续保留原文。
详见 [BATCH_005_ABAZET](BATCH_005_ABAZET.md)。

## 第四批未完成游戏显示验收（2026-10-19）

新增308条，累计841条INT草稿，只完成文本离线回填，尚未更新增量字库/TOC/可玩包。
Coalesced开场两章427条剧情及155条NPC均有draft，另有1条异常转义保留；不代表动画字幕等均完成。
75项术语仍为candidate，后续需校对及游戏内排版验收；现有入口/配置/存档/runs保持不变。
详见 [BATCH_004_ISLAND](BATCH_004_ISLAND.md)。

## 第三批未完成游戏显示验收（2026-10-19）

新增217条开场/NPC/关联名称仅离线回填，累计533条；尚未按本轮新增字集更新字体/TOC/可玩包。
59项术语仍是candidate，长对白与名称排版待用户游戏验收。现有测试入口、存档与配置未改。
Ch00_1/00_101_00含未核验`\\항상`，已保留原文并列入held_entries；不得把它直接猜成换行。
详见 [BATCH_003_OPENING](BATCH_003_OPENING.md)。

## 共享译库第二批仅离线回填（2026-10-19）

`batch-002.json`的54条商店/武器类型/属性草稿已与既有262条组合验证，
但尚未重建本轮增量字库/TOC或刷新可玩包；现有测试入口内容不变。
45项术语均为candidate，尤其香器及连环攻防仍待上下文/画面确认。
INT主线外的JPN/KOR、xxx内嵌与图片文字仍需覆盖审计；315条独立字幕cue尚有266条未译。
详见 [SHARED_TRANSLATION_WORKFLOW](SHARED_TRANSLATION_WORKFLOW.md)。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## 用户确认旧包显示缺陷；新候选待画面验收（2026-10-19）

**Verified failure / High：** 用户截图确认旧包问号消失、标点附近空隙，以及余宽充分时提前换行。
**Fixed offline / runtime pending：** 新包修复透明字形映射，按实际 ink 调整新增字形宽度；66 条对白显式去除继承硬断行。
启动提示及49条开场字幕已加入独立候选，真实字幕读取、自然换行及三类2048高字图兼容仍待用户实测。
新入口 dist/MC2-display-repair-disc1/开始中文测试.cmd；完整验收清单见 DIALOGUE_DISPLAY_REPAIR.md。

## 新 NPC/教程/菜单包待验收（2026-10-19）

**Open / Medium：** dist/MC2-opening-batch-disc1 是累计 231 条的独立候选，
三类字体重新收字；新最大高度可能影响行距和裁切，未取得本批游戏画面验收。
标题警告、未纳入菜单、其他章节及 Disc2 仍是原文；使用 candidate 术语，不宣称译名定稿。
一键入口、原文对照和八项测试清单见 OPENING_BATCH_TEST.md。

## 最新：旧剧情样本正文空白，新增 Subtitle 候选待测（2026-10-19）

用户确认有/无行宽修复都空白；姓名和 A 按钮可见。旧样本游戏验收未通过。
新增 Subtitle 两别名覆盖 101 个缺字，原九句和 General_15/SmallFont 不变；
入口 dist/MC2-story-subtitle-disc1/开始中文测试.cmd，默认不加载行宽补丁。
它是针对已确认覆盖遗漏的新候选，运行字体及画面恢复仍待同场景验证，见 STORY_DIALOGUE_SAMPLE.md。

## 真实剧情宽框仍待用户验收（2026-10-19）

九条开场/NPC 样本和一键中文/无修复/原文入口已准备；详见 STORY_DIALOGUE_SAMPLE.md。
自动往返、字库覆盖、字节恢复和受控行宽模型不是游戏通过证据。
本次 General_15 512×256、SmallFont 256×512 扩图兼容、实际对话布局、NPC 触发、
字体动态覆盖尚待用户截图；隔离存储不自动继承旧存档，测试请从新游戏开始。
其余剧情/过场 Subtitle/Disc2 未由九句样本覆盖；样本之后出现原文属预期。

# Known Issues

This document records known user-visible limitations, compatibility problems, incomplete areas, and unresolved defects in the localization project.

Use this file for issues that affect players, testers, or release quality.

Use `docs/PITFALLS.md` for technical traps, failed approaches, and development lessons.

---

# 1. Issue Classification

Classify issues using one of these statuses:

- Open
- Investigating
- Workaround available
- Partially fixed
- Fixed in development
- Fixed in release
- Won't fix
- Upstream issue
- Emulator-specific
- Version-specific

Also classify severity when useful:

- Critical
- High
- Medium
- Low
- Cosmetic

Do not overstate severity.

---

# 2. Issue Entry Template

Use the following template for each known issue.

```markdown
## Short issue title

**Status:** Open  
**Severity:** Medium  
**Affected versions:**  
**Affected platforms:**  
**Affected locales:**  

**Symptoms:**
Describe what the player sees.

**Trigger:**
Describe how to reproduce the issue.

**Expected behavior:**
Describe what should happen.

**Actual behavior:**
Describe what actually happens.

**Workaround:**
Describe any temporary workaround.

**Technical notes:**
Briefly describe the suspected or verified cause.

**Related files:**
List relevant files, resources, tools, or code.

**Tracking:**
Link an issue, commit, or release if available.
```

---

# 3. Player-Visible Text Issues

Record issues such as:

- untranslated strings
- mistranslated strings
- duplicate translations
- missing subtitles
- wrong speaker text
- incorrect names
- inconsistent terminology
- untranslated debug text
- text using the wrong locale

If the issue is only a translation-quality concern and not a technical defect, state that clearly.

---

# 4. Missing Glyphs

Record any characters that:

- render as boxes
- render as question marks
- disappear
- display the wrong glyph
- cause fallback fonts
- crash the renderer

Include:

- affected string
- affected screen
- missing character
- font resource
- locale

Where practical, link to a font-coverage validation issue.

---

# 5. Text Clipping

Record cases where translated text:

- exceeds a button
- clips outside a dialog
- overlaps another element
- extends off-screen
- is truncated
- wraps incorrectly

Include:

- screen
- resolution
- UI scale
- font scale
- affected locale

If the issue only occurs at certain resolutions, state that explicitly.

---

# 6. Line Wrapping

Record incorrect wrapping such as:

- breaks in the middle of protected tokens
- lines that exceed safe width
- excessive empty lines
- broken punctuation placement
- dialogue boxes with too many lines
- subtitles wrapping beyond engine limits

If a workaround requires manual line breaks, document it.

---

# 7. Subtitle Issues

Record:

- missing subtitles
- wrong timing
- subtitles too long
- overlap
- wrong speaker
- wrong scene
- subtitles outside the visible region
- subtitle renderer missing glyphs

For video subtitles, include:

- video filename
- timestamp
- subtitle source file

---

# 8. Audio and Voice Issues

Record localization-related audio problems such as:

- wrong voice clip
- missing voice playback
- mismatched subtitle and voice
- audio event broken by translated identifier
- regional voice assets missing
- alternate-language voice selection failure

Do not list unrelated original-game audio bugs unless the localization interacts with them.

---

# 9. Font Rendering Issues

Record:

- inconsistent glyph sizes
- bad baseline
- incorrect spacing
- kerning errors
- blurry font
- font scale mismatch
- incorrect punctuation width
- full-width/half-width alignment problems
- fallback font appearing unexpectedly

Include screenshots or scene references when useful.

---

# 10. Resolution and Scaling Issues

Record problems that depend on:

- 4:3
- 16:9
- ultrawide
- 720p
- 1080p
- 1440p
- 4K
- DPI scaling
- emulator internal resolution

Do not assume a rendering defect affects all resolutions.

---

# 11. Menu Issues

Record:

- clipped menu items
- wrong selection labels
- misaligned text
- untranslated options
- broken hotkeys
- overlapping descriptions
- menu navigation issues caused by translated text

State whether the issue affects usability or is purely cosmetic.

---

# 12. HUD Issues

Record:

- clipped HUD labels
- missing counters
- overlap with icons
- wrong alignment
- text too large
- font scaling errors
- localization text causing performance issues

If a HUD issue only occurs in one renderer or resolution, document that condition.

---

# 13. Inventory and Item Issues

Record:

- item names missing
- wrong item descriptions
- pickup text mismatch
- linked names inconsistent
- inventory sorting affected
- item references broken
- text overflows item panels

If an item name is used internally as an identifier, document the risk.

---

# 14. Dialogue Issues

Record:

- missing lines
- wrong speaker
- wrong branch text
- duplicate dialogue
- skipped dialogue
- broken control codes
- dialogue box overflow
- progression blocked by modified text

Include chapter, scene, or event identifiers where possible.

---

# 15. Script and Progression Issues

Localization changes can sometimes affect game logic.

Record cases such as:

- quest does not advance
- event does not trigger
- item cannot be obtained
- scene fails to load
- script branches incorrectly
- save state becomes inconsistent

Treat progression-blocking issues as high severity.

---

# 16. Save Compatibility Issues

Record:

- old saves no longer load
- saves created with localization fail on unpatched game
- translated identifiers affect save data
- different locale builds are incompatible
- save labels display incorrectly

State clearly whether:

- old saves are supported
- new saves are compatible across versions
- clean-start testing is required

---

# 17. Version Compatibility

Record unsupported or partially supported game builds.

Example:

```text
Supported:
Steam 1.2.3

Not tested:
GOG release

Unsupported:
Retail 1.0
```

Do not describe untested versions as supported.

---

# 18. Region Compatibility

Record region-specific behavior.

Examples:

- US build supported
- JP build requires different executable patch
- KR build has different font table
- EU build uses another archive layout

Do not assume two regions with similar files are identical.

---

# 19. Mod Compatibility

Record known conflicts with:

- graphics mods
- source ports
- modernizer patches
- loaders
- proxy DLLs
- reshade
- script mods
- texture packs
- audio mods

Explain the conflict mechanism if known.

Example:

```text
Both projects use dinput8.dll as a proxy loader.
They cannot be installed together without chaining.
```

---

# 20. Runtime Loader Conflicts

If the localization uses a proxy DLL or injected runtime, document conflicts involving:

- `dinput8.dll`
- `winmm.dll`
- `version.dll`
- `dxgi.dll`
- `d3d9.dll`
- `dsound.dll`

State whether chaining is supported.

---

# 21. Antivirus and Security Software

If generated binaries are sometimes flagged, document:

- affected file
- detection type
- whether the file is built locally
- source availability
- checksum
- known false-positive behavior

Do not claim a detection is a false positive without evidence.

---

# 22. Emulator-Specific Issues

Record issues that occur only in an emulator.

Include:

- emulator name
- version
- renderer
- settings
- internal resolution
- whether the issue reproduces elsewhere

Examples:

- PCSX2 texture corruption
- timing-sensitive subtitle issue
- renderer-specific blending problem

Do not present emulator-specific behavior as a confirmed original-hardware issue.

---

# 23. Hardware-Specific Issues

Record issues that depend on:

- GPU vendor
- driver version
- CPU architecture
- controller type
- display refresh rate
- operating system

Only list hardware-specific causes when verified or clearly labeled as suspected.

---

# 24. Operating System Issues

Record differences between:

- Windows versions
- Linux
- Wine
- Proton
- compatibility layers

Examples:

- path encoding
- missing runtime libraries
- case sensitivity
- font availability
- fullscreen behavior

---

# 25. Installation Issues

Record common installation failures.

Examples:

- patch installed to wrong directory
- original version mismatch
- missing required file
- read-only game directory
- launcher restores modified files
- Steam validation overwrites patch
- antivirus removes runtime component

Provide the simplest reliable workaround.

---

# 26. Uninstallation Issues

Document whether the localization can be removed cleanly.

Record:

- files added
- files replaced
- backups created
- files generated at runtime
- settings changed

If uninstall requires restoring original files, state that clearly.

---

# 27. Performance Issues

Record localization-related performance problems such as:

- frame-rate drops caused by text rendering
- excessive runtime glyph generation
- slow archive lookup
- expensive text replacement
- repeated font rasterization
- excessive logging

Include measurable data when possible.

Avoid vague statements like "performance seems worse."

---

# 28. Memory Issues

Record:

- memory leaks
- oversized font atlases
- buffer exhaustion
- increased heap usage
- large translation tables
- runtime cache growth

If an issue only appears after long sessions, document approximate duration and trigger conditions.

---

# 29. Crash Issues

For crashes, record:

- exact trigger
- game version
- locale
- affected file
- stack trace if available
- crash address if available
- reproducibility

Do not write only "sometimes crashes."

State whether the crash is:

- deterministic
- intermittent
- version-specific
- emulator-specific
- unresolved

---

# 30. Data Corruption Issues

Treat potential corruption as critical.

Examples:

- save corruption
- malformed archive
- invalid executable patch
- broken resource index
- overwritten original files
- corrupted configuration

Document backup and recovery instructions.

---

# 31. Build-to-Release Differences

Record cases where:

- development build works
- packaged release fails
- files are missing from release
- release paths differ
- compression changes behavior
- installer changes encoding

Release packaging should be tested independently from local development output.

---

# 32. Known Cosmetic Issues

Cosmetic problems may include:

- minor spacing
- inconsistent punctuation width
- imperfect alignment
- slightly blurry glyphs
- low-priority untranslated decorative text

Classify them as cosmetic rather than presenting them as functional defects.

---

# 33. Deferred Issues

If an issue is intentionally postponed, explain why.

Possible reasons:

- low impact
- requires large engine rewrite
- upstream dependency
- insufficient research
- no known safe fix
- affects only unsupported version

Do not silently abandon known problems.

---

# 34. Fixed Issues

When an issue is fixed, keep a short historical record when useful.

Example:

```text
Status: Fixed in v1.2

Cause:
Font width table used byte count instead of glyph count.

Fix:
Updated layout calculation and added regression test.
```

This helps explain old bug reports and prevents regressions.

---

# 35. Reporting New Issues

When possible, ask testers to provide:

- game version
- platform
- locale
- localization version
- scene or level
- exact text
- screenshot
- logs
- reproduction steps
- whether the issue occurs without the localization

This information greatly improves debugging quality.

---

# 36. Project-Specific Known Issues

Add actual project-specific issues below this line.

Remove unused template sections when adapting this file to a real project.

---

# 37. Final Known-Issue Standard

A useful known-issues document should let players and maintainers understand:

- what is currently broken
- who is affected
- how severe it is
- how to reproduce it
- whether a workaround exists
- whether a fix is planned
- whether the issue belongs to the localization, the original game, an emulator, or another mod

Known limitations should be documented clearly rather than hidden.


## 2026-10-18 当前玩家可见状态

**2026-10-19 更新 / Partially fixed：** 用户截图确认 Disc1 标题弹窗的“踢击”两字正常显示。

**2026-10-19 后续 / Investigating：** 扩展样本的中文/标点可见，窄弹窗自动折行后的前两行左溢、
末行居中。已准备原生强制分割测宽修复候选与无修复中文 A/B 入口，见 WRAP_WIDTH_FIX.md；
尚待用户复测。游戏内剧情对话框更宽，其实际表现不由标题弹窗截图推断。
这是单场景、两字的显示验收，并非完整汉化、双盘或全部字体通过。
本轮已准备长句/标点/无空格中文自动断行的独立测试入口，见 TEXT_LAYOUT_PROBE.md；
额外折行、标点禁则、裁剪及字图扩高的运行表现等待用户截图。

**Open / High：** 尚无可用汉化补丁；中文 glyph coverage、UI 布局、剧情、双盘切换和完整流程未验收。启动提示的静态样式链已指向 General_15 候选，三份 cooked/独立候选的 namespace/GUID 与完整数据指纹一致；双盘 4145 包类表调查完成，见 FONT_BINDING_AUDIT.md。序列化 Core CDO 尾链已闭合，原生默认值、实际加载优先级与绘制绑定仍未确认，历史中文候选未获显示验收。最新约定为游戏测试全部由用户进行，自主开发只做离线分析、工具、合成验证及隔离候选准备。


字面字体覆盖已能离线验证所有显式候选，但不验证像素、atlas矩形、shaping/fallback、动态展开、UI裁剪或实际控件字体。两字文本与三别名候选的静态通过不是玩家可用性验收，见 TEXT_FONT_COVERAGE.md。
