# 第五十一批：广场营救与贝尔福特撤离

日期：2026-10-20。新增INT106条，累计6,644条draft；315项共享candidate及1项历史字幕来源记录。
字幕新增25cue至32计划232/315cue；邮件116/235字段保持，均未人工定稿。

## 范围与上下文

- CSMB09_30/35/36/50/55/57/60/70八段100条，Compose/Chapter09_06-11六条康复相关场地念白。
- 分类97 dialogue、9 narrative；CSMB09明确前缀168/169有draft，唯一0920_06异常源仍保留；Compose09 11/11、上一批NPC09两节20/20有draft。
- 09_zepi_3雷之试炼23字段仍待对应阶段，不将这些明确前缀覆盖说成全部可见文字完成。

Verified / source/offline：主角受伤、逃往柯塔马雷、梅莉莎与克蕾尔对质、难民去向都按原说话者立场翻译。
关于伤势秘密、灾祸种人为因素和失踪难民仍保留提问/暗示，不补成已证实结论。
0957_06-08为第一人称念白，Compose为括号场地念白；52条普通对白/念白显式去硬换行。
别西卜为벨제붑暂定candidate，实际锚定本批Boss对白，不核定官方名称或其他变体关系。

## 关联战斗日志片段待查

Verified / source：MC2UI.int Battle_Log/beeljebubRecover_1与_2是主语片段和带助词的HP后缀片段。
Unverified：运行时数值夹入位置、拼接顺序与中文重组方式尚无调用证据。
两字段完整ID/hash列入review held_entries，原值保持，不只改单独Boss主语，不计draft。
旧0920_06混合异常源与历史unknown/held全部保持。

## 独立字幕

csm09-40.txt二十五cue，实际来源Disc2；位于09_36与09_50之间，营救及后续伤势语境已结合前后剧情核读。
双盘ISO与44成员全源hash重新校验两轮；原31计划207cue逐字节保持，新增1计划独立锁定。
时轴、KRCC、BOM、15个br保持；空计划全字节roundtrip，隔离回滚副本恢复，修改副本保留。
第九章两份字幕29/29cue有draft，未刷新字体/TOC/玩家入口，仍需游戏内验收。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/square-rescue-batch051/current-workspace
python build/batch-051-verification/verify_resources.py baseline
python build/batch-051-verification/verify_resources.py modified
python build/batch-051-verification/verify_resources.py rollback
python build/batch-051-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增106条两盘回填一致，旧6,538条保持，11,532条仍为源值；隔离回滚恢复6,538条，主修改产物保留6,644条。
历史held、本批两个日志片段、重复key occurrence、未改数值和键位均独立验证。
干净index源码测试、137项依赖锁、164文件重建一致性与错误hash回滚拒绝分别核对。
本轮复核第47批CI run39281739035四组已completed/success，第48-50批仍queued；排队不记作通过。
仅清理已核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批接CSMB10开场、柯塔马雷康复阶段及对应NPC/任务/独立字幕；雷之试炼按同阶段上下文补齐，原异常源和日志片段继续待查。
