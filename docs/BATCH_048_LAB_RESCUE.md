# 第四十八批：中央研究室对峙与紧急救援

日期：2026-10-20。新增INT90条，累计6,341条draft；310项共享candidate及1项历史字幕来源记录。
独立字幕新增9cue至30计划203/315cue；邮件114/235字段保持。均未人工定稿。

## 范围与上下文

- CSMB08_25/27/28/30/40五段56条：动力启动、尼克斯离开、洁菲与修恩扎伊特、两个艾尔加的对峙。
- Quest/08_802_0紧急救援22字段，Compose/Chapter08_16-26十一条停战传闻及撤离对白，CharacterName/Balfour姓名一条。
- 分类86 dialogue、2 name、1 quest_description、1 quest_progress；CSMB08达到172/239，Compose前26条有draft。
- 巴尔福依据Balfour键及韩文发音暂定；制动装置新增candidate。一号、主人、玛格纳卡尔塔、灾祸种及既有姓名复用候选。

Verified / source/offline：求救对白的2小时与任务DES的3分钟属于不同源字段，均保持。
In_1仍是“也许在第1研究室”，不将推测改为保证；救援成功/失败台词独立保留，不合并结局。
数值、QUEST%s、方括号、DES四处功能换行及空行保持；50条普通对白显式去硬换行。
已译通行卡第二occurrence与未译第一组钥匙全部保持，不按key去重。

## 独立字幕

csm08-30为2cue，csm08-40为7cue，实际来源Disc2；不从Coalesced推造字幕ID或时轴。
两盘ISO全hash、44成员源hash分别校验；原28计划194cue保持，新增两计划独立锁定。
时间、KRCC、BOM、br数量保持，空计划全字节roundtrip；独立回滚副本恢复，修改副本保留。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/lab-rescue-batch048/workspace
python build/batch-048-verification/verify_resources.py baseline
python build/batch-048-verification/verify_resources.py modified
python build/batch-048-verification/verify_resources.py rollback
python build/batch-048-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新90条两盘回填一致，旧6,251条保持，11,835条仍为源值；隔离回滚恢复6,251条，主产物仍有6,341条。
历史held/未知格式/重复key及旧译保持；错误hash回滚拒绝且不变。
干净index源码测试、129项依赖锁、164文件重建一致性及四组云端CI分开记录。
本轮开始检查第46/47批CI仍queued，无新增失败结论，不将排队记作通过。
完整源文、资源和验证证据只保存在build/batch-048-verification；公开计划仅存译文与源hash。

仅清理已核实绝对路径内、无入口依赖的再生pyc；保留原盘、配置、存档、runs、当前包、研究与回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批接CSMB08_50及后续主线、Compose08_27-30与同阶段NPC/任务；不重复本批对峙与两份字幕。
