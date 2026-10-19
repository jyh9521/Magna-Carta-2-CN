# 第三十批：第五章任务、E05邮件与利安达尔关联字段

日期：2026-10-19。新增INT119条，累计4,580条draft；210项candidate，0项人工reviewed。
字幕profile22份154/315cue保持。

## 补齐范围

- Quest/05_112_0/120_0/131_0/136_0/209_0/218_0：25/16/16/17/15/11，共100字段。
- QubeMail/E05_001–008：八封邮件16个主题/正文字段。
- Item/Ingredient/liandal、liandal_D及UI/information/liandal：3个关联字段。
- 分类79 dialogue、1 menu、6 quest_description、8 name、5 quest_progress、3 quest_objective、8 mail_subject、8 mail_body、1 item_description。

Verified / source/offline：Quest/05_十组157字段、E05八封16字段全部有draft。
连同前批第五章主线432/433（070_27占位待查）、Compose75、NpcTalk/05_46与四份字幕13cue，
只是明确资源前缀覆盖，不代表整章所有可见文字或全文完成，也不是游戏验收。
所有邮件当前86/235字段有draft，其余149字段按各自阶段审计。

任务接受/拒绝/进行/完成与海岸/森林状态独立保留，不把早期联络任务改成战后现况。
源提到朱特曾采坏药草，按角色原话翻译；第一章Ch01_103_1同植物任务仍是早期未译缺口，未冒称已补齐。
利安达尔果实新增candidate，利安达尔为同一基名的暂定音译；Item/UI统一，未人工定稿。
“不死怪物”是任务发言者称呼，关于露的提示仍为“也许”疑问，不补写原文未给的机制答案。
八封邮件按发信立场保留担忧、感谢与战争疲惫，不凭推测补署名或改成主线最终状态。

五个DES保留7个硬换行，X/Y菜单1个，邮件正文53个，共14字段61个保留换行；
邮件空段落位置、样式标签、8名/15名以上目标、标题2、LV2、QUEST/Quest大小写及占位符/空格/冒号保持。
54条普通对白去硬换行显式记录line_break_policy。com_2尾随1空格、131DES尾随2、
136/218DES尾随1及liandal名称尾随1空格保持；其他源尾随空白逐字段核验。

字幕profile和22份计划逐字节保持旧HEAD，本批不重读完整ISO，不把旧字幕证明称为新增验证。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/chapter05-support-batch030/workspace
python build/batch-030-verification/verify_resources.py baseline
python build/batch-030-verification/verify_resources.py modified
python build/batch-030-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘原hash保持，119条新值回填一致；旧4,461条保留，13,596条仍为源值。
独立回滚恢复4,461条基线，主MODIFIED_FILE.int保留4,580条；错误hash输入拒绝且不变。
干净Git index源码测试、85项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文/资源与本机验证脚本只在build/batch-030-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批按源顺序接CSMB06与同阶段NPC/任务/独立字幕，后续另审计早期任务和其他邮件缺口。
