# 第一百零六批：特殊与复合饰品（225条）

日期：2026-10-20。第105批完成清理/提交/推送并核对HEAD与远端一致、工作区干净后，直接接续本批225条INT draft，累计12,073；新增33项candidate，共885，旧852保持。

## 完整功能组与源上下文

- Accessory剩余1270–1344的75组名称/简述/全述225字段合批，现完整438/438字段有draft，不称全部游戏翻译或人工/游戏验收完成。
- 复用旧配方基础名和独立饰品候选42项，包括生命与隼、力量与守护、魔力与勇气、雪水晶、连环术师吊坠、铁壁之心等；不因配方顺序或数字key建立未经验证的合成映射。
- 财富耳环/项链额外SID分别10/20%，祭品戒指ＳＩＤ30%为全角字母；KAN生成量1．5倍的全角小数点和耐力消耗－10/20%的全角减号保持。力量KAN/属性KAN复用既有译库，不把生成量变成直接恢复量。
- 复活耳环/项链/戒指全述含死亡时以30/50/80%体力自动复活，使用一次后饰品损坏；简述不补全述的死亡/损坏条件。只翻译显示资源，不声称已验证触发或消耗机制。
- 1290体力30%速度15、1291体力10%速度20、1292体力30%速度10分别保持，不按数列规律纠错；1337常规攻击20速度10与旧式攻击30速度10分别保留。
- 名称中的隼不按属性改成迅捷；力量与魔力不误替换成魔力量。1342/1343按猫猫关联与喵语气翻译，~与～各依源；1344全述艾尔加耳环/简述饰品各独立保持。
- 206加号、52百分号、10全角小数点、2处ＳＩＤ、4全角减号、3半角~及1全角～、153功能换行和逐行边界空白保持。非剧情单句不加句末句号，所有历史held原值/hash不动，本批无新held。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-106-verification/final-workspace
python build/batch-106-verification/verify_resources.py baseline
python build/batch-106-verification/verify_resources.py modified
python build/batch-106-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

源INT双盘SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；双盘回填相同，旧11848和6103个其余源值保持，所有历史held独立核对。
基线1392测试，新增六项source-free合同覆盖225字段/旧ID/布局/特殊形态与条件/候选复用/输入锁和字幕；完整验证含164工作区文件逐字节复现、索引导出干净源码测试、独立回滚及错误哈希拒写。
隔离回滚恢复11848条旧译，主MODIFIED_FILE仍12073；四实物及精确命令/输入/字面结果/退出状态见build/batch-106-verification/VERIFICATION.txt。
只清理核实绝对路径的干净源码可再生成pyc；保留原盘/配置/存档/runs/当前包/入口依赖/基线/回滚/研究。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235、44字幕315cue保持；离线成功不等于游戏验收。验证清理提交推送核对后继续朱特/洁菲装备206字段功能组，完整其余物品596字段另存待审，不把含工具/样本的6103原值当玩家待译总量。
