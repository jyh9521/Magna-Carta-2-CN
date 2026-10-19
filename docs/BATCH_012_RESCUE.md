# 第十二批：海底洞窟营救、阿巴泽特尾段与追加指令

日期：2026-10-19。新增INT144条draft，累计2,246条；161项candidate术语。
另补齐csm02-10/21/33独立字幕27cue，累计93/315cue；当前csm02四份字幕30cue均有draft。

## 范围与覆盖

- CSMB03_71/72/73/80/90/100六场74条，连续推进隐藏道路、洞窟、鲁坦对峙与救出马雷族。
- Ch02_Abazet索引222–275尾段54条；该section全部276条已遍历，274条draft、2条纯连字符保留。
- Ch02_Qube_01追加指令12条，包含领斧、击杀目标、炸弹运输与归还要求说明。
- 鲁坦、尼尔提、杜南平原、寂静荒野4条关联人物/地点名称。
- 分类135 dialogue、5 name、1 quest_description、1 quest_progress、2 quest_objective。

上述城市范围只是MC2NpcTalk/Ch02_Abazet这一个section，不表示城市所有任务、脚本或其他资源完成。
CSMB02剧情585条和csm02字幕30cue已有draft，也不表示第二章所有可见文字完成。

## 格式与术语

新增鲁坦、尼尔提、杜南平原、寂静荒野、南部关卡、强壮拉普斯、炸弹箱7项candidate。
杜南平原/丘陵是不同源名；炸弹箱与既有炸弹包按不同源词保留，不静默合并。
Dunen_Field等原key拼写保持不变，关联字段通过稳定ID而非翻译名称定位。
追加指令保留3只目标、斧子领取、港口方向、炸弹箱交付及破甲条件；Des保留5个功能换行。
`QUEST%s:`及另两个`%s`顺序不变，77条对白仅按显式source_count策略移除继承硬换行。
鲁坦的指控、族群仇恨和角色的解释按说话立场翻译，不将任何一方断言改成已证实旁白。
攻城相关NPC对话保留晶柱、潜入/扰敌分工及胡安的区别，不擅自统一为同一种作战。
字幕13/9/5cue依据各自源值hash与时序独立翻译，保留5处br与全部清屏/class/BOM结构。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/rescue-batch012/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-012-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。workflow十二份不重叠INT计划、字幕profile十份计划；两盘完整ISO及44份字幕hash重新核验。
Verified / offline：双盘INT结果一致，旧2,102条逐ID不变，原18,176条中15,930条保持原文。
字幕旧66cue不变，27cue实际回填、结构不变；独立副本回滚恢复原三份字幕，修改输出保留新译。
INT独立回滚恢复2,102条基线，主MODIFIED_FILE.int仍保留2,246条；旧未知反斜线、两条纯标记和重复key均保持。
另验证274/276城市范围、30/30 csm02字幕、干净源码单测、依赖hash和164文件重建一致性。
四份主证据及字幕差异/基线/回滚副本保存在本地build/batch-012-verification。

清理仅处理核实可再生成的验证缓存；保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究证据。
本批不启动游戏、不生成ISO/整盘副本，不更新字库/TOC/可玩包；草稿和候选不等于人工定稿或游戏验收。
推送核对后从CSMB03_104继续；城镇尾段已遍历，下一批转同阶段柯塔马雷NPC与后续任务。
