# 第132阶段：开篇场景、任务与字幕上下文审读

2026-10-20，起点a765dd2、干净状态，核对BUILDING及workflow最后已提交翻译批次116。本轮是275项既有草稿的上下文审读，不新增翻译批次或凑条数，14,082 INT/315cue draft、1104 candidate保持。

## 完整范围：244 INT + 31独立字幕

- MC2CSMB的CSMB00_10/13/14/15/18五个完整场景，共192项：备战与瞭望台、拉·斯特拉达背景、珍珠/晶柱、80行完整战斗教程、木剑/真剑及公主到访过渡。
- MC2Quest/Ch00_104_0整条42字段：委托、拒绝、教程选项、进行、完成、击杀进度、目标/说明全部纳入，不只抽看含换行的几句。
- 10项关联：Juto/Melissa/Mellisa/Mellisa1/Villter五名称、Chapter00_13踢击提示、Ch00_2/80_0完整指路节点、Cave场地名、ShellofRabpers交互名及Movie/00_12标题。
- 独立字幕csm00-10/12/20完整22/3/6cue，共31句；保留盘一来源、原始时序/class/清除事件与br标记，不把这些字幕合入INT或第二盘。

下一阶段从CSMB00_21/22的洞窟带路/加入请求继续，不把第五章重访台词混入本轮。旁读的后续场景不计本轮已完成数量。

## 当前草稿处置

逐句对照本轮韩文与中文及关联名称，保留当前草稿，没有发现需要在本轮强制改译的语义/键位冲突：

- 守护者/哨兵及南部军研究动机按源区分；拉·斯特拉达、斯特拉斯、兰兹海姆、KAN沿用共享候选，不升级术语定稿。
- 朱特命名与草的玩笑保留；木剑/真剑、过去战事与恐惧的推测语气保持，不把猜测写成已证事实，不从轮次推断具体配音者。
- 完整战斗教程中LT、A、X、B、RB、LB与普通攻击3次保持；RB或LB的切换与RB+LB同时按下的锁定动作不混同。
- 无壳克洛普斯3只与硬壳拉普斯分开，任务接受/拒绝/进行/完成连贯；QUEST%s及三个%s进度/选项样式与键位顺序不改。
- 村民/朋友的语气差异及已有“知道了/明白了”等自然应答不机械统一，Melissa/Mellisa/Mellisa1名称记录各自保留。
- 开篇字幕回忆叙述、叫醒/坠落对话、瞭望台抱怨与伤兵来报均与邻接场景衔接；没有用字幕内容反向猜填未知格式。

这些是对既有draft的上下文观察，不是人工reviewer、全文定稿、配音核验或游戏验收。

## 换行观察与功能分隔对照

全计划5191条显式line_break_policy不改。本轮244项中121项有这种策略，记录为context-observed-draft-retained；其余5070项仍待上下文审读。所有5191项运行布局仍待核，不因上下文读通就批准删换行。

明确锁定三个保持功能分隔的对照：Ch00_104_0/yesno的X进行教程/Y跳过教程、DES的任务说明，以及Chapter00_13踢击提示。它们的源/译TOKEN序列含原换行且完整相同；不把对白布局策略套到选项和说明。

新增tools.audit_line_context和locales/zh-Hans/context-reviews/opening-layout.json。完整源SHA、完整计划canonical SHA、各项源/译SHA、document/section/key/occurrence及原始顺序锁定；完整section不允许悄悄缩成若干key，单项关联则显式列key，重叠/缺项/新原值/变更草稿拒绝。输出只含标识、摘要、邻接ID与说明，不输出完整原文/译文。

新增键位/数字检查在已有TOKEN验证之后执行：先在临时观察字符串中隔开已验证的转义/样式标记，再识别按钮和数字。初始朴素ASCII边界把紧邻字面换行后的A/X当成与n相连的单词，误报Chapter00_13和0015_38；修正的是观察器，不是源或译文，不删除真实A/X。已加入回归用例。

## 复现

```powershell
python -m tools.audit_line_context --source build/disc1-selected/MC2Game/Localization/Coalesced.int --plan build/cumulative-locale-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json --profile locales/zh-Hans/context-reviews/opening-layout.json --output build/开篇新建上下文报告.json
python -m unittest discover -s tests -p test_line_context_audit.py -q
python -m unittest discover -s tests -q
```

不带profile：0项观察、5191上下文待审；带profile：244项上下文、121策略观察、5070上下文待审。两者runtime待核均5191、translation_edits=0。源/计划/profile输入与输出回读，输出必须新建。

## 验证与收尾

基线1602、新增10项后修改与干净索引源码1612均OK(skipped=1)。源/计划/草稿/顺序漂移、完整场景闭合、坏key/重叠范围、未翻译原值、功能换行被删、键位数字变化、转义邻接识别与旧输出保护均测试。

双盘报告精确相同；31字幕逐cue源/译摘要、BOM/时序/class/清除事件与逆重建核对。两原ISO/八源hash、双盘14082回填/旧译/未改值、七字体与56 raw回滚、164工作区、24held及当前204入口依赖再核保持。原token检查与生产翻译计划不改，TAB coverage=false。

四件证据保存在build/phase-132-verification。真实报告BASELINE无profile到MODIFIED含profile，独立报告副本经hash保护回滚恢复0观察/5191上下文待审；主报告保留244/121/5070。精确命令、输入、字面输出和退出状态见VERIFICATION.txt。回滚的是报告，不是玩家译文或运行包。

只清理核实可再生成的隔离源码pyc；保留原盘、依赖、配置、存档、runs、当前包与全部回滚/研究。提交推送后核对HEAD/远端和干净状态，再沿场景继续审校，不生成ISO/整盘副本、不启动模拟器、不重复翻译已提交批次。
