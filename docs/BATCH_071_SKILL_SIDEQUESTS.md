# 第七十一批：连携支线与技能说明

日期：2026-10-20。新增INT82条，累计8,280条draft；新增4项candidate至387项，另保留1项历史字幕来源记录。
独立字幕38计划271/315cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBQ11_10..13营救玛莉丝31条、20..23露的笑容31条，zuto_crocell关联任务10字段，Compose12_38-41学习提示4及Skill两名称/四描述6同步。
- 分类70 dialogue、3 name、1 quest_description、4 system_message、4 skill_description。两组支线按各自源序核读，不擅自补说话者或认定两组实际触发先后。
- 克罗塞尔与朱特合作营救、回村解释；塞蕾丝汀想让露开心、猫猫赠礼与袭击、合作及笑容，均保持人物语气。猫猫口癖沿用“喵”，姓名沿用玛莉丝/露等旧候选。
- 马雷灵药仅是对白中的采药理由，不据此生成实际Item。新星斩的Skill源名노바 슬래시与Compose源名노바슬래시相差内部空格，分别锁定源ID并作候选主词/alias，不修改源拼写。
- 超冰结雷震爆为초빙결뇌진폭的暂定汉字表达，原汉字与词源待核，不作官方定稿。共4项候选新增，旧383项逐条保持。
- 四个学习提示各保留1处literal换行；任务DES/标题原布局保持，共6字段保留功能布局，49条普通对白显式去硬换行。四技能描述保留数值1、非剧情单句不加末句号。
- Renkai_Ougi/Skill_d_37有两个独立occurrence：1风/雷的55批旧译保持；2冰/雷本批新增。按完整ID/hash/occurrence定位，不按key构造字典覆盖。详见PITFALLS新记录。
- CSMBQ11明确前缀62/62、Renkai_Ougi五组10/10字段均有draft，不表示支线触发/技能解锁已验。旧三奥义名与风雷描述不改，未发现新增对应Item或邮件字段。
- Compose11-16仪式提示及37疑名不按相邻编号混入；所有历史held含63三处与68两处保持。第十三章剧情/字幕仍待接续。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/skill-sidequests-batch071/workspace
python build/batch-071-verification/verify_resources.py baseline
python build/batch-071-verification/verify_resources.py modified
python build/batch-071-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
82条两盘回填一致，旧8,198条保留，9,896条仍为源值；隔离回滚恢复8,198条，主产物保留8,280条。
干净index源码测试、183项依赖锁、164工作区文件重建一致与错误hash回滚拒绝分别验证。
历史held、旧译、重复occurrence保持；字幕profile、38计划271cue、历史字幕来源及README逐字节冻结，本批不读取或导出ISO。
第70批CI run39310402621四组实际completed/success；当前提交排队/运行中不记为成功。
仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批接第十三章剧情与独立字幕；仪式提示的上下文审计及37疑名保持可恢复待查记录。
