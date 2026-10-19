# 第三十六批：休息站助手、寻物与拉诺阿拉湖任务

日期：2026-10-19。新增INT73条，累计5,273条draft；231项共享candidate及1项独立字幕candidate。
字幕27份187/315cue保持原样，均未人工定稿。

## 上下文与范围

- Quest/06_601_0寻找助手16字段；06_602_0丢失物品20字段。
- 06_603_0护送14字段，603_0包含未知反斜线序列，保持原值，不计draft；不得宣称整段完成。
- 06_603_1拉诺阿拉湖怪物17字段。
- CSMBQ06_040拜泽恩日记反应2条；Item/Valuables四字段（Diary/Diary_D/small_box/small_box_D）。
- 分类55 dialogue、6 name、4 quest_description、3 quest_progress、3 quest_objective、2 item_description。

Verified / source/offline：所有新增ID与前35批无重叠，双盘输入hash保持；Quest/06_由50增至117/316，剩199字段。
助手自己的日记已经找到，拾得日记与拜泽恩关联只译原有对白，不额外补写身份结论。
拜泽恩、银白的拜泽恩及地区名称复用旧候选；不覆盖旧姓名字段。
日记、破旧的日记、小袋子新增三个候选，QUEST和方括号保持。
36条普通对白去硬换行有显式line_break_policy，四条DES功能换行及Diary末尾空格保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/rest-stop-batch036/current-workspace
python build/batch-036-verification/verify_resources.py baseline
python build/batch-036-verification/verify_resources.py modified
python build/batch-036-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

工作区输出须全新；早期未写plan前一次预检查工作区留作证据，current-workspace才是本批维护输出。
原始资源SHA256：179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
双盘回填新73条一致，旧5,200条保留，12,903条仍为源值；独立回滚恢复5,200条，主MODIFIED_FILE保留5,273条。
校验功能换行、占位符、数值、重复key occurrence及全部历史held项；错误hash回滚拒绝且不变。
干净Git index源码测试、102项输入依赖锁、164文件重建一致性和推送后四组CI分别核对。
完整原文、资源、差异及验证脚本只留build/batch-036-verification，不提交Git。

仅清理经绝对路径核实可再生、无入口依赖的验证pyc；原盘/配置/存档/runs/当前包及基线和研究证据保持。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/现有测试入口；离线成功不代替游戏验收。
下一批先接续休息站关联06_605_0/605_1、06_670_0及同阶段邮件；王之试炼与两处未知格式继续单独审计。
