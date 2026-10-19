# 第七十二批：最终对峙与尾声字幕

日期：2026-10-20。新增INT40条，累计8,320条draft；新增3项candidate至390项，另保留1项历史字幕来源记录。
独立字幕新增六份44cue，累计44计划、315/315已提取cue均有draft；邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMB13_20/35/45三段17/9/14条，均为角色对白，25条显式去普通硬换行；独立csm13-10/30/40/50与csmep-45/50分别4/5/4/24/5/2cue同步。
- 13-10字幕先提出身份疑问与自述，再接13_20；13-30后接35、13-40后接45，之后为13-50与尾声。未把后期揭示塞入旧章节，也不额外补说话者。
- 复制行为/复制体、战争责任、自称创造者、乐园代价、KAN循环与哨兵命运均按角色立场保留；疑问、推测、威胁和反驳不转成译者裁定或技术事实。
- 尾声的愿望、承诺和欢迎仍是原有发言，不补生死、身份或重逢机制的解释。315/315仅指当前已提取的独立字幕，不等于全部游戏文本或游戏内验收完成。
- 阿维斯贝尔克战争独立建候选，不自动与旧阿维斯战争归并；复制、KAN循环共新增3项候选，旧387项保持。卡尔玛、玛格纳卡尔塔、二号艾尔加、斯特拉斯及旧人名/概念复用。
- 六份字幕保留盘2来源、UTF16LE BOM、起止时间、KRCC、清屏事件、框架与每cue的br数量；INT不新增数字、占位符、按键或控制码。
- CSMB13明确前缀40/40有draft；Compose12_11-16仪式提示仍待上下文核读，37疑名与130_26空源等全部历史held保持。其他未译NPC、支线、邮件、物品、教程及UI仍须持续清点。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/final-confrontation-batch072/workspace
python build/batch-072-verification/verify_resources.py baseline
python build/batch-072-verification/verify_resources.py modified
python build/batch-072-verification/verify_resources.py rollback
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-072-verification/subtitle-catalogs
python build/batch-072-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
40条两盘回填一致，旧8,280条保留，9,856条仍为源值；隔离回滚恢复8,280条，主产物保留8,320条。
源锁定字幕导出在修改前、修改后及干净index分别执行；完整ISO身份只读校验，不复制ISO。
原38计划271cue逐字节保持，六新资源分别通过原成员hash、空计划原字节往返、时间/类/框架/br与隔离回滚；修改后的字幕副本保持译文。
干净index源码测试、191项依赖锁、164工作区文件与45字幕导出文件重建一致、错误hash回滚拒绝分别验证；README保持。
第71批CI run39311845638四组实际completed/success；当前提交排队/运行中不记为成功。
仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批从未译条目的稳定ID清单继续审计支线与关联文本，不以独立字幕覆盖或本次提交作为全文翻译结束。
