# 第二十批：家人遗物、哨兵争论与拉提族任务

日期：2026-10-19。新增INT167条draft，累计3,454条；191项candidate术语。
同阶段csm04独立字幕14cue已在第十六批覆盖，全部字幕仍为141/315cue，本批不重复修改。

## 范围与覆盖

- CSMB04_150/151/152/153/154/155/160七场96条，含150末尾4条内心叙述。
- Ch04_Abazet索引91–120共30条，累计121/242条；原key和顺序保持，下一条04_2227_00。
- 04_4202_0黛芭请求11条、04_4203_0古文书18条、04_4203_1九节草9条，共38条。
- 关联名称：Marice/Deva/poison_rati共3条；没有给未具名的家人遗物补造正式物品名。
- 分类154 dialogue、4 narrative、6 name、3 quest_description；本轮没有进度计数模板。

Verified / offline：当前INT MC2CSMB的CSMB04前缀共411条，357条已有draft，剩余164/170/180/190四场54条。
Ch04_Abazet达到121/242条；仅为该独立section的一半，不包括后续同地点状态、Compose、邮件、字幕或硬编码。
不把这些统计等同于全章或游戏显示完成。

## 上下文、称谓与格式

玛莉丝、黛芭、九节草3项新增candidate；露、阿维斯族、公会联盟等复用既有译库。
阿尔斯是生物学家之子，来自4203_0的明确原文；不据其他英文key的相似拼写合并独立角色字段。
玛莉丝称呼少爷、克罗塞尔的下级贵族出身和物品被夺按原文翻译，不增补遗物种类或名称。
军事会议中反对、支持、按战局有条件考虑哨兵的不同立场逐句保持，守护者制造方式仍是人物推论，
不提升为工程研究事实。九节草只译游戏任务称谓，不增写原文没有的配方或操作步骤。
城镇源文仍要求夺回杜南丘陵，按源保留，不根据当前剧情进度暗改成已夺回。

4202/4203_0任务DES各保留1个功能换行；4203_1说明与poison_rati名称各保留1个源尾随空格。
96条继承硬换行使用显式计数策略移除；数字、键位、控制标记、旧译、重复key和未知格式保持。
本轮未新增QUEST进度条，不擅自套用先前的数量/占位符模板。

## 重建、核验和收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/heirloom-batch020/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。双盘INT原件hash保持，167条新值回填一致；旧3,287条不变，14,722条仍为源值。
独立副本回滚恢复3,287条基线，主MODIFIED_FILE.int保持3,454条；错误hash目标被拒绝且不变。
Git index源码干净导出后运行完整测试，61项依赖锁逐一核对；两次工作区164个文件hash一致。
字幕profile及18份计划逐字节保持旧HEAD，本批未重读完整ISO，不把旧字幕证据称为新回填验证。
本地主证据、测试日志和独立回滚副本在build/batch-020-verification；完整源文/资源不提交。
仅清理确认无入口依赖的可再生验证缓存；原盘、配置、存档、runs、当前包及基线/回滚/研究证据保留。

不生成ISO/整盘副本，不自行启动模拟器，不更新字库/TOC/可玩入口；离线成功不替代游戏验收。
提交推送、核对远端/干净状态后，从CSMB04_164及Ch04_Abazet索引121继续，
按场景推进剩余04_4222/4225/4232/4239分支与后续独立字幕，不重复已译资源。
