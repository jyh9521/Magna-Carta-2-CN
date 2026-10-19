# 第八十七批：海岸清怪与早期教学分支

日期：2026-10-20。新增INT43条，累计9,016条draft；共享candidate416项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- Ch00_104_0完整任务42与ruhalt/698_0告别1同步；35 dialogue、4 system_message、1 name、1 menu_option、1 quest_description、1 quest_objective。
- 21条普通对白显式去硬换行，8个功能字段保留布局；Styles标签、X/Y、QUEST、五个%s、数字、括号与前后空白保持。任务3只数字不改，yesno的X进行教程/Y跳过不交换。
- 复核旧CSMB00_14/15、比尔特/风歌洞窟/拉普斯壳与开场语境；任务是早期海岸清怪与战斗教学分支，不拿后期情报补人物认识。
- 无壳克洛普斯与硬壳拉普斯区分，木剑难以对付硬壳的说法按源表达；克洛普斯클로퍼스新增1项candidate，旧415项保持。源中九处名称语义锚点仅见本任务，未见独立CharacterName，不造英文名或判定物种关系。
- 比尔特、梅莉莎、朱特、守护者、晶柱、风歌洞窟、拉普斯复用旧候选；壳内有时有道具、海边可能藏本体按源说法保留，不保证每个壳掉落道具。
- ruhalt/698_0与同源698键的露相关任务/NPC语境核读，但同key不证明人物绑定。只中性译别担心我/期待再见，不加说话人姓名、性别或任务触发条件，未标held。
- 00_104_yes_02省略处在你以为我是笨蛋/嗯的已知应答语境，暂译中文省略，不推作任何纯省略用途已知。历史PartyTalk静默等held仍原ID/hash保留，无新增held。
- NPC现1443/1473 draft，余30为既有占位/未知斜线/标记，源值保持；不表示全部游戏对白已完成。邮件128/235、44字幕315/315已提取cue、README和旧译/重复occurrence冻结。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/coast-cleanup-batch087/workspace
python build/batch-087-verification/verify_resources.py baseline
python build/batch-087-verification/verify_resources.py modified
python build/batch-087-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
43条新译双盘回填一致，旧8,973条保留，9,160条其余原值未改；独立回滚恢复8,973条，主文件保留9,016条。
基线1278、修改/干净index1284测试各skip1；221依赖锁、164工作区文件重建一致、687份index文件复核及错误hash回滚拒绝分别验证。
初次内存选择表把两条功能字段的字面换行解释为物理行，在写计划前被条数断言拦住；改用原始字符串后完整验证，未写入半成品译文，过程记录保留。
GLOSSARY由416项结构化源渲染核对，旧415项不变；README/字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前测试包与基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和干净状态，当前CI按实际结果记录。
