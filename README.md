# 《真名法典2》简体中文汉化

Xbox 360 版《MagnaCarta II》（마그나카르타 2）的简体中文汉化与可重建本地化工具链。

目标语言为 `zh-Hans`，以 Xenia 为主要测试环境。仓库保存结构化译文、术语、字体与资源处理工具，以及格式研究和验证记录；语言数据与通用工具分离，便于后续维护和其他语言复用。

## 支持版本与当前状态

基于项目已校验的韩版 Disc 1 / Disc 2 原始样本开发，资源身份由[提取配置](locales/zh-Hans/extraction-profile.json)锁定。版本指纹及双盘差异见[版本与资源调查](docs/RESOURCE_SURVEY.md)，其他区域或未知版本不作为当前构建目标。

**正在分批翻译与验证，尚非完整汉化发行版。**

进度快照：2026-10-23，翻译`batch-120`，资源工程第287阶段。

| 内容 | 当前进度 |
| --- | --- |
| 正文文本 | 14,148 / 18,176 条已有中文草稿 |
| 独立动画字幕 | 315 / 315 条已有中文草稿 |
| 邮件主题与正文 | 233 / 235 字段已有草稿，包含在正文统计内 |
| 共享术语 | 1104 项候选，另保留历史字幕来源记录 |
| 字体与显示 | 已有补字、标点与对白排版测试候选，仍需游戏内验收 |
| 发布与验收 | 第一盘现有测试根已含累计INT和本盘152cue；第二盘163cue独立离线，游戏验收未完成 |

草稿数量不等于人工定稿或游戏内完成率。正文统计包含空白、删除标记和格式待查项，图片及硬编码文字仍需覆盖审计。后续进度以[连续翻译接续点](docs/TRANSLATION_QUEUE.md)与[翻译工作流](locales/zh-Hans/translation-workflow.json)为准。

两盘保留独立来源，共用经过资源路径与哈希校验的译库，**当前不做双盘合一**。

## 获取与测试

仓库提供源码、译文、配置和技术文档，不包含游戏本体、原版镜像、Xenia 或本机构建输出。重建需另行准备匹配版本的原始文件及字体等依赖。

现有本地测试入口及内容范围：

- [开场 NPC、教程与菜单测试](docs/OPENING_BATCH_TEST.md)：开场范围的独立测试包与原文对照。
- [对白显示与开场字幕修复](docs/DIALOGUE_DISPLAY_REPAIR.md)：标点、空白字形与折行修复候选。
- [字体与文本可读性](docs/TEXT_READABILITY.md)：字距、标点和排版规则。

以上旧文档记录各自阶段。当前同一`dist/MC2-display-repair-disc1`入口已增量更新累计14,148条INT、本盘21字幕/152cue及七字体，原文对照保持；见[第287阶段](docs/PHASE_287_REMAINING_UI_AND_SEPARATORS.md)。第二盘29项资源/163cue保持独立离线。TAB语义、既有换行策略以及对白、菜单、字幕、战斗和存读档仍需游戏验收；未自主启动模拟器，离线验证不代替实际游玩。

问题反馈宜附版本或测试包身份、Xenia 版本、场景、复现操作、截图及日志。

## 从源码重建

依赖、原始文件身份、资源提取、字体生成、回填及增量刷新流程见[构建说明](BUILDING.md)。当前包含多个专项构建与诊断流程，不提供将所有研究候选自动组合为完整发行版的单命令安装。

默认源码测试使用 Python 3.12+，以自制样本运行，不依赖游戏本体：

```powershell
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

普通迭代复用现有测试目录，只按校验流程增量刷新相关资源，不逐轮生成 ISO 或完整游戏副本。原盘、配置、存档、运行记录及必要回滚证据保持不变。

## 参与翻译与维护

译文按稳定 ID 和原文摘要绑定，保留控制码、占位符、资源标识与功能换行。未知格式先记录，不猜补；候选译名和自动检查通过不等于人工校对完成。

- [翻译说明](TRANSLATING.md)：文本分类、上下文、换行与校对约定。
- [术语表](GLOSSARY.md)：由 `locales/zh-Hans/terms.json` 生成。
- [系列术语来源](docs/SERIES_TERMS.md)：参考版本、来源和跨作品身份的核对边界。

其他语言的数据应独立放入 `locales/<locale>/`，并验证编码、字形覆盖和游戏内排版；当前不表示其他语言已完成适配。

## 仓库结构

| 路径 | 内容 |
| --- | --- |
| `locales/zh-Hans/` | 译文、术语、来源约束与批次审核记录 |
| `tools/` | 提取、校验、字体和资源重建工具 |
| `tests/` | 自动化测试与自制样本 |
| `references/`、`assets/`、`licenses/` | 固定来源、项目配置素材及第三方许可 |
| `docs/` | 格式研究、构建方法、专项测试与历史批次记录 |
| `build/`、`dist/`、`xenia/` | 本地输入、生成物及测试环境，不随源码分发 |

## 技术与测试文档

- [技术说明](TECHNICAL.md) · [当前状态](docs/STATUS.md) · [已知问题](docs/KNOWN_ISSUES.md)
- [共享译库与双盘回填](docs/SHARED_TRANSLATION_WORKFLOW.md) · [正式文本管线](docs/TRANSLATION_PIPELINE.md)
- [文件格式](docs/FILE_FORMATS.md) · [技术陷阱](docs/PITFALLS.md) · [全部专项文档](docs/)

## 许可与来源

项目原创代码采用 [MIT](LICENSE)，原创译文采用 [CC BY-SA 4.0](LICENSE-translations.md)。字体、参考工具和第三方组件遵循各自许可，固定版本、作者及复用范围见[来源与许可](NOTICE.md)。

原版游戏文本、商标与商业资源的权利归原权利方所有，不在上述原创内容授权范围内。仓库不分发完整原版游戏文件。
