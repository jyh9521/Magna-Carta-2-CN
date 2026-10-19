# 第五十二批：柯塔马雷诊治与海底怪物线索

日期：2026-10-20。新增INT115条，累计6,759条draft；317项共享candidate及1项历史字幕来源记录。
独立字幕新增2cue至33计划234/315cue；邮件116/235保持，均未人工定稿。

## 范围与上下文

- CSMB10_20/30两段72条，NPC/10_kotamare二十三条，Quest/10_Juto_0/1十八字段，Item/FieldAction觉醒之香名称/说明两字段。
- 分类109 dialogue、3 name、2 quest_description、1 item_description；只覆盖开场诊治与寻找怪物线索，不提前写康复、精神世界或梅莉莎到访结果。
- 佐帕、觉醒之香新增2项candidate，复用主人、哨兵、卡蒙德、血之契约、尼克斯、凯汀、斯维汀等候选。

Verified / source/offline：尼克斯对更换主人的设想仍是从未尝试且危险的游戏幻想术式，不改成已验证疗法或成功结果，不补现实技术参数。
NPC309_0的동생结合第三章及第六章同角色既有译文统一为妹妹；斯维汀的中性原文不另补性别。
强行惊醒与先用觉醒之香两种情况区分，原方括号、DES功能换行、香名尾随空格保持；69条普通对白显式去硬换行。
10_Juto_2取回卡蒙德、康复后NPC与精神世界念白仍待后续场景；雷之试炼23字段未提前计入。
历史0920_06异常源与HP拼接日志两个held字段保持，旧译与重复key occurrence不改。

## 独立字幕

csm10-10.txt两cue实际来源Disc2，时序在CSMB10_20之前。
双盘ISO与44成员源hash重新校验两轮，原32计划232cue逐字节保持，新计划单独锁定。
时轴、KRCC、BOM、br保持；空计划全字节roundtrip，隔离副本回滚恢复，修改副本保留。
csm10-65/70后续20cue待对应场景，不提前混入开场。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/kota-care-batch052/final-workspace
python build/batch-052-verification/verify_resources.py baseline
python build/batch-052-verification/verify_resources.py modified
python build/batch-052-verification/verify_resources.py rollback
python build/batch-052-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增115条两盘回填一致，旧6,644条保留，11,417条仍为源值；隔离回滚恢复6,644条，主产物保持6,759条。
干净index源码测试、140项依赖锁、164文件重建一致性、历史held与错误hash回滚拒绝分开验证。
本轮开始核对第50批CI已completed/success，第51批仍queued，不将pending写成成功。
仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批接CSMB10_32/33起的寻找卡蒙德及精神世界阶段、10_Juto_2与关联名称/物品；同阶段补场地念白与NPC，不重复本批诊治。
