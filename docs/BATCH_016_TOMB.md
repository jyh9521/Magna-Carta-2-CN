# 第十六批：信任、祖先之门、斯特拉斯之墓与归途

日期：2026-10-19。新增INT179条draft，累计2,821条；176项candidate术语。
另新增csm04-20/100独立字幕14cue，累计141/315cue；两份csm04字幕14cue均有draft。

## 范围与限定覆盖

- CSMB03_170/180/181/190/200五场134条，含170末尾5条内心独白及180内的1_00/1_01后缀key。
- Ch03_KotaMare_03独立状态25条；初始/_01/_02/_03四个section合计118条均有draft，不合并同名key。
- Ch02_299_00新手鞣皮匠18条；斯特拉斯之墓、阿塞莉娜之泪2条关联地点/物品名。
- 分类168 dialogue、5 narrative、3 name、各1条quest_description、quest_progress、quest_objective。

Verified / offline：当前INT Coalesced的CSMB03共有688条，687条已有draft，唯一保留为原文的是
CSMB03_20/voc_csmb_0320_50未知反斜线条目。该统计不包括任务/NPC/独立字幕/资源内嵌文字，
也不表示第三章所有可见文字或游戏显示完成。KotaMare覆盖仅限上述四个section，不含后续章节同地点内容。

## 语义与格式

新增阿塞莉娜、卡尔塔大战、斯特拉斯之墓、阿塞莉娜之泪4项candidate。
碑文/传说按角色转述翻译，保留坟墓与死亡地点不同的说法，不擅自补写遗体所在或跨作同一性。
内心独白与对白分别分类；相信同伴/复仇的不同立场按原文保留，不添加角色未说出的结论。
香水瓶摆放明确保留颜色匹配条件，不发明颜色数量或新操作码。
鞣皮匠任务保留5只目标、皮钱及`QUEST%s:`和另两个`%s`；DES保留1个功能换行。
96条对白仅按显式计数移除继承硬换行；旧功能布局、未知转义、纯标记和空白pay不动。
字幕1/13cue按各自hash/时间轴翻译，保留6处br及BOM/class/清屏；只翻译源文明确称呼，不补写身份解释。
csm04字幕是独立资源先行推进，不代表第四章Coalesced正文已完成。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/tomb-batch016/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-016-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。workflow十六份不重叠INT计划，字幕profile十八份计划；两盘完整ISO及44份字幕hash重新核验。
双盘INT结果一致，旧2,642条逐ID不变，原18,176条中15,355条保持原文。
字幕旧127cue不变，14cue回填且结构不变；独立副本回滚恢复原两份字幕，修改输出保留新译。
INT独立回滚恢复2,642条基线，MODIFIED_FILE.int仍保留2,821条；另验证687/688剧情、118状态NPC、
干净源码测试、依赖hash和164文件重建一致性。四份主证据及字幕差异/基线/回滚副本保存在本地build/batch-016-verification。

清理仅处理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究证据。
本批不启动游戏、不生成ISO/整盘副本、不更新字库/TOC/可玩包；草稿与候选不等于人工/游戏内验收。
推送核对后从CSMB04_001继续，接第四章NPC、剩余第二章任务分支及后续独立字幕。
