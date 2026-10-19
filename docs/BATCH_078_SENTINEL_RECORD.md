# 第七十八批：研究记录、墓地线索与队伍引导

日期：2026-10-20。新增INT57条，累计8,648条draft；共享candidate403项，另保留1项历史字幕来源记录。
独立字幕44计划315/315已提取cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBQ08_10/15研究记录与寻找计划26、9_cerestin_1墓地线索任务12，PartyTalk五角色Ch08语言字段19同步；55 dialogue、1 quest_description、1 name。
- 报告由角色读出，不改为全知旁白；巨大化/暴走与怪物型分开，意志/肉体原因仍为无法确定。“处理”保留源措辞，不增添处决细节；人物悲伤、死亡判断与安慰按发言保留。
- 9_cerestin_1提供后续地点线索，不因08/9目录名认定即时触发。101_2/101_6是说话中断，保留省略、不补完整结论；石灰丘陵沿用候选，游戏中石灰块的说法不添加额外材料机制解释。
- PartyTalk城墙、石像、秘密通道、哨兵研究所与末段休息/营救按阶段保留。克罗塞尔使用风而非火，阿尔戈等待露、其他角色救洁菲的措辞不强行统一。
- 本章30个PartyTalk中19有语言并draft，11个纯省略号保持源ID/hash/值held，不转换计数；沉默/占位或功能用途未核，不断言运行不用。
- 修亚伦、克蕾尔、拜泽恩、石灰丘陵、漩涡炸弹复用旧候选。新增1项alias：无空格센티넬연구소仍译哨兵研究所，与有空格源词分别绑定真实ID/hash，不修改源拼写。旧402项逐项保留，未人工定稿。
- 任务说明/标题两字段保持布局，均无功能换行；38条普通对白/队伍引导显式去硬换行，控制码、数字、键位、前后空白保持。
- CSMBQ08完整26/26有draft；不是全章、全文或游戏验收完成。原08_任务91、Chapter08的30条、遗物Item与Q06/Q07旧译保持；10_cerestin_2继承七字段及母亲姓名，待实际墓地场景后另接。
- 下一批核读CSMBQ09保护事件与关联后期玛拉基亚线索/营救任务；Q10墓地、复仇、部族、营救与武器场景分别核上下文，不按邻号混成连续剧情。本批无新增邮件或独立字幕。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/sentinel-record-batch078/workspace
python build/batch-078-verification/verify_resources.py baseline
python build/batch-078-verification/verify_resources.py modified
python build/batch-078-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
57条双盘回填一致，旧8,591条保留，9,528条其余原值未改；隔离回滚恢复8,591条，主产物保留8,648条。
基线1224、修改/干净index1230测试各skip1；203项依赖锁、164工作区文件重建一致、651份index文件复核及错误hash回滚拒绝分别验证。
历史held含Q07默认值/纯省略号、当前11处、重复occurrence、44字幕计划/profile/315cue、历史字幕来源及README冻结；GLOSSARY由403项结构化源渲染核对。
第77批CI run39320246453四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包、基线/回滚与研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为项目结束。
