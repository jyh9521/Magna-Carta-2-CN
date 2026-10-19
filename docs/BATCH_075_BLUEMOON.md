# 第七十五批：青月族群与重建支线

日期：2026-10-20。新增INT78条，累计8,478条draft；共享candidate399项，另保留1项历史字幕来源记录。
字幕44计划315/315已提取cue、邮件122/235保持；均未人工定稿。

## 范围与语境

- CSMBQ06_030/031阿尔贝多质问、交战后托付29条；10_901_0/10_910_0后期重建与圣物任务26、11_trewa聚居地NPC14、Item6和CharacterName3同步。
- 分类59 dialogue、8 name、2 quest_description、3 system_message、3 quest_objective、3 item_description。06_场景、10_任务、11_聚居地分阶段核读，不把物理目录当实际触发顺序或即时连续场景。
- 复用旧Ch04/E04部族史、青月/黑角特雷瓦、鲁坦与鲁哈尔特高原候选。责任指责、背叛者称呼为人物立场；源未明确宣告阿尔贝多死亡，不补死亡、遗言或复活。
- 11_trewa/911_2纯双连字符标记按稳定ID/hash保持held，不译、不照抄计数。916两句等待战争结束再求婚不指定对象或角色身份；保留未明关系。
- Item三圣物按源为剑、镜、宝玉；不按Bluemoon_staff/cap英文key误译法杖/帽子。三名称各保留尾随一空格。奖励只写源“青月武器”，不猜具体装备。
- 新增8项candidate：阿尔贝多、德雷戈、青月圣物、青月之剑、青月之镜、青月宝玉、暗黑特雷瓦头领、青月重建。德雷戈按源드레고，不按Drago键改发音；暗黑头领不凭语义自动并为黑角族名。旧391项逐项保留，未核官方名或实际触发。
- 任务说明/标题/获得提示/目标10字段保留布局，两处功能换行、数字3、QUEST:和三处尾随空格保持；47条普通对白显式去硬换行。Item单句不加末句号。
- 完整catalog确认CSMBQ06实际117字段，040已有2条历史draft；此前115是未译子集，不是全量。74批后29/117、本批后58/117，剩余59。纠正74批文档、当前review与PITFALLS，旧计划/审核锁不变，不把旧两条算新增。
- 下一批按独立阶段接复仇变体22、父亲日志15待译或求婚22；先核040已有2条与关联物品/任务、Malachia姓名/邮件，不重复已有译文或猜阶段。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/bluemoon-batch075/current-workspace
python build/batch-075-verification/verify_resources.py baseline
python build/batch-075-verification/verify_resources.py modified
python build/batch-075-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
78条双盘回填一致，旧8,400条保留，9,698条其余原值未改；隔离回滚恢复8,400条，主产物保留8,478条。
基线1206、修改/干净index1212测试各skip1；197项依赖锁、164工作区文件重建一致、639份index文件复核、错误hash回滚拒绝分别验证。
历史held、重复occurrence、44字幕计划/profile/315cue、历史字幕来源与README冻结；旧391术语保持，GLOSSARY由399项结构化源渲染核对。
第74批CI run39316271851四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包、基线/回滚/失败统计研究证据及初次工作区。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为项目结束。
