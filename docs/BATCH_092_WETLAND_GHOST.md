# 第九十二批：湿地讨伐与马雷的幽灵

日期：2026-10-20。新增INT38条，累计9,319条draft；437项共享candidate冻结，另1项历史字幕来源记录不变，未人工定稿。

## 范围与语境

- 03_352_00完整15条、03_360_0完整20条、Kotamare/Refuge地点名1条与Mare_Pendant名/说明2条同步。28对白、4名称、2任务说明、2系统提示、1目标、1物品说明。
- 18条对白显式去硬换行；10个功能字段保持换行与空段，4个%s、QUEST/Quest大小写、[]和三处数字6保持。非剧情单句提示依现行规则去句末句号。
- 布莱博拉/暗影藏身处复用旧候选，西北方与北方各依源，不统一成一个方向；制造怪物等说法保持委托人的据说语气，不作为独立历史考据结论。
- 任务DES明确死后化为幽灵，player字段明确尸体；不补死者性别、怪物种类、复活或诅咒机制。族长原以为孩子在外过得好，不改为早知死讯。
- 목걸이项链与펜던트吊坠语感分别保留；独立Item明确是遗物，不引入同词素的其他饰品或配方，也不补数值。马雷族不是个人姓名。
- NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、全部旧译/held/重复occurrence冻结。初次工作区在review系统分类修正前生成，保留为证据；当前规范输入是build/batch-092-verification/final-workspace。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-092-verification/final-workspace
python build/batch-092-verification/verify_resources.py baseline
python build/batch-092-verification/verify_resources.py modified
python build/batch-092-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT原始SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
38条回填一致，旧9281条保留，8857条其余原值不改；独立回滚恢复9281条，主文件保留9319条。
基线1308、修改/干净index1314测试各skip1；231输入锁、164文件重建一致、707份index导出复核；错误hash回滚拒绝且目标不变。
只清理经绝对路径及无依赖核实的干净源码测试pyc，原盘/配置/存档/runs/当前包/基线/回滚/研究证据保持。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端一致和工作区干净，当前CI只记录实际状态。
