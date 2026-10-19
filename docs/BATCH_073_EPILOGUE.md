# 第七十三批：尾声正文与三年后的生活

日期：2026-10-20。新增INT51条，累计8,371条draft；390项共享candidate及1项历史字幕来源记录保持。
独立字幕44计划315/315已提取cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBE_10/20/30/40四段17/13/16/5条，补齐仍未译的尾声正文，不因72批独立字幕覆盖而跳过。与已译ep-45/50字幕核对上下文，不重复字幕计划。
- 分类43 dialogue、8 narrative：E10末五条为三年回顾与世界变化，E30末三条为适应新环境与选择的心境收束；其余保留场景发言，不按整文件默认归对白。
- 民众的劳作抱怨、瘟疫传闻、责任指责与反驳分开表达；不将流言升级为叙述者判断。哨兵按源写沉睡，不改为死亡，也不新增复活/重逢解释。
- 重聚、露的玩笑、阿维斯未来机器的可能性/夸口、药草知识流行与交流均按角色语气保留，不增补人物婚姻、科学、医疗或实际性能结论。
- 三处阿拉伯数字3分别对应回顾、长时间改变与过渡时期；数量/控制码/按键顺序保持。33条普通剧情显式去硬换行，无功能布局改动。
- 蕾洁菲尔妲、治愈连环术、卡尔玛、灾祸种、柯塔马雷及旧人名/地名复用候选；共享词库/GLOSSARY逐字节保持，不新增术语或人工定稿。
- 提取NpcTalk、Quest、QubeMail、Compose未见ep/end/13_/e_前缀同阶段字段；这是有界命名审计，不是所有运行显示不存在的证明。
- CSMBE明确前缀51/51有draft，不等于全文或游戏内验收完成。下一批回到未译支线场景与关联任务；剩余原值含编辑器/工具/测试样例，不把所有原值当作已确认必译玩家文本。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/epilogue-batch073/workspace
python build/batch-073-verification/verify_resources.py baseline
python build/batch-073-verification/verify_resources.py modified
python build/batch-073-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
51条两盘回填一致，旧8,320条保留，9,805条仍为源值；隔离回滚恢复8,320条，主产物保留8,371条。
干净index源码测试、193项依赖锁、164工作区文件重建一致与错误hash回滚拒绝分别验证。
历史held、旧译及重复occurrence保持；字幕profile、44计划315cue、历史字幕来源、共享词库、GLOSSARY及README逐字节冻结，本批不读取或导出ISO。
第72批CI run39313454046四组实际completed/success；当前提交排队/运行中不记为成功。
仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批核读未译支线场景与任务的关联，按稳定ID续接；仪式提示/疑名保持待查，不以尾声或一次提交作为整个翻译工作的结束。
