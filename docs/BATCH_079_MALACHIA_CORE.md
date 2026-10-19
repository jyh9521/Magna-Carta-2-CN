# 第七十九批：保护、营救与雷力核心

日期：2026-10-20。新增INT59条，累计8,707条draft；共享candidate407项，另保留1项历史字幕来源记录。
独立字幕44计划315/315已提取cue保持，邮件新增2字段至124/235，均未人工定稿。

## 范围与语境

- CSMBQ09_10/15保护与担忧21、CSMBQ10_50再会4/55雷力10、rue_0三字段/Rue_1十四字段、Q11_0邮件2及Item5同步。
- 分类48 dialogue、4 name、2 quest_description、1 mail_subject、1 mail_body、3 item_description。保护/离开、以后打听、后期邮件/营救、重逢/核心线索、武器雷力分别核读，不按09/10/Q11编号认定即时连续触发。
- 违令受罚的担忧与邮件“似乎转移”保持推测/传闻；命运与关心仍为人物说法，不替露确认爱情。邮件首句采用“之前提到的”，不凭省略主语倒置谁先告知谁。
- Rue_1的核心成分、雷力过强及露能否控制按源保留；698_2以逗号承接下一条，不补实验步骤或结论。敌人903四字段是角色叫嚣；1055成功收纳与能否运用未知并存，“最强”为人物描述，不当实测排序。
- 雷帝Item三字段保留雷力/终极短刀与两处攻击+270；其与任务奖励的运行绑定未验。研究所钥匙两个字段可独立翻译，但不凭泛称认定就是Rue_1赠物。
- Valuables/key_laboratory及_D各两occurrence：只新增1钥匙名/描述，保留2旧通行卡两值/ID/hash；不要按key覆盖。名称末尾一空格保持。源区别/后续验证约定见PITFALLS新增条目。
- 新增4项candidate：雷之核心、雷帝、研究所钥匙、短刀。雷帝按뇌제及雷力语境暂拟汉字，原汉字/官方名待核；核心仅有实际Quest名/对白，不新造独立Item。旧403项保持，未人工定稿。
- 邮件正文保留5处literal换行、空段落和末尾一空格；两处武器D/S保留功能换行，全部11个非对白字段保留布局。28条普通对白显式去硬换行，数字/控制码/键位/方括号/前后空白保持。
- Ch09六个PartyTalk纯省略号保持ID/hash/值held；是否沉默/占位或功能用途未核，不计draft或断言运行不用。CSMBQ09_10/03的已知场景沉默按剧情标点表达，不将两种语境混为功能证据。
- CSMBQ09为21/21、CSMBQ10为14/97，后者余83分别为复仇42、部族22、父女相见19；不是全章/全文完成。rue_cerestin七字段另属已译微笑/连携支线，后续单独补，不与Rue_1混并。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/malachia-core-batch079/current-workspace
python build/batch-079-verification/verify_resources.py baseline
python build/batch-079-verification/verify_resources.py modified
python build/batch-079-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
59条双盘回填一致，旧8,648条保留，9,469条其余原值未改；隔离回滚恢复8,648条，主产物保留8,707条。
基线1230、修改/干净index1236测试各skip1；205项依赖锁、164工作区文件重建一致、655份index文件复核及错误hash回滚拒绝分别验证。
历史held含默认值/纯省略号与当前6处、重复occurrence、44字幕计划/profile/315cue、历史字幕来源及README冻结；GLOSSARY由407项结构化源渲染核对。
第78批CI run39321692855四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包、初次候选工作区、基线/回滚与研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为项目结束。
