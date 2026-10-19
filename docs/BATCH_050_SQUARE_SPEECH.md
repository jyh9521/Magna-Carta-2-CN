# 第五十批：广场演说与第九章开场

日期：2026-10-20。新增INT93条，累计6,538条draft；共享314项candidate及1项历史字幕来源记录保持。
字幕新增4cue至31计划207/315cue；邮件116/235字段保持。均未人工定稿。

## 范围与上下文

- CSMB09_20演说69个源字段中68条draft，1条异常源值保持；Compose/Chapter09前5条场地念白。
- NpcTalk/09_Velfort十六条、09_velfort_battle四条，同步覆盖停战传闻、演说准备及群众指控。
- 分类88 dialogue、5 narrative；当前CSMB09为68/169、Compose09为5/11，NPC09_两节20/20有draft。

Verified / source/offline：voc_csmb_0920_06源句中含감Ｒ异常混合字符、句段缺损。
双盘相同hash仅证明资源相同，不证明句意完整。该稳定ID/source hash记入review held_entries，保留原值，不猜补、不计draft。
完整原文仅留本地证据。其余对白按说话者分别保留：修恩扎伊特的自辩、群众指控、同伴反驳不是同一种叙述立场。
不将演说中关于先王、公主与战争的说法提升为已核实的全知事实。
拉·斯特拉达、斯特拉斯、KAN、玛格纳卡尔塔、灾祸种与既有姓名均复用共享候选，不新增术语，不标人工定稿。
64条普通对白显式去硬换行；数字、键位、未知字段与旧译保持。
09_zepi_3王之试炼及Compose09_06-11康复念白还未到本批阶段，继续保留未译。

## 独立字幕

csm09-10.txt四cue为演说之前的开场，实际来源Disc2。
profile对双盘ISO与44成员重新校验源hash；原30计划203cue逐字节保持，新增1份计划单独锁定。
时轴、KRCC、BOM及br保持，空计划全字节roundtrip、独立副本回滚恢复，修改副本保持。
csm09-40.txt后续25cue待对应场景，不提前混入开场。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/square-speech-batch050/workspace
python build/batch-050-verification/verify_resources.py baseline
python build/batch-050-verification/verify_resources.py modified
python build/batch-050-verification/verify_resources.py rollback
python build/batch-050-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增93条两盘回填一致，旧6,445条保持，11,638条仍为源值；隔离回滚恢复6,445条，主修改产物仍保留6,538条。
全部历史held与本批异常字段保持；重复key occurrence不变。干净index源码测试、134项依赖锁、164文件重建一致性另行验证。
第46批CI run39280617531四组Ubuntu/Windows、Python3.12/3.14已completed/success，证据保存在本批忽略目录；第47-49批本轮开始仍queued，不记作成功。
仅清理核实绝对路径内、可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB09_30/35/36接续到csm09-40对应场景及之后主线；同阶段补关联任务，异常0920_06继续待查。
