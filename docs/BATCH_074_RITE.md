# 第七十四批：成人礼邀请与庆典回顾

日期：2026-10-20。新增INT29条，累计8,400条draft；共享candidate391项及1项历史字幕来源记录。
字幕44计划315/315已提取cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBQ06_010邀请15、060庆典祝贺/次日12，与Item/Valuables仪式信物名/描述2同步。
- 24 dialogue、3 narrative、1 name、1 item_description。060末三条为庆典回顾、次日战斗的推测和第二天过渡；不把物理section顺序当运行触发证明，不跳过中间已译仪式任务。
- 核读旧Quest06_301/302/304/307仪式、06_kotamare/feast NPC、ComposeChapter06_54/55/57及Q06_qube_1邮件；这些已有draft仅作上下文，不重复翻译或计数。第六章任务314/316与NPC287/312保持，其余格式未知/删除标记仍保留原值。
- 成人礼沿用候选。060_06明确只活了12年，保留数字12及完整语义，不因仪式成年而篡改年龄；两处结婚发言只保留为角色提议/愿望，不写成已经结婚或新增设定。
- 实际Item名仪式信物与描述对应盖有族长印章的成人礼所需信物；新增共享候选“仪式信物”，保留旧390项，不凭任务“成年信物”的称呼断言同一运行物品。暂译而非官方名、人工定稿或实机身份确认。
- 18条普通剧情显式去硬换行；控制码/数字/键位顺序、前后空白保持。省略号转为中文标点而非照抄计draft；Item单句不加末句号。
- CSMBQ06仅27/115有draft，剩余88按复仇阶段变体、部族冲突、父亲日志与求婚场景分别接续；020/020_01/020_02不拼成一个连续事件。下一批先核关联姓名/物品/既有任务。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/rite-batch074/workspace
python build/batch-074-verification/verify_resources.py baseline
python build/batch-074-verification/verify_resources.py modified
python build/batch-074-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
29条双盘回填一致，旧8,371条保留，9,776条其余原值未改；隔离回滚恢复8,371条，主产物保留8,400条。
基线1200、修改/干净index1206测试各skip1；195项依赖锁、164工作区文件重建一致、635份index文件复核及错误hash回滚拒绝分别验证。
历史held、重复occurrence、44字幕计划/profile/315cue、历史字幕来源、README冻结；旧390术语逐项保持，GLOSSARY由391项结构化源渲染并检查。
第73批CI run39314535476四组实际completed/success；当前提交的排队/运行状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包、基线/回滚及研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口。离线成功不代替游戏验收，不以本次提交作为整个项目结束。
