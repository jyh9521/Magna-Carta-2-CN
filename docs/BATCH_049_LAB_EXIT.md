# 第四十九批：研究所撤离与第八章关联任务收尾

日期：2026-10-20。新增INT104条，累计6,445条draft；314项共享candidate及1项历史字幕来源记录。
独立字幕30计划203/315cue保持；邮件新增2字段至116/235。均未人工定稿。

## 范围与上下文

- CSMB08_50/55/58/60/70/80六段67条；Compose/Chapter08_27-30四条等候露的场地念白。
- Quest/08_cerestin_0三字段、08_802_1十五字段、08_Qube_1十字段；Q08_qube_1主题/正文两字段。
- Item/Valuables制造室通行卡及说明、北部军保管箱钥匙三字段。
- 分类80 dialogue、7 narrative、6 quest_progress、5 name、3 quest_description、1 mail_subject、1 mail_body、1 item_description。

Verified / source/offline：INT明确前缀CSMB08为239/239、Compose08为30/30、Quest08_七组91/91有draft。
这不是第八章全部可见文本完成声明；字幕、邮件、硬编码、图片与游戏内布局仍分别审计。
队伍退出研究所、准备去广场；先王死因保留为角色质问及回避回答，不补后续结论。
主角三条第一人称念白及四条括号场地念白区分于对白。临时安全、停战传闻与血统解释均保持说话者立场。

制造室、制造室钥匙、制造室通行卡、北部军保管箱钥匙新增4项candidate。
任务/对白称钥匙，Item名称称通行卡，两者源差异保持，不未经验证统一。
杰巴萨、雷卡斯沿用候选；不把雷卡斯与贝卡斯视作同一角色或拼写错误。
59条普通对白/念白显式去硬换行；三项DES、邮件正文功能换行与空行、QUEST%s、数值、括号/方括号及钥匙尾随空格保持。
旧通行卡第二occurrence与第一组钥匙原值保持；历史held/未知格式不改。
本批无新增字幕，原30计划与profile、历史一号字幕来源记录逐字节冻结，不重复读取ISO或复制视频。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/lab-exit-batch049/current-workspace
python build/batch-049-verification/verify_resources.py baseline
python build/batch-049-verification/verify_resources.py modified
python build/batch-049-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增104条两盘回填一致，旧6,341条保留，11,731条仍为源值；隔离回滚恢复6,341条，主产物仍保留6,445条。
干净index源码测试、131项依赖锁、164文件重建一致性、错误hash回滚拒绝及四组云端CI分开记录。
本轮开始查到第46/47/48批仍queued，第45批completed/success；排队不是通过，也没有新失败结论。
完整源文、资源和验证证据仅存build/batch-049-verification，不提交完整游戏资产。

仅清理核实路径内可再生且无依赖的验证pyc，保留原盘/配置/存档/runs/当前包与研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字体/TOC/可玩入口；离线成功不代替游戏验收。
下一批从CSMB09开场及同阶段NPC/任务/关联名称与独立字幕接续，不重复已完成的第八章明确前缀。
