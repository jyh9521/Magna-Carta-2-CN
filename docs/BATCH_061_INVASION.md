# 第六十一批：梅莉莎的变故与柯塔马雷防卫

日期：2026-10-20。新增INT51条，累计7,504条draft；341项共享candidate及1项历史字幕来源记录。
独立字幕新增16cue至37计划270/315cue；邮件116/235保持，均未人工定稿。

## 范围与顺序

- 先处理盘2独立字幕csm11-50/60各8cue：突发变故、代价与临别，然后北部军到来。不因为是独立sidecar而漏译，不提前将克蕾尔的疑问写成确认。
- 接CSMB11_65十五条、11_70二十一条；入侵阶段10_kotamare_battle九条与Compose11_18-23六条同步。
- 分类42 dialogue、9 narrative；11_65末三条是悲伤与奔赴战场的收束叙述，不按CSMB文件名一律归对白。
- 23条普通对白/念白显式去硬换行。字幕UTF16LE BOM、KRCC、原起止时间、清屏事件、<br>数量、所属cue与次序受锁定验证，字幕不去硬换行。
- 联合军为对方自称，源文有南北军并存；新增兰兹海姆联合军1项candidate，不把每个军人一概认定为加入。
- 前批已完成到访NPC与核心材料链。本批只纳入实际入侵NPC，不提前混入战后慰问、葬礼/墓碑或尚待审计的支线残句。

## 可复现验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/invasion-batch061/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-061-verification/subtitle-catalogs
python build/batch-061-verification/verify_resources.py baseline
python build/batch-061-verification/verify_resources.py modified
python build/batch-061-verification/verify_resources.py rollback
python build/batch-061-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增51条两盘回填一致，旧7,453条保留，10,672条仍为源值；隔离回滚恢复7,453条，主产物保留7,504条。
双盘ISO仅只读hash校验和导出字幕目录，没有生成新ISO或整盘副本。44目录315cue保持，旧254cue逐字段保留，新增16cue，45cue未译；原始字幕空计划重建逐字节一致，独立回滚还原原始副本，修改字幕保持。
干净index源码测试、162项依赖锁、164工作区文件及45字幕目录文件重建一致性、错误hash回滚拒绝分开验证。
旧35字幕计划、profile.sources、历史字幕来源与README逐字节保持；共享旧340项候选结构保持，新项仅追加。
第60批CI run39296845281四组均completed/success，实际jobs保留；当前提交排队/运行中不记为成功。
仅清理核实绝对路径下可再生验证pyc；保留原盘、配置、存档、runs、当前测试包及回滚/研究证据。
未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB11_71的防线说明接11_80/90对峙，再按后续事件核读战后NPC/Compose；11_80本身仍是敌方对峙，不提前当战后慰问。不复译本批16cue及入侵前准备。
