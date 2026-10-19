# 第六十七批：前两道关卡与中间对峙

日期：2026-10-20。新增INT61条，累计7,957条draft；新增11项共享candidate至363项，另保留1项历史字幕来源记录。
独立字幕38计划271/315cue、邮件116/235保持，均未人工定稿。

## 范围与语境

- CSMB12_091/092首试炼及之后对话17条，100/110中间对峙10条，111与112-117第二试炼及各阶段对话31条；Compose12_34-36三字段教程同步。58 dialogue、3 tutorial。
- 译文组织按场景编号与内容接续，100/110未因物理目录排在117之后而遗漏；不额外为未署名发言补人物名，实际脚本触发和事件先后仍需运行核验。
- 明智之试炼的三个区域、同属性两个KAN、开关颜色/顺序、重复触发和中央启动开关重来分开表达；“我和朱特”无法产生属性KAN是角色自述，不改成所有KAN均不可用。
- 祭品之试炼的王族血脉、守护对象、10次爆炸与剩余时间失败条件逐字段保持；教程仍按源词写能量球/防护罩，不机械归并成对白专名试炼之球/庇护之光。
- 两个试炼名、六个区域名、启动开关、试炼之球、庇护之光共11项候选有真实源ID锚点。진용暂译真勇，仅为上下文候选，汉字与词源待核；不把勇气/勇猛/真勇合并。既有352项逐条保持。
- 34条普通对白显式去硬换行，三教程保留3/2/2处literal换行、方括号与星号序列。阿拉伯数字逐字段同序保持，韩文数字词不擅改成新增阿拉伯数字。
- CSMB12明确前缀235/305有draft；不是全章所有可见文字完成。提取NPC表仍无12_/Ch12_前缀，不重复既有辞别NPC；其他显示仍待审计。
- Compose11-20仪式/王之证明进度、37王之试炼及38-42技能/结果待对应场景核读，不仅按数字相邻混入；历史held含63批三处原ID/hash/值保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/gate-trials-batch067/workspace
python build/batch-067-verification/verify_resources.py baseline
python build/batch-067-verification/verify_resources.py modified
python build/batch-067-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
61条两盘回填一致，旧7,896条保留，10,219条仍为源值；隔离回滚恢复7,896条，主产物保留7,957条。
干净index源码测试、175项依赖锁、164工作区文件重建一致与错误hash回滚拒绝分别验证。
字幕profile、38计划271cue、历史字幕来源与README逐字节保持；本批不读取或导出ISO。
第66批CI run39304953559四组实际completed/success；当前提交排队/运行中不记为成功。
仅清理核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批接CSMB12_120克蕾尔对峙、后续场景及关联独立字幕；先核读原句与候选，不提前归纳世界真相或消解角色立场。
