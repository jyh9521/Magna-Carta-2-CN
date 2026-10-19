# 第二十八批：中毒余波、萤火与继续并肩作战的决定

日期：2026-10-19。新增INT110条，累计4,345条draft；208项candidate、0项人工reviewed保持。
独立字幕新增3cue，累计152/315cue，profile21份锁定计划。

## 连续场景与独立字幕

- CSMB05_086/087_1/088：分别63/36/11，共110条，104 dialogue、6 narrative。
- MC2Game/Movies/csm05-82.txt一条、csm05-85.txt两条；csm05-90两条未提前翻译。
- 当前阶段的任务、独立NPC状态和Compose提示在前批保留，不重复导入旧ID；本批无新术语或名称字段。

Verified / source/offline：与前27批无重叠，48条普通对白/叙述显式去源硬换行。
086中朱特先敬称公主、发怒后直呼、道歉恢复敬称、获准后改叫洁菲，按顺序保留；
“不再用敬语”的源解释不删除，不把情感转变压成同一口吻。6条叙述保留朱特第一人称回忆视角。
对制造哨兵者身份、能否说服梅莉莎、战争结束与回岛的条件均保持原语气，不提前改写剧情结局。
中毒、连环术与马雷族解毒剂仅为游戏剧情设定，不扩展成现实医疗说明。
087_1作为原section保留，不补造未出现的087场。

两份新字幕独立锁定完整源文件hash、cue源hash、start/end，保留KRCC/BOM和1个br标记。
82/85与086受袭/中毒余波语义衔接属源编号与台词的高可信推定，静态对照并非游戏内触发顺序验收。
旧149cue逐字段保持，csm05现11/13cue有draft，后段90两条仍需随089系列场景核对。
既有208项术语数据与GLOSSARY逐字节保持旧HEAD，不把自动校验升级成人工定稿。
070_27编辑占位及其他未知/空白/标记继续保持源值。

## 可复现验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/fireflies-batch028/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-028-verification/subtitle-catalogs
python build/batch-028-verification/verify_resources.py baseline
python build/batch-028-verification/verify_resources.py modified
python build/batch-028-verification/verify_resources.py rollback
python build/batch-028-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT源hash不变，110条新值回填一致；旧4,235条保持，13,831条仍为源值。
独立副本回滚恢复4,235条基线，主MODIFIED_FILE.int保持4,345条；错误hash输入拒绝且不变。
字幕导出重新核验双盘ISO完整hash及44份文本成员，不输出整盘副本；字幕独立回滚恢复，修改副本保留。
干净Git index源码测试、80项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文/资源及本机验证脚本只在build/batch-028-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB05_089（17条）开始，随后089_1/089_2及100/110，衔接村长后续情报、独立字幕和相关任务。
