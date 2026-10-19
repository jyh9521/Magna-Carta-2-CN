# 第七十六批：复仇变体、父亲日记与花之传说

日期：2026-10-20。新增INT74条，累计8,552条draft；共享candidate402项，另保留1项历史字幕来源记录。
独立字幕44计划315/315已提取cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBQ06_020/020_01/020_02复仇阶段变体22、040父亲日记15待译、050初遇求婚22，CSMBQ07_10花之传说再遇13与CharacterName两字段同步。
- 分类72 dialogue、2 name。020三版分别对应身份未知、艾尔加身份/营救公主争论、承认过错与赎罪承诺，独立按源ID/语境保留，不拼成一次连续争吵。重复威胁依旧保留三个ID及感叹号/句号差异，不按词面去重。
- 040原00/01两条拜泽恩/银白的拜泽恩旧译、CharacterName的Vizen/bizen及Diary/small_box四物品字段保持；Quest06_601-604作旧上下文，未知603_0继续held。只新增02..16，绝不把整节17条重复记成新增。
- 日记中停留、计划前往贝尔福特与复仇保留推测/转述；可能知道下落仍为可能，不改成父亲现在就在贝尔福特或确认结局。
- 初遇求婚、一见钟情、露的拒绝与同伴猜测保持各自立场。07_10花名功效仍为传说/人物相信与质疑；不替露确认心意，也不为了后句揣测而删去前面的明确拒绝。
- 新增3项candidate：雷恩波尔特惨案、玛拉基亚、塞娅之泪；旧399项逐项保持。花仅见对白解释，未见对应已提取Item定义，不据此新造物品或断言功能。两处玛拉基亚姓名按独立稳定ID回填，不合并源记录。
- 51条普通剧情显式去硬换行；控制码/数字/按键/前后空白保持。省略号按中文标点真实改值，不照抄计draft。
- 完整CSMBQ06为117/117有draft；不是全章/全文或游戏内验收完成。CSMBQ07_10为13/13，后续20/30/40/45/48共27条按重逢、父亲线索与旧宅/机关/回顾接续；已有07任务150字段不重复计数。
- 玛拉基亚后期保护/营救与武器支线、Q11_0邮件/rue_0任务按后续09/10阶段另接，不把后期来信提前拼入初遇或传说场景。未新增邮件或独立字幕。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/reinpolt-batch076/workspace
python build/batch-076-verification/verify_resources.py baseline
python build/batch-076-verification/verify_resources.py modified
python build/batch-076-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
74条双盘回填一致，旧8,478条保留，9,624条其余原值未改；隔离回滚恢复8,478条，主产物保留8,552条。
基线1212、修改/干净index1218测试各skip1；199项依赖锁、164工作区文件重建一致、643份index文件复核及错误hash回滚拒绝分别验证。
历史held含11_trewa/911_2、重复occurrence、44字幕计划/profile/315cue、历史字幕来源及README冻结；GLOSSARY由402项结构化源渲染核对。
第75批CI run39317488655四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包、基线/回滚与研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为整个项目结束。
