# 第五十三批：取回卡蒙德与精神世界入口

日期：2026-10-20。新增INT87条，累计6,846条draft；321项共享candidate及1项历史字幕来源记录。
字幕33计划234/315cue、邮件116/235字段保持，均未人工定稿。

## 范围与上下文

- CSMB10_32/33/35/36/37五段69条，Compose/Chapter10前4字段，Quest/10_Juto_2十二字段，Item/Valuables超越卡蒙德名称/说明两字段。
- 分类77 dialogue、3 narrative、3 name、2 quest_progress、1 quest_description、1 item_description。
- 第十章主线当前141条draft，Compose前4字段、10_Juto_0/1/2三组30字段已有draft；未泛称全章可见文字完成。

Verified / source/offline：取回卡蒙德、进入精神世界与留守保护尼克斯是相邻但不同视角。
精神接触最多2人、尼克斯倒下会失败、幻象与现实的区别都按角色说法保留。
不把精神中的失忆写成现实中新发生的确证事实，不提前写后续康复结果。
精神接触的无空格/有空格韩文形式统一候选中文；精神世界、超越卡蒙德新增候选，合计4项。
Item说明保留“据说”的传闻语气，不把复活描述改成已验证的游戏机制。

35条普通对白/念白显式去硬换行；DES两处功能换行、QUEST%s、数值2及其他机器标记保持。
前批NPC10_kotamare已覆盖当前阶段；10_kotamare_battle提及实际入侵，不能仅凭battle后缀当精神黑暗战斗提前混译。
历史0920_06异常源及HP数值拼接日志两个held字段保持，旧译与重复key occurrence不改。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/mind-entry-batch053/final-workspace
python build/batch-053-verification/verify_resources.py baseline
python build/batch-053-verification/verify_resources.py modified
python build/batch-053-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增87条两盘回填一致，旧6,759条保留，11,330条仍为源值；隔离回滚恢复6,759条，主产物保持6,846条。
干净index源码测试、142项依赖锁、164文件重建一致性、历史held与错误hash回滚拒绝分别验证。
本批没有新字幕；原profile与33计划234cue逐字节冻结，不重复导出ISO；csm10-65/70仍待对应场景。
本轮查到第52批CI run39287489967四组均completed/success，完整证据仅留忽略目录。
仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批接CSMB10_40及精神世界的后续，与现实侧场景交替接续，按阶段补场地念白/NPC/任务，不能预译康复结果。
