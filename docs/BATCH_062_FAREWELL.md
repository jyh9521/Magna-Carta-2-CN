# 第六十二批：冰壁防线、敌方对峙与辞别

日期：2026-10-20。新增INT108条，累计7,612条draft；341项共享candidate及1项历史字幕来源记录保持。
字幕37计划270/315cue、邮件116/235字段保持，均未人工定稿。

## 范围与阶段

- CSMB11_71/80/90/93/100/110六段77条：防线说明、敌方对峙、战毕归村、族长辞别与墓前对话/收束叙事；11_80仍是对峙，不是战后慰问。
- 同阶段10_kotamare_after二十三条；回补Compose11_30声援、31墓铭和37-42材料交付前出战拦截，共8字段。
- 分类95 dialogue、13 narrative。11_110末六条是叙述；“魔女洁菲”的死亡传闻保留为流言，不写成叙述者认可的事实。
- 60条普通对白/叙述显式去硬换行；六条出战拦截各保留1处功能换行，不修改提示触发或任务逻辑。
- NPC309的동생沿用06/10同ID组已用的“妹妹”，不在此改成“弟弟”。轮回说法属于NPC转述，族长的村民责任与其他村民的欢迎态度均保留，不擅自消解立场差异。
- Compose32-36独立场地对白的说话者/触发仍待审计，不凭临近墓铭就臆定亡者复活或鬼魂。24-29机关提示也保留待相应上下文审计。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/farewell-batch062/workspace
python build/batch-062-verification/verify_resources.py baseline
python build/batch-062-verification/verify_resources.py modified
python build/batch-062-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
108条两盘回填一致，旧7,504条保留，10,564条仍为源值；隔离回滚恢复7,504条，主产物保留7,612条。
当前CSMB11明确前缀381/381条有draft，不表示第十一章全部可见文字完成；零散场地字段、支线与其他资源继续按阶段核读。
干净index源码测试、164项依赖锁、164工作区文件重建一致性与错误hash回滚拒绝分开验证，历史held/重复occurrence保持。
字幕profile、37计划270cue、历史字幕来源、共享词库、术语Markdown与README逐字节冻结；本批不重复导出或读取ISO。
第61批CI run39297838032四组均completed/success，实际jobs保留；当前提交排队/运行中不记为成功。
仅清理核实绝对路径下可再生验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
同key跨locale文案差异及源hash已记录docs/PITFALLS.md；JPN仅作旁证，不据其数字改写INT五碑机关，不将待查字段计draft。
下一批从余下Compose机关/独立场地字段及同阶段支线审计接续，再进入第十二章；不把主线前缀完成当作全章完工。
