# 第六十六批：伊格顿送行与登上拉·斯特拉达

日期：2026-10-20。新增INT45条，累计7,896条draft；352项共享candidate及1项历史字幕来源记录保持。
盘2独立字幕csm12-80新增1cue，累计38计划271/315cue；邮件116/235保持，均未人工定稿。

## 范围与语境

- CSMB12_070设置装置、尾羽笑话及伊格顿留守28条，CSMB12_090到达8条；送行字幕位于两段之间，不改成到达宣言。
- Compose12_25-33随时使用装置、准备/启动与再访9字段同步，44 dialogue、1 menu_option。再返回地面的说法保留“应该”，不升级为已验证的游戏机制。
- 12_29与64批12_08源值完全相同，复用完整译值；四个Styles标记、X/Y次序、空格、literal换行不变。26末尾一空格保持；全部九条Compose功能换行保留，22条普通对白显式去硬换行。
- 伊格顿梦想、队友打趣与平安归来的约定保持原有角色口吻；联合军及携带物只译现有台词，不增补身份或细节。伊格顿、传送装置、拉·斯特拉达等沿用共享候选，不新造定稿术语。
- 提取NPC表无12_/Ch12_前缀可新增，旧辞别NPC不重复计数；不据此声称没有其他运行显示。CSMB12主线177/305有draft，未完成全章。
- 12_091与Compose34首试炼、其余仪式/结果/试炼/技能说明待下一阶段逐条核读，不按数字相邻混入。历史held含63批三处疑词/残句保持原ID/hash/值。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/ascent-batch066/workspace
python build/batch-066-verification/verify_resources.py baseline
python build/batch-066-verification/verify_resources.py modified
python build/batch-066-verification/verify_resources.py rollback
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-066-verification/subtitle-catalogs
python build/batch-066-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
45条两盘回填一致，旧7,851条保留，10,280条仍为源值；隔离回滚恢复7,851条，主产物保留7,896条。
源锁定导出在修改前、修改后和干净index分别执行；只读完整ISO身份校验，不复制ISO。
csm12-80保留BOM、44406–48664、KRCC、清屏事件及段落框架；空计划原字节往返、隔离恢复与旧270cue保持分开验证。
164工作区文件与45字幕导出文件重建一致；173项依赖锁及597份干净index源码逐份核对。错误hash回滚拒绝且不改输入。
共享词库、GLOSSARY、README与37份旧字幕计划保持；第65批CI run39303469068四组实际completed/success，当前排队/运行中不记为成功。
仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB12_091明晰类试炼说明及Compose34关联字段接续，先核查候选术语和元素KAN/开关/岛屿路径语义，保持所有数值与功能布局。
