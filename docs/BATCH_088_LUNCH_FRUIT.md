# 第八十八批：送便当与利安达尔果实

日期：2026-10-20。新增INT38条，累计9,054条draft；共享candidate420项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- Ch01_103_0便当13、Ch01_103_1果实20、人物名2、便当Item2、木剑短说明1同步；26 dialogue、5 name、2 system_message、2 quest_description、1 quest_objective、2 item_description。
- 18条普通对白显式去硬换行，12个功能字段保留布局；QUEST、四个%s、[]、数值、首尾空白保持。便当名尾1空格及木剑短说明功能换行/攻击+5保持，旧木剑名/D不改。
- 完整核读送饭、受伤者急需治疗与迟到后的悲恸，各section来源保留，不将写入顺序当运行触发证明。大叔已经/要是再快一点的未尽句保持，不扩写死亡诊断、失败倒计时或成功救活。
- 莉安娜리안나、哈曼하만实际人物名同步；玛玛蠕虫마마 웜暂译，未见独立CharacterName，不造官方英文/物种关系。任务指称莉安娜的便当리안나의 도시락入候选，但实际Item只叫便当，各按源保持。新增4项candidate至420，旧416项完整保持。
- 青灵森林/利安达尔果实复用旧译库。Ingredient liandal名含尾空格及描述均保持，不重复计数。危险指怪物的角，不改成果实有毒。
- 森林入口/东侧升降梯的yes/in两分支虽语义相同，ID不同，各自回填；朱特finish_02/zuto两条自责也按不同源分行/词序保留，不合并。
- NPC1443/1473与其余30占位/未知标记、全部历史held/重复occurrence保持；邮件128/235、44字幕315/315已提取cue、README冻结。仍有早期任务、其他教程/邮件/物品/技能待接续，不用其余原值直接表示玩家待译量。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/lunch-fruit-batch088/workspace
python build/batch-088-verification/verify_resources.py baseline
python build/batch-088-verification/verify_resources.py modified
python build/batch-088-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
38条新译双盘回填一致，旧9,016条保留，9,122条其余原值未改；独立回滚恢复9,016条，主文件保留9,054条。
基线1284、修改/干净index1290测试各skip1；223依赖锁、164工作区文件重建一致、691份index文件复核及错误hash回滚拒绝分别验证。
GLOSSARY由420项结构化源渲染核对，旧416项不改；README、字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和工作区干净状态，当前CI按实际结果记录。
