# 第八十四批：阿巴泽特攻城准备期NPC

日期：2026-10-20。新增INT38条，累计8,866条draft；共享candidate411项及1项历史字幕来源记录保持。未人工定稿。

## 范围与语境

- Ch04_Abazet_1完整未译组38条均dialogue，21条显式去普通对白硬换行；机器控制码、数字、按键、首尾空白保持。
- 语境为峡谷战后、杜南丘陵攻城准备、黑刃要塞新守将与北部军残党；按组内发言核读，不以目录号证明真实运行触发或事件播放顺序。
- 反哨兵部队、希昂·雷格拉尔、泽格隆、狼人/拉提族、杜南丘陵/老狐峡谷/黑刃要塞、阿维斯族与哨兵沿用旧候选。terms411和GLOSSARY字节冻结，不另造新守将姓名或绑定某位已知女战士。
- 盲从、制造技术/地点、猫猫族群袭击等保留疑问、听闻、推测；不拿后续研究所情报替早期NPC解答，也不把可靠情报的自我宣称改成旁白事实。对泽格隆的悼念保留未尽句，不补凶手或死因。
- 210_2/210_3虽语义相近，源ID/key与硬换行不同，各自回填，不合并；短版不补长版某处的修饰。
- 2217_0..3自称王子、寻人类新娘、沉默、反问是否相信完整处理；2217_2源纯省略按这组已知发言上下文暂译中文省略，不视作所有纯省略均已知用途。历史PartyTalk纯省略held仍原样，未改变分类或计数。
- 现有INT按04_任务及Q04/E04/B04邮件前缀有界审计未见未译项；旧阿维斯族两名字段与泽格隆名保持。不把通用AvisMerchant角色名自行绑定王子发言；相关名字复用，不重复计数。
- 下一组Ch04_Abazet_2五十二及04_oldfox十五待接续，另有ruhalt/698_0一条实际未译对白待核上下文，不当held。邮件128/235、44字幕315/315已提取cue与全部旧译/held/重复occurrence保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/abazet-siege-batch084/workspace
python build/batch-084-verification/verify_resources.py baseline
python build/batch-084-verification/verify_resources.py modified
python build/batch-084-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
双盘38条新译回填一致，旧8,828条保留，9,310条其余原值未改；独立回滚恢复8,828条，主文件保留8,866条。
基线1260、修改/干净index1266测试各skip1；215依赖锁、164工作区文件重建一致、675份index文件复核及错误hash回滚拒绝分别验证。
README、术语/词表、字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前测试包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端与干净状态，当前CI记录实际结果。
