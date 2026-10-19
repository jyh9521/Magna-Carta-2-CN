# 第三十七批：杜南盗贼、投降部队与第六章邮件

日期：2026-10-19。新增INT58条，累计5,331条draft；234项共享candidate及1项独立字幕candidate。
字幕27份187/315cue不变，所有新译与术语仍未人工定稿。

## 场景与范围

- Quest/06_605_0休息站盗贼16、06_605_1盗贼窝点15、06_670_0投降部队队长15，共46字段。
- E06_001/002/003三封及Q06_qube_1/2两封：5主题、5正文，共10字段。
- CharacterName/madmac与FieldName/Dunan_Field/Outlaws_basement两个关联字段。
- 分类38 dialogue、5 name、5 mail_subject、5 mail_body、3 quest_description、1 quest_progress、1 quest_objective。

Verified / source/offline：新增ID与前36批无重叠。Quest/06_由117增至163/316，余153字段；
邮件由86增至96/235字段，余139字段。235为邮件字段数，不是信件封数。
麦德麦克、杜南盗贼、杜南盗贼窝点新增3项候选；其余地区、人名、反哨兵部队、连携奥义复用旧候选。
605_0复仇指认保持说话者立场，不补写主角已犯案；670_0救援前后的士兵/队长人称不合并。
Q06任务通知仅译游戏原文，不补写制药配方。E06_003保留双手剑/扇子、每人所需KAN至少5个、
双方进入连锁状态与方向键右的操作条件，不能误译成总共5个或任意一人连锁。

3条DES与5封正文合计37个功能换行保持，邮件空段落索引不变；32条对白按显式策略去硬换行。
任务标题(2)、QUEST标识、括号、数值、稳定ID、重复key occurrence均保持。
两个第六章未知反斜线条目及全部历史held值不变；不将未知值照抄计作draft。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/dunan-support-batch037/verified-workspace
python build/batch-037-verification/verify_resources.py baseline
python build/batch-037-verification/verify_resources.py modified
python build/batch-037-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新，verified-workspace为最终输入锁；保留早期样式拒绝/说明文字修订前的工作区证据。
双盘原始资源SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新58条回填一致，旧5,273条保留，12,845条仍为源值。独立回滚恢复5,273条，主MODIFIED_FILE保留5,331条。
错误hash回滚拒绝且不变；干净Git index源码测试、104项依赖锁、164文件重建一致性与四组云端CI分别检查。
完整原文、容器、验证脚本及差异只在build/batch-037-verification，不进入Git。

仅清理绝对路径核实可再生且无入口依赖的验证pyc；原盘/配置/存档/runs/当前包及必要研究和回滚证据保留。
未生成ISO或整盘副本，未启动模拟器，未更新字库/TOC/可玩入口；离线验证不代替游戏验收。
下一批接续成人礼/王之试炼与06_301_0等杜南关联任务；先审计源中的未知序列，再独立保留待查项。
