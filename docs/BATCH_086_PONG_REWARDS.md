# 第八十六批：抓蓬蓬玩法与奖励

日期：2026-10-20。新增INT40条，累计8,973条draft；共享candidate415项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- pong game NPC25、Recover三物品名/D/S九、英雄卡蒙德名/D/S三、Tutorial_Scene_21三同步；21 dialogue、4 system_message、5 name、6 item_description、2 effect_description、2 tutorial。
- 14条普通对白显式去硬换行，19个价格/奖品表/名字/效果/教程等功能字段保留布局。数字、%/SID、括号、键位、控制码、前后空白保持，六条恢复品说明源尾空格逐项保留。
- 蓬蓬/抓蓬蓬沿用旧候选，核读旧Ch02_Abazet、Ch02_227_0狩猎任务与实际奖励物品/教程；普通狩猎不是小游戏奖励机制。Q02_237_0风异常弱点邮件待完整组处理，不顺便并入本批。
- 1000SID、20/25/30分档、首次英雄卡蒙德/后续苏生丸与3岁数字保持。score源说超过20分，而奖品表列20分，各自依源保留，不擅自统一大于/大于等于；实际阈值与奖励绑定仍待游戏验证。
- 新增治愈叶힐 리프、疗愈花큐어 플라워、英雄卡蒙德영웅의 카몬드、苏生丸소생환四项candidate，旧411项保持；苏生丸原汉字/官方名未核。恢复1人700、全体1500、全体战斗不能者20%及卡蒙德攻击+10/防御+10依源，不当实测数值。
- 仅阿尔戈、持锤、限时和捕捉越多得分越高按教程表达，不补键位、时长或积分公式。观众失望、闹别扭、鼓劲与想要玩偶分别保留，不把玩偶自动列为实际奖品。
- NPC小游戏25为真实可读玩法/观众发言，不与06_Abajet25旧held混淆。ruhalt/698_0一条仍待人物上下文核读；所有旧held、重复occurrence、旧译与44字幕315/315已提取cue保持。
- 邮件128/235和README不变，仍有任务/教程/物品/技能待译及工具/样本需辨别，不用其余原值直接计算玩家待译量。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/pong-rewards-batch086/workspace
python build/batch-086-verification/verify_resources.py baseline
python build/batch-086-verification/verify_resources.py modified
python build/batch-086-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
40条新译双盘回填一致，旧8,933条保留，9,203条其余原值未改；独立回滚恢复8,933条，主文件保留8,973条。
基线1272、修改/干净index1278测试各skip1；219依赖锁、164工作区文件重建一致、683份index文件复核及错误hash回滚拒绝分别验证。
README、字幕profile/全部计划/历史候选冻结；GLOSSARY由415项结构化源渲染核对。仅清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前测试包与基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端及干净状态，当前CI按实际结果记录。
