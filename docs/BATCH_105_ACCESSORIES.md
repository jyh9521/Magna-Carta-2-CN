# 第一百零五批：基础与状态饰品（212条）

日期：2026-10-20。新增212条INT draft，累计11,848；新增65项candidate，共852，旧787保持。全部历史held原值保持，本批无新held。

## 完整功能组与上下文

- Accessory完整438字段，本批新增212（名称70、说明142），加旧1224_acc经验腰带名，现213/438有draft。覆盖1200–1269实际存在的基础/状态系列及三个旧式key；不存在1256/1257不造占位译文。
- 补齐每组名称/简述/全述，旧经验腰带名不重算；复用救援腰带、克服之戒、完美无缺之戒和属性/状态共享候选。旧译与旧787候选不改，不按配方key推断合成对象。
- 1233_Accessory与1233_acc同名，但旧式防御+30%、常规+10%；1263_Accessory黎明戒指攻击+30速度+10，而1263_acc清晨戒指免疫睡眠；1337旧式名力量与速度戒指独立保留，不覆盖常规key。
- 1240シモヤケ字面冻疮，1241추위寒冷，1242凍傷冻伤；各按实际源，不认为状态枚举相同。1252觉醒腰带为眩晕50%免疫，1255觉醒戒指为力竭免疫；元气戒指两个ID各保留。
- 50%免疫与完全免疫分别保留，不增补概率机制。1264四大属性异常不擅自列举，1265明确烧伤/冰冻/沉默/触电；1266全述四大属性以外的属性异常、简述其他异常各依源。
- 1227技能吊坠全述含升级时获得技能点数+50%，简述只含技能点数+50%；1240/1244/1254/1261的额外功能换行、行尾空格保持，不自动拉平说明。
- 76个加号、62个百分号、28对引号、146功能换行以及数字顺序/逐行边界空白保持。非剧情单句行不加句末句号。所有词条仅draft/candidate；Verified只指源值和离线结构，不是游戏显示/效果/官方中文验收。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-105-verification/reviewed-workspace
python build/batch-105-verification/verify_resources.py baseline
python build/batch-105-verification/verify_resources.py modified
python build/batch-105-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

源INT两盘SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；双盘同译文回填相同，旧11636及6328个其余源值保持，全部历史held独立核对。
基线1386测试；本批新增六项来源无关回归覆盖范围/旧ID/布局/差异/候选/输入锁与字幕。合批后统一完整验证，164工作区文件逐字节复现、索引导出干净源码测试、独立回滚和错误哈希拒写。
隔离回滚恢复11636条旧译，主MODIFIED_FILE仍11848；四个实物与精确命令/输入/字面结果/退出状态见build/batch-105-verification/VERIFICATION.txt。
仅清理经绝对路径约束的干净源码pyc；原盘/配置/存档/runs/当前包/基线/回滚/研究证据保持。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235、44字幕315cue保持；离线成功非游戏验收。验证清理提交推送核对后接续其余225条Accessory完整组（1270–1344），不把一次提交当全工程结束。
