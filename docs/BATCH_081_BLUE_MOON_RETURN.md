# 第八十一批：青月重建与归来的领袖

日期：2026-10-20。新增INT22条，累计8,775条draft；共享candidate410项，另有1项历史字幕来源记录。全部未人工定稿。

## 范围与语境

- CSMBQ10_30五条挑战、CSMBQ10_35十七条重建请求，均为dialogue；15条显式去普通对白硬换行，控制码/键位/数值/前后空白保持。
- 实际源人物드레고沿用德雷戈，不混作鲁坦或阿尔贝多；青月/黑角特雷瓦、阿巴泽特、修恩扎伊特、鲁哈尔特高原均复用旧候选。
- 德雷戈对故乡覆灭的归因、改变态度、只认阿尔戈的态度均是人物发言，不扩成客观历史裁决或全族一致决定。阿尔戈疑问保留，不代写正式接任仪式。
- 同伴正在高原聚集、未来继续招募、组织已有规模，不写成故乡已重建完成；相连场景核读不等于已证运行触发条件或实际播放顺序。
- 상인조합复用旧NPC Ch02_Abazet/02_2267_00的商人公会，新增1项共享candidate，旧409项完整保留；未核官方译名或组织运行绑定。
- 同阶段Quest10_901_0四、10_910_0二十二，Npc11_trewa十四译文/一项held及CharacterName德雷戈已在75批处理，本批保持，不重复计数；旧商人公会NPC文本保持。
- CSMBQ10共97条中78条draft；余父女相见40场景19条，继承10_cerestin_2七字段与母亲姓名随其后核读。另有rue_cerestin七字段待补，不混同Rue_1。
- 邮件124/235、44独立字幕计划315/315已提取cue保持，后者不是全部游戏字幕已完成的证明；全部历史held、重复key occurrence与旧译保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/blue-moon-return-batch081/workspace
python build/batch-081-verification/verify_resources.py baseline
python build/batch-081-verification/verify_resources.py modified
python build/batch-081-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
双盘22条新译一致，旧8,753条保留，9,401条其余原值未改；独立回滚恢复8,753条，主修改产物保留8,775条。
基线1242、修改/干净index1248测试各skip1；209依赖锁、164工作区文件重建一致、663份index文件复核、错误hash回滚拒绝分别验证。
README、字幕profile/计划/历史候选、全部旧held冻结。仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，当前提交CI以实际状态为准。
