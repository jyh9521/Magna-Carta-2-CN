# 第四十一批：南部军关卡、劳德证言与贝尔福特路线

日期：2026-10-19。新增INT94条，累计5,691条draft；259项共享candidate及1项独立字幕candidate。
字幕28份194/315cue、邮件98/235字段不变，全部未人工定稿。

## 范围与语境

- CSMB07_25关卡拦阻21、CSMB07_30劳德制止交战与证言46，共67条。
- Compose/Chapter07第06-25、31、34-38共26字段；FieldName/Velfort/Starlightfield一字段。
- 分类86 dialogue、5 narrative、2 system_message、1 name。

Verified / source/offline：所有新增ID与前40批无重叠。CSMB07主线153/282有draft，Compose33/40。
劳德亲眼见到秘密会面、推断绑架阴谋和私下调查后的怀疑分别保持证言与推测，不升级为全知旁白。
士兵的叛徒指认、同伴反驳和劳德的撤退命令保留说话者立场。哨兵制造方法/弱点仅译虚构情报，未补技术细节。
亚历克斯先往阿巴泽特与主角去贝尔福特的不同路线、消息时间及称谓自我修正保持。
市民/公主安全与不让南部军同行引发全面交战的理由完整保留。
星光平原新增一项candidate，与关联FieldName一致；其余人名/地区复用旧候选。

2条路障/捷径系统提示保留两个功能换行；60条普通对白/括号念白有显式去硬换行策略。
第七章独立csm07-10此前已全7cue；本批字幕profile/28计划及一号字幕候选逐字节保持，不重读完整ISO。
07_velfort城内NPC、07_701_0情报员任务及Compose26-30/39-40属于后续救援/进城阶段，仍待接续。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/road-velfort-batch041/workspace
python build/batch-041-verification/verify_resources.py baseline
python build/batch-041-verification/verify_resources.py modified
python build/batch-041-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新94条双盘回填一致，旧5,597条保留，12,485条仍为源值；独立回滚恢复5,597条，主修改产物保留5,691条。
第六章两处未知反斜线与所有历史held/旧译/重复key occurrence保持；错误hash回滚拒绝且不变。
干净Git index源码测试、113项依赖锁、164文件重建一致性与四组云端CI分别核对。
完整原文、容器、差异、基线和本机验证脚本只留build/batch-041-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究和回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批从CSMB07_40接续贝尔福特/情报员救援及关联NPC/任务，再补余下场地提示与技能字段。
