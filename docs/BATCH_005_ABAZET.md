# 第五批：阿巴泽特到访、城镇NPC与首任务

日期：2026-10-19。新增276条draft，累计1,117条INT草稿；本轮只完成文本离线回填。

## 范围与连续性

- CSMB02_05/11/20/22/23/24六场160条：岛屿救援争执、朱特苏醒、复仇与入队、
  狼人任务、库布通信装置及小队战斗引导。
- Ch02_Abazet前84条：02_201_00至02_286_close_01，涵盖城镇欢迎、种族/KAN知识、
  公会联盟、矿工、战争反应及抓蓬蓬小游戏。该section共276条，本轮只完成84条，不宣称整城NPC已完成。
- Ch02_206_0任务21条：任务名、目标、委托/拒绝/接受/进行/完成对白与格式化进度。
- 关联名称11条：露、伊尔/伊姆/伊恩、施耐德、两份阿维斯族姓名字段、解毒剂、
  老狐峡谷、狼人据点及拉提族洞窟。

分类为250条dialogue、11条narrative、12条name，以及quest_description/progress/objective各1条。
CSMB02_11四句自语，及CSMB02_22的25–28/50–52号内心独白单独分类narrative。
既有841条逐ID保持不变；原18,176条INT值中其余17,059条保持原文。
动画字幕仍保留既有49条draft，本轮未新增；此前未知反斜线条目继续保留原文待查。

## 功能标记与换行

**Verified / offline：** 两条带Styles的X/Y选择及任务DES共三个条目的功能性换行全部保留。
两个选择各1个字面换行，任务DES为3个（含空白段落）；没有套用普通对白去继承硬换行策略。
review.preserved_functional_break_ids仅作审核记录，不豁免校验；这三条没有line_break_policy，
由既有导入器默认要求保护标记/字面换行严格一致。

其他需要去继承硬换行的对白逐条锁定source_count与target_count=0，非目标标记仍要求顺序一致。
所有新增键位（含X/Y）、数字与SID逐条核对；保留3只、300SID及34/12/6等分数原值。
任务Kill的`QUEST%s:`前缀不翻译，三个`%s`及顺序/括号保持一致，未把机器前缀当作自然语言。
同名NPC/任务key保留各自文档/稳定ID，不按key合并跨文档值。

## 名词与上下文

词表75增至102项，全部candidate，不自动标维护者已审核或跨作同一概念。
库布沿用既有UI译名，并明确为收发信件的装置；既有“给库布的信”标签保留待专项校对，未覆盖旧译。
本批同步补齐露、公会三位工作人员等姓名以及相关地名/物品名。
亚历克斯与亚历克斯伯爵的短名/称号分别记录；亚历克斯命中固定《真红的圣痕》词表同词面同译名，
只保留锁定来源，不自动认定是同一人物或确认继承。

**Verified / source observation：** 本作CSMB03_20/voc_csmb_0320_12将재화종解释为“灾难的种子”。
本批据该上下文使用候选名“灾祸种”，未把其成因或相关世界观推测标为事实，也未把查阅的后续场景计作已译。
狼人、种族、希昂·雷格拉尔、矿山及小游戏等新增译名仍需维护者结合后续剧情审核。

## 重建与证据

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/abazet-batch005/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -v
python tools/check_repository.py
```

输出必须全新；workflow明确组合readability-fix及batch-002至005五个不重叠批次。
同资源/hash跨盘共享回填，不合盘、不生成ISO或完整游戏副本。
源文件及所有计划依赖均使用真实字节hash，生成工作区后可用既有build_coalesced.py回填任一受支持原盘。
源文件、既有841条版工作区和历史回滚证据均保留。

build/batch-005-verification中BASELINE_FILE.int为841条版，MODIFIED_FILE.int为1,117条版，
DIFF_FILE.json保存276条增量；ROLLBACK.sh在独立副本恢复841条，主修改文件保持新译文。
VERIFICATION.txt记录精确命令、输入、字面输出、exit、hash、测试及提交/远端身份。
公开无原文单测只检查声明的参考身份/固定commit；`series_terms.py check --with-references`
另行核验真实固定缓存字节，不能把无缓存单测替代上游来源核验。

**Runtime pending：** 本轮未更新字库/TOC或刷新可玩包，也未启动模拟器；现有入口、原版对照、
存档、用户配置及runs均保持不变。新增字幕/排版仍需后续字库与游戏验收，不把离线通过当作画面通过。
下一批接CSMB02_25的小队战斗教学和城镇后续NPC/任务，不跳过未译分支。
