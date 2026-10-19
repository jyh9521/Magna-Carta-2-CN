# 第三十九批：成人礼三仪式与第六章任务缺口收尾

日期：2026-10-19。新增INT97条，累计5,497条draft；255项共享candidate及1项独立字幕candidate。
字幕27份187/315cue与邮件96/235字段不变，均未人工定稿。

## 范围与上下文

- Quest/06_301_0成人礼总任务21、06_304_0自然仪式17、06_302_0力量仪式16、06_307_0香气仪式18。
- 06_699_0亚历克斯的信17字段；任务共89字段。
- CharacterName内斯汀/斯维汀/格拉米3字段，Item空瓶说明/尤尼昂之角/香气之源及说明4字段，UI香气之源1字段。
- 分类70 dialogue、11 name、6 quest_objective、5 quest_description、3 quest_progress、2 item_description。

Verified / source/offline：新增ID与前38批无重叠。Quest/06_由225增至314/316，剩余恰为
06_603_0/603_0与06_zepi_1/order_2两处未知反斜线。全部已解释字段有draft，不能称316条全部完成。
与此前主线、场地念白及庆典前/中NPC复用共享译库，不因同一场景重复翻译或合并独立ID。
内斯汀/斯维汀/格拉米/尤尼昂及其角、香气之源、三项仪式新增9项candidate；
阿塞莉娜之泪直接复用既有candidate及Item译法，不重复新增或覆盖旧Item值。
699_0对亚历克斯私下联系投降部队的疑惑保持说话者怀疑，不补写背叛等结论。
成人礼的3项仪式、3个人与4处香气来源、明日庆典及塞蕾丝汀限定参加条件保持。

5条DES共9个功能换行及首条空段落索引保持，58条普通对白有显式去硬换行策略。
QUEST%s、计数%s、ASCII括号/方括号与Union_horn尾随空格保持。
既有花名Item原值无尾随空格的旧译亦逐字节保留，本批不暗改历史译文。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/coming-age-batch039/workspace
python build/batch-039-verification/verify_resources.py baseline
python build/batch-039-verification/verify_resources.py modified
python build/batch-039-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘原始资源SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新97条双盘回填一致，旧5,400条保留，12,679条仍为源值；独立回滚恢复5,400条，主修改产物保留5,497条。
未知值及重复key occurrence保持；错误hash回滚拒绝且不变。
干净Git index源码测试、108项依赖锁、164文件重建一致性与四组云端CI分别核查。
完整原文、容器、差异、基线与验证脚本只在build/batch-039-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究和回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线验证不代替游戏验收。
下一批审计第七章连续场景与雷/风试炼关联；第六章两处未知序列继续独立保留待查，不猜格式。
