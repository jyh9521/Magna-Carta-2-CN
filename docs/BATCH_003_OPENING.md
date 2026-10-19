# 第三批：开场剧情、战斗教学对白与村民

日期：2026-10-19。状态：217条新增draft已离线回填，尚未更新字体/TOC及可玩测试包。

## 翻译范围

| 文档 / 场景 | 新增条数 | 内容 |
|---|---:|---|
| MC2CSMB / CSMB00_13 | 30 | 拉·斯特拉达、世界历史、斯特拉斯的牺牲 |
| MC2CSMB / CSMB00_14 | 19 | 拉普斯珍珠、护身符、晶柱及保存记忆 |
| MC2CSMB / CSMB00_15 | 80 | 战斗/移动模式、普通攻击、冲刺、技能、固有技、耐力、超限及过热 |
| MC2CSMB / CSMB00_18 | 42 | 比尔特、朱特的名字与失忆、真剑恐惧、公主来访 |
| MC2NpcTalk / Ch00_1 | 15 | 公主来访与村民反应 |
| MC2NpcTalk / Ch00_2 | 27 | 洞窟受袭、伤员、带路及守护者危机 |
| 关联姓名/地点/技能字段 | 4 | 比尔特、拉·斯特拉达、风歌洞窟、凌空震踢 |
| 合计 | 217 | 210条dialogue、3条narrative、4条name |

既有316条内容逐ID保持不变；累计533条INT草稿，原18,176条中其余17,643条不变。
三条narrative为CSMB00_18的31/32/33号内心独白，保留第一人称和上下文。
同NPC文档Ch00_2中的00_131_00重复key仍保留两个occurrence，未按key覆盖。
独立动画字幕本轮未新增，继续保留已有49条draft。

## 用词与标记

沿用朱特、梅莉莎、蕾洁菲尔妲、斯特拉斯、守护者、哨兵、晶柱、耐力、超限、过热及KAN。
新增14项术语，词表由45项增至59项，全部仍为candidate；不声明官方定名或维护者已审核。
新增用词包括拉·斯特拉达、兰兹海姆、比尔特、特雷瓦族、风歌洞窟、拉普斯、
拉普斯壳、连环术、力量KAN、战斗模式、移动模式、冲刺、反击、凌空震踢。
四个关联名称字段与对白中的称呼同步回填，不只在对白里改名。

**Verified / source observations：** INT的Juto_Style1/Juto_Skill00为이공진퇴，
JPN同字段为裏空進槌；本批按踢击/击飞的连续教学语境使用候选名“凌空震踢”。
这不是日文汉字的机械简化或官方译名声明。

对白延续已采用的去继承硬换行策略：只对本批存在字面\\n的条目逐项写明
line_break_policy的source_count及target_count=0。其他控制标记仍逐项有序校验。
未修改教程文档中的功能性换行，也未以空格或手工换行迁就旧字库。
对真实源值逐条比较A/B/X/LT/LB/RB/BACK键位顺序与数字字面值，均保持一致，包括3次连击。

## 保留待查项

**Verified / anomaly：** Ch00_1的00_101_00含未核验的`\\항상`片段，不是标准字面\\n。
该条未进入新计划，原值及其hash保持不变；held_entries记录真实ID和原因。
不把未知转义猜成换行后继续翻译，后续须先调查原文本和显示行为。

**Verified / alignment trap：** INT与JPN的CSMB00_15同名对白key存在位置错位。
例如0015_31在INT提到技能名，在JPN却是“以前教过腿技”的话题句；
因此本批未按同key批量套用另一容器译文。关联技能名称的字段线索与整场对白对齐是不同证据。

**Runtime pending：** 新增字集、长句自然折行、村民对白和名称宽度尚待重建字体/TOC及用户游戏验收。
本轮未启动模拟器，也未刷新现有可玩入口，原盘、存档、配置、runs和历史测试包均保留。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/chapter00-batch003/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -v
python tools/check_repository.py
```

输出必须全新；正常后续批次另选build下的描述性输出目录，原文件和研究证据不覆盖。
workflow当前组合readability-fix、batch-002、batch-003三个不重叠批次，
每个依赖均锁定LF字节SHA256，原始八容器重新校验后生成一份累计计划，跨盘复用。
本地证据位于build/batch-003-verification：
BASELINE_FILE.int为既有316条版，MODIFIED_FILE.int为533条版，DIFF_FILE.json保存217条增量；
ROLLBACK.sh仅接受预期新hash与基线hash，在独立副本恢复原316条版，主修改文件保持533条。
VERIFICATION.txt记录精确命令、输出、exit、hash、测试及推送结果。

下一批接CSMB00_21起的公主到访/洞窟剧情，避免跳过场景，并继续补齐同阶段NPC与任务文本。
