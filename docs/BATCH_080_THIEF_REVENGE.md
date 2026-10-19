# 第八十批：盗贼复仇与家传宝剑

日期：2026-10-20。新增INT46条，累计8,753条draft；共享candidate409项，另保留1项历史字幕来源记录。
独立字幕44计划315/315已提取cue、游戏邮件124/235字段保持，均未人工定稿。

## 范围与语境

- CSMBQ10_10救援3、15对话15、20父母之仇/赠剑24，Item130_sword三字段及CharacterName盗贼1同步；42 dialogue、2 name、2 item_description。
- 以同一追讨父母之仇的角色与前后发言核读相连场景，不把旁边父女灰烬或部族支线拼入，不以目录号证明真实触发顺序。
- 过去暴行、受控制、受害者自责/怀念、朱特想要守护的动机均按人物发言保留，不替角色免责或升为旁白判决。末尾收回杀意不改成全面原谅；未来会理解/但愿如此不改成已经理解。
- 旧盗贼两组11_zuto_0十四、12_zuto_1九共23任务字段，以及zuto_crocell既有连携任务10条均保持；后者不是同一盗贼任务，不混并或重复计数。10_前缀NPC按雷恩波尔特/铁匠关键词未见额外字段，是有界审计，不是全部运行文字不存在的证明。
- CharacterName/thiefboss源值仅为도적，按源译盗贼，不按英文key补头目或造个人名。Item팬텀 블레이드暂译幻影之刃；共2项新增candidate，旧407项保持，未核官方译名或人工定稿。
- 幻影之刃名/描述/短说明各自绑定ID/hash，两处攻击+240与功能换行保留；据说名匠打造/最强修饰按描述表达，不当实测排序。赠剑与具体Item奖励的运行绑定未验，不能以语义接近当已证映射。
- 四个非对白字段保留原布局，23条普通对白显式去硬换行；控制码/数字/按键/前后空白保持。剧情省略号按中文标点实际改值，不照抄计数。
- CSMBQ10当前56/97有draft，余41为部族22和父女相见19；不是全章或全文完成。后者之后再核继承任务10_cerestin_2七字段及母亲姓名，rue_cerestin关联七字段另补，不混入本批。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/thief-revenge-batch080/workspace
python build/batch-080-verification/verify_resources.py baseline
python build/batch-080-verification/verify_resources.py modified
python build/batch-080-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
46条双盘回填一致，旧8,707条保留，9,423条其余原值未改；隔离回滚恢复8,707条，主产物保留8,753条。
基线1236、修改/干净index1242测试各skip1；207项依赖锁、164工作区文件重建一致、659份index文件复核及错误hash回滚拒绝分别验证。
全部历史held、重复occurrence、79批钥匙/通行卡四字段、44字幕计划/profile/315cue、历史字幕来源与README冻结；GLOSSARY由409项结构化源渲染核对。
第79批CI run39323446304四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包、基线/回滚与研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为项目结束。
