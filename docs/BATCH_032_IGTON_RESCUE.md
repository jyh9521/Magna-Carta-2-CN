# 第三十二批：伊格顿获救、前线重逢与拉提女王支线

日期：2026-10-19。新增INT124条，累计4,841条draft；218项candidate、0项人工reviewed。
独立字幕新增7cue，累计161/315cue，profile23份计划。

## 场景与同阶段补齐

- CSMB06_030/031/040/060/070：12/12/20/11/14，共69条。
- NpcTalk/06_Abajet源序第21至50条：26条draft、4条删除标记保留。
- Quest/06_203_0与06_225_0：15/12，共27条，衔接九节草/生物学家的女王与面具任务。
- Item/Valuables/broken_maskofqueenrati及说明：2条；csm06-35独立字幕7cue。
- 分类112 dialogue、2 quest_description、3 name、3 quest_progress、3 quest_objective、1 item_description。

Verified / source/offline：新增ID与前31批不重叠。06_Abajet已检查前50条，46条draft，
233/234/2201/2207四个源删除标记保持原值；不翻译成玩家对白，不计draft。后续从源序偏移50接续，
不能按已译46条偏移造成重复或跳过。源id、occurrence和两种NPC阶段均不合并。

伊格顿的梦想、研究与被冤枉经历按其自述；亚历克斯契约和梅莉莎未说完的话不补身份结论。
拉提女王、拉提女王的面具碎片新增candidate；CharacterName中未找到女王源姓名字段，未编造关联ID。
任务的接受/拒绝/进行/完成分别保留；游戏内种族、卵和毒药均按虚构支线原意翻译，不扩展现实步骤。

两个DES各保留1个功能换行，80条普通对白去源硬换行逐条声明line_break_policy。
QUEST%s及另两个%s、原空格/冒号、方括号、goal和面具名称尾随空格保持。
新字幕保留时间轴、KRCC/BOM和5个br；实际源来自Disc2，旧154cue逐字段保持。
35位于031/040之间救出伊格顿的语义衔接为源编号和台词推定，不称游戏内触发顺序验收。
后段80/90/120/122共26cue仍待按场景推进；未知反斜线/占位/空白等旧值不改。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/igton-rescue-batch032/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-032-verification/subtitle-catalogs
python build/batch-032-verification/verify_resources.py baseline
python build/batch-032-verification/verify_resources.py modified
python build/batch-032-verification/verify_resources.py rollback
python build/batch-032-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT原hash保持，124条新值回填一致；旧4,717条保留，13,335条仍为源值。
独立回滚恢复4,717条基线，主MODIFIED_FILE.int保持4,841条；错误hash输入拒绝且不变。
字幕导出重新核验双盘ISO完整hash及44份文本成员，不输出整盘副本；字幕独立回滚恢复，修改副本保留。
干净Git index源码测试、90项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-032-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批接相邻csm06-80/90和CSMB06_100/110/121，再补120/122后段字幕；城镇NPC从源序偏移50继续。
