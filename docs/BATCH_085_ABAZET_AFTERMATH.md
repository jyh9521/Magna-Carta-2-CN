# 第八十五批：阿巴泽特战后反应与峡谷残党

日期：2026-10-20。新增INT67条，累计8,933条draft；共享candidate411项及1项历史字幕来源记录保持。未人工定稿。

## 范围与语境

- Ch04_Abazet_2五十二条、04_oldfox十五条完整组，均dialogue；45条显式去普通对白硬换行，数字/括号/控制码/按键/首尾空白保持。
- 城内组描述杜南攻占后反应，峡谷组描述泽格隆率残党抵抗；各section来源保留，不以目录相邻或写入顺序拼成真实事件播放顺序。
- 反哨兵部队、杜南丘陵/平原、鲁哈尔特盆地/王城贝尔福特、雷恩波尔特/黑刃要塞、拉诺阿拉湖、斯特拉斯/阿塞莉娜/风息岛、泽格隆/希昂·雷格拉尔均复用旧候选。terms411与GLOSSARY字节冻结，括号内短湖名译为[拉诺阿拉]湖，与旧完整名一致。
- 修恩扎伊特现身传闻、假设抓住则战争结束、敌将能力评价、哨兵失效判断、风息岛撤兵及兵力不足推测均按NPC发言保留，不当已核战略结论或客观旁白。
- 雷恩波尔特被清洗的动机保留人物判断，不据此改80批盗贼旧回忆，不补铁匠个人名或运行身份绑定。宫殿1000年数字不改千字或绝对年代，恋人称谓不改配偶。
- 泽格隆仿佛希昂活着回来的比喻保持，不写成希昂真的复活/两人同一。疲倦、饥饿、负伤、玩笑、家属祈愿各自保留，未尽短句不擅自说完。
- 同阶段04_任务及Q04/E04/B04邮件有界审计未见未译项，旧相关名字保持；ruhalt/698_0尚待人物上下文核读，未并入本批。邮件128/235、44字幕315/315已提取cue、所有历史held与重复occurrence保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/abazet-aftermath-batch085/workspace
python build/batch-085-verification/verify_resources.py baseline
python build/batch-085-verification/verify_resources.py modified
python build/batch-085-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
67条新译双盘回填一致，旧8,866条保留，9,243条其余原值未改；独立回滚恢复8,866条，主文件保留8,933条。
基线1266、修改/干净index1272测试各skip1；217依赖锁、164工作区文件重建一致、679份index文件复核及错误hash回滚拒绝分别验证。
本地验证脚本模板曾误改无关章统计381为671，在生成修改产物前触发断言；只修正该验证统计后完整重跑三模式，过程记录保留，未改翻译数据。
README、术语/词表、字幕profile/全部计划/历史候选冻结；只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前测试包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端与工作区干净状态，当前CI按实际结果记录。
