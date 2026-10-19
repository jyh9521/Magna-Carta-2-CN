# 第二十六批：风息岛双线作战、解放与归村

日期：2026-10-19。新增INT167条，累计4,113条draft；207项candidate，0项人工reviewed。
独立字幕profile19份149/315cue保持不变。

## 场景、NPC及关联战斗提示

- CSMB05_040/046/050/055/055_1/056/060：分别19/12/19/4/4/9/24，共91条。
- MC2NpcTalk/05_chinook：31条，解放后村民感激、担忧、怨恨、丧亲悲伤和复仇诉求分别保留。
- MC2Compose/Chapter05_01–19、24–49：45条，包括19个进度字段与12条括号内心念白。
- 分类135 dialogue、19 quest_progress、13 narrative；与前25批不重叠。

Verified / source/offline：森林/海岸分组、杰巴萨目标、死亡弩炮及屏障装置提示与当前行动相关。
死亡弩炮共4台、每1台的守兵、15名北部军目标及15/4分母、进度序号全部字面保持。
进度与念白保留ASCII括号，杰巴萨提示保留方括号；85条去源硬换行记录显式line_break_policy。
CSMB05_050里源key本来包含05051后缀，055_1是独立section；不补造或改写ID。

杰巴萨新增candidate；当前CharacterName/FieldName/Item源目录未发现同名关联字段，未编造姓名ID。
青灵森林、死亡弩炮等复用已有candidate，不宣称官方英文或跨作身份已核实。
朱特对村长说梅莉莎在阿巴泽特养伤，译文保持角色原话，不改成旁白事实，不暗改已译的北部军情节。
村民的复仇、责难与感谢都是角色立场，不相互抹平；解放不抹去丧亲者悲伤。

本阶段csm05-10归队字幕已在25批完成，不重复；后续82/85/90五条尚未到相应场景。
本批字幕profile和既有19份计划逐字节保持旧HEAD，不重读完整ISO，不将旧字幕证明当作新增验证。
05_chinook31/31有draft；05_chinook_s八条及第五章任务尚待后续，不能泛称全章覆盖。

## 可复现验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/island-liberation-batch026/current-workspace
python build/batch-026-verification/verify_resources.py baseline
python build/batch-026-verification/verify_resources.py modified
python build/batch-026-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT源hash不变，167条新值双盘回填一致；旧3,946条保留，14,063条仍为源值。
独立副本回滚恢复3,946条基线，主MODIFIED_FILE.int保持4,113条；错误hash输入拒绝且不变。
干净Git index源码测试、74项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-026-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB05_070（40条）开始，按村长请求衔接任务、05_chinook_s与同阶段字幕。
