# 第八十九批：岛上防备、工具与坚硬的角

日期：2026-10-20。新增INT72条，累计9,126条draft；共享candidate427项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- Ch01_104_0采集21、105_0工具20、120_0狩猎19、Item10及UI information2同步；41 dialogue、10 name、9 system_message、3 quest_description、4 quest_objective、5 item_description。
- 31条普通对白显式去硬换行，31个功能字段保留布局；QUEST、17个%s、[]、4株/5个等数字及前后空白保持。四个源尾1空格字段为采集完成问句、送工具DES、钥匙名、陷阱材料名。
- 三个完整任务分别核读，各section来源保留，不以写入排序证明运行触发。向哈曼报告的源目标不因前批果实悲恸而改写，也不强行统一成同一任务时间线。
- 火焰草/工具/比尔特的钥匙/陷阱材料/坚硬的角/比尔特的箱子六名与无空格피어스웜源变体新增7项candidate，旧420项保持。穿刺蠕虫、海因格尔、比尔特、梅莉莎、哈曼、青灵森林、风息岛、燃烧瓶沿用候选，源变体不回写或合并ID。
- 源tool_box只是工具，不按英文key扩成工具箱；箱子另有UI实际源名。坚硬的角也出现在守护者护甲描述，但不据共同词组套译无关护甲、合并物种或推断运行奖励绑定。
- 采集太急/太慢与适当力度按对白保持；旧Tutorial_Scene_13三字段已译保持，不重复计数，不把其中3秒或按键擅自搬进本任务。
- 村长家前/家旁的源位置差异分别保留，不静默统一。工具与陷阱材料取得消息/目标都保留，不简化成只送工具。
- 等级差的命中/伤害/暴击提醒保持，不补等级阈值/公式。120_0 DES的普通韩文笔误회득按句义译获得，不改源字节/hash，也不当未知控制码。
- NPC1443/1473及余30标记未知、邮件128/235、44字幕315/315已提取cue、README和全部旧译/held/重复occurrence保持；不把其余原值直接表示玩家待译量。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/island-preparation-batch089/workspace
python build/batch-089-verification/verify_resources.py baseline
python build/batch-089-verification/verify_resources.py modified
python build/batch-089-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
72条新译双盘回填一致，旧9,054条保留，9,050条其余原值未改；独立回滚恢复9,054条，主文件保留9,126条。
基线1290、修改/干净index1296测试各skip1；225依赖锁、164工作区文件重建一致、695份index文件复核及错误hash回滚拒绝分别验证。
GLOSSARY由427项结构化源渲染核对，旧420项不变；README、字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和工作区干净状态，当前CI按实际结果记录。
