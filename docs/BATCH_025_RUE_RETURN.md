# 第二十五批：露归队、血之契约与收复风息岛的请求

日期：2026-10-19。新增INT99条，累计3,946条draft；206项candidate，0项人工reviewed。
独立字幕新增8cue，累计149/315cue，19份锁定计划。

## 场景与关联内容

- CSMB05_001/020/030/031：分别10/29/26/23条，共88条。
- MC2NpcTalk/05_harbor：7条，保留禁航期间旅客焦虑、抱怨与安全解释的不同立场。
- MC2Compose/Chapter05_20–23：4条，出航询问、X/Y选择、出发和未就绪回应。
- MC2Game/Movies/csm05-10.txt：露归队独立字幕8cue，衔接001迎接与020训话/介绍。

Verified / source/offline：上述新增ID与前24批无重叠。98 dialogue、1 menu。
血之契约/主人新增candidate；KAN、卡蒙德、连环术、守护者、贝尔福特与风息岛等复用既有候选。
露对修恩扎伊特施术能力的疑问、对强化型哨兵用途的推测、亚历克斯关于战争和救岛的立场均按角色表述翻译，
不将传闻/推测变为叙述事实，也不擅自说明朱特失忆或二人似曾相识的原因。
先王的称呼按当前对白保留，不暗改旧邮件或给未明示的称呼补充身份。

普通对白去源硬换行时逐条写入line_break_policy；X/Y菜单保留样式标签、键位及1个功能换行。
新字幕保留全部时间轴、KRCC、BOM及3个br标记；既有141cue逐字段不变。
csm05-82/85/90共5cue属于后段，本批仅做清点，留到对应剧情；不提前把第五章全部字幕标成已译。
05_chinook解放后NPC及05_前缀任务还有缺口，尚非第五章全覆盖。

## 可复现验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/rue-return-batch025/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-025-verification/subtitle-catalogs
python build/batch-025-verification/verify_resources.py baseline
python build/batch-025-verification/verify_resources.py modified
python build/batch-025-verification/verify_resources.py rollback
python build/batch-025-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT源hash不变，99条新值双盘回填字节一致；旧3,847条保持，14,230条仍为源值。
独立副本回滚恢复3,847条基线，主MODIFIED_FILE.int保持3,946条；错误hash输入拒绝且不变。
字幕导出重新核验双盘ISO完整hash及44份文本成员来源，不输出整盘副本；源字幕独立回滚恢复、修改副本保留。
干净Git index源码测试、72项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文/资源/本机验证脚本只在build/batch-025-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB05_040继续，并按实际场景关联补齐第五章任务与NPC，不重复已译归队字幕。
