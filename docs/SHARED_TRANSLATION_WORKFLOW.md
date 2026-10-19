## 第七批司令部与新命令（2026-10-19）

新增112条，累计1,501条INT草稿、131项candidate；剧情含CSMB02_38_1/2分支，城镇142/276条。
旧译1,389条保持不变，狩猎任务保留功能换行、QUEST%s前缀与占位符。
范围与重建见 [BATCH_007_ORDERS](BATCH_007_ORDERS.md)，不更新字库/TOC/可玩入口；推送核对后直接接续。

# 共享译库、核心名词与第二批翻译

## 最新：第六批与连续接续（2026-10-19）

新增272条，累计1,389条，124项candidate；当前工作区build/team-batch006/verified-workspace。
接续点及每批推送后继续的约定见 [TRANSLATION_QUEUE](TRANSLATION_QUEUE.md)，批次证据见
[BATCH_006_TEAM](BATCH_006_TEAM.md)。后文数字均为历史快照。

## 最新：第五批阿巴泽特到访（2026-10-19）

新增276条，累计1,117条INT草稿，102项candidate。当前工作区build/abazet-batch005/workspace，
明确组合五个不重叠批次；原841条版保留作基线。首任务及带样式的分支保留功能性换行，
范围与证据见 [BATCH_005_ABAZET](BATCH_005_ABAZET.md)。下文数字为历史快照。

## 最新：第四批洞窟与海岸防卫（2026-10-19）

新增308条，累计841条INT草稿；75项candidate。当前工作区为build/island-batch004/workspace。
CSMB00/01的427条可提取剧情均有draft，相关NPC155/156条，剩余异常1条保留；
不扩大为动画字幕、其他文档或全游戏完成。完整范围见 [BATCH_004_ISLAND](BATCH_004_ISLAND.md)。
历史533条版保留为基线，后文数字是各批快照。

## 最新：第三批开场剧情（2026-10-19）

新增217条，累计533条INT草稿；名词表59项candidate。范围、异常原文保留、
键位/数字校验、双盘回填及恢复证据见 [BATCH_003_OPENING](BATCH_003_OPENING.md)。
当前输出为build/chapter00-batch003/workspace，原316条版工作区保留作基线。
下文316条和45项等数字是第二批快照，当前workflow已显式加入第三批；不手工维护累计译文副本。

日期：2026-10-19。当前决定：暂缓双盘合一，使用一份翻译工程与双盘来源映射。

## 已验证事实

- 重新核验八份提取原容器及无修改逐字节往返。三个本地化容器分别跨盘相同，
  71,802条两盘物理记录共享为35,901条候选；配置容器只审计，不作译库。
- 80份本地源catalog完整保留；新的work副本叠加当前批次，原源catalog不改。
- INT 18,176条：316条draft、13,097条翻译候选、3,211条编辑器参考、1,552条待查上下文。
  JPN 17,642条与KOR 83条保留独立复核队列，不机械对齐到INT。
- 域/队列是筛选提示，不保证每条都在玩家画面出现；数字、标识符、未调查文档均保留。
  相同词面不同ID保持独立，不因共享字符串而丢失上下文。
- `batch-002.json` 新增54条：商店30、武器类型/属性24。
  累计316条保留readability-fix全部262条；其余17,860条INT原值不变。
- 45个术语均为candidate；本轮新增22项，均有真实本作字段锚点。
  `term-concordance.json`记录精确词面与子串上下文ID，子串不作为概念关系证明。

## 两盘独有动画字幕

`subtitle-profile.json`锁定两份ISO完整SHA256、文件大小及全部Movies/*.txt成员。
工具实际重新核验完整ISO、从XDVDFS获取真实成员位置、核对每份字幕hash后再解析。
两盘有44个不同字幕路径：D1独有21、D2独有23，无共享路径。
共315个可解析cue，既有四份计划的49条draft已叠加，其余266条未译。
全部44份保留BOM、时序、class、清屏及br标记并验证无修改逐字节往返。
相同路径且相同内容可共享；独有路径即使词面相同也不自动合并。

字幕源全文仅在忽略的build里；仓库profile只含路径、大小、hash和盘别，不收录完整原字幕。
完整ISO只读，不提取视频或新建完整游戏副本。

## 可复现命令

从原盘准备八份源容器的步骤沿用BUILDING.md。以下输出目录必须尚不存在：

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/shared-translation-workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -v
python tools/check_repository.py
```

工作区manifest给出每份源/工作catalog路径、盘别、队列计数及累计回填计划。
`plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json`
是当前316条累计INT计划，可用既有`build_coalesced.py`对任一受支持原盘容器回填。
它由两个不重叠批次生成，不维护第三份手工累计译文。

依赖hash改变、批次重叠、原值hash不符、控制码/分类错误、术语锚点不存在时均终止；
验证完成前只在临时目录构建，失败不发布半成品。现有输出拒绝覆盖。
subtitle导出还拒绝漏列/重复Movies txt成员、错盘hash、未知字幕计划和重复cue起点。
新批次应只列增量ID，并显式更新workflow锁；历史样本不再叠加，否则重复ID会失败。

## 本轮离线回填与回退证据

本地目录：`build/shared-workflow-verification/`。

- `BASELINE_FILE.int`：D1/D2原容器hash相同，无修改回填仍逐字节相同。
- `MODIFIED_FILE.int`：316条中文；两盘独立重建得到相同输出hash。
- `DIFF_FILE.json`：逐ID前后值、316条修改、262条保留、54条新增、17,860条不变。
- `ROLLBACK.sh`：只接受预期中文hash及原备份hash，独立副本恢复全部18,176条原值。
- `VERIFICATION.txt`：精确命令、输入、输出、exit和最终状态；主修改文件保持中文。

这些只证明资源/工作区一致性，不代表全游戏显示、第二盘流程或新增菜单排版已验收。
本轮未刷新可玩测试包：新增字符尚未纳入本轮字体/TOC构建。
现有`dist/MC2-display-repair-disc1/开始中文测试.cmd`、用户配置、存档与runs均保持不变。
后续依次做译文/术语校对、按正式译文收字、字体与TOC验证，再增量刷新同一测试入口；
不删改译文迁就旧字库容量，不创建新的整盘副本。游戏验收仍由用户执行。

## 下一批

优先核对本批武器/属性及45项术语的上下文，再按章节推进剧情/NPC，按功能推进任务、
教程与物品技能。已译ID始终从累计计划继承；战斗日志前后缀先确认拼接顺序。
xxx内嵌、硬编码、图片文字仍是独立覆盖审计项，35,901与315均不是“全游戏台词数”。
