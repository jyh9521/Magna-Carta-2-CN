# 第134阶段：有界多cohort与撤退入队255项审读

2026-10-21，从9fdc6e5干净状态及workflow最后翻译116接续。新增上下文观察255项既有草稿：219 INT、36独立字幕；不是新增255条翻译。14,082 INT/315cue仍draft，1104术语仍candidate。

## 有界汇总合同（Verified / offline）

新增独立通用工具`tools.audit_line_context_suite`，不改旧`audit_line_context.audit`或旧CLI。每个profile仍须通过原32 scopes/1000成员、源/计划canonical SHA、逐项source/translation SHA与源顺序、功能TOKEN和按钮/数字门禁。一个suite显式接收1–16个profile；不接受空集合或非对象。

跨profile任一ID重复立即报错，即便摘要相同也不静默去重。汇总context和功能分隔按源容器顺序输出；输入profile顺序仅影响provenance列表。策略仍从同一源/计划导出的唯一policy集合重算，不相加全局pending。报告kind为`read-only-line-context-suite-audit`，profiles记录各profile canonical SHA、scope数与成员数。零改译、零人工定稿、零运行批准保持。

原opening-layout.json保持逐字节不变：476成员/32 scopes。新island-retreat-recruitment.json独立219成员/15 scopes。累计695 INT、306策略已观察、4885上下文待审；全部5191运行布局仍待核。原五项功能分隔对照保留，新14项对照按源序汇总共19，不因报告顺序变化改写旧profile。

复现命令（输出须新建；同一命令把source换成disc2-selected亦通过）：

```powershell
$plan = 'build/cumulative-locale-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json'
python -m tools.audit_line_context_suite --source build/disc1-selected/MC2Game/Localization/Coalesced.int --plan $plan --profile locales/zh-Hans/context-reviews/opening-layout.json --profile locales/zh-Hans/context-reviews/island-retreat-recruitment.json --output build/context-suite-new.json
```

## 完整场景、任务目标及关联范围

- 八个完整场景170项：CSMB01_31/47/48、CSMB02_05/11/20/22/23，覆盖防壁救护/陷阱/燃烧瓶、撤退、回收守护者与救岛争执、复仇与入队、首次狼人任务。
- Chapter01全部28项已有计划字段，涵盖完整休息对话与X/Y选项、救护和陷阱任务目标/进度、炮击与撤退提示。原Chapter01_19仅省略号、未列入翻译计划，保持原值并显式排除；不谎称原section全29项均为草稿。Chapter02_39–42完整四视角狼人任务边界提示另列4项。
- 01_112 NPC节点两阶段4+2项完整覆盖。四个克罗塞尔别名/亚历克斯/露关联名称、青灵森林名称、绷带/燃烧瓶/爆炸陷阱三组完整名称及说明6项。合计219；旧476项不重新计数。
- 独立盘一字幕csm01-45/01-50/02-10/02-21分别8/6/13/9cue，共36。各自原source/plan hash、BOM、时序、class、clear及br独立逆验证，不合并双盘或猜配音者；累计85cue跨10个来源。

## 语境处置：保留draft

- RT与方向键上或下选道具，X启用/选取，左摇杆移瞄准圈后A确认：不把分步操作改成同时按所有键；陷阱放在标记处、燃烧瓶范围伤害和周边物体增伤按各自上下文保留。
- 任务源中治疗计数包含4/3、5/3，保留原数值，不凭目标3擅自截断；爆炸陷阱不同于后续麻痹陷阱。Chapter01的功能分隔与X/Y选项保留。
- “应该在东北海岸”“大概没料到”“恐怕已被占领”“似乎有战利品权限”保留推断语气；不能把角色推测写成全知事实。青灵森林与风息岛海岸不强行合并地名。
- 撤退争执、梅莉莎牺牲、阿尔戈为救人制止失控、朱特讽刺道谢与幸存愧疚连贯；哨兵、守护者与反哨兵部队区别保持。
- 加入南部军与要求加入最前线反哨兵部队不是同一提案；先拒绝、考虑后坚持、最终附带服从命令/除名条件，不机械统一态度。克罗塞尔的粗话与朱特自省保留不同视角。
- 露在北方获取情报的说法不推断成已确认成果；当前只审初次狼人出击提示，不提前纳入后续老狐峡谷攻略或胡安任务链。

源/译对照未发现本轮必须改译的冲突。共享候选术语已核对，未升级review_status；未改生产计划、译文或字体/TOC/玩家资源。

## 验证、回滚与接续

新增10个源无关测试覆盖union、顺序、重叠拒绝、single-profile兼容、16总数、32 scopes/1000成员原门禁、身份/草稿漂移、批准状态、CLI只读失败与输入快照。基线1612、修改/索引导出干净源码1622，均OK(skipped=1)。旧476实际拆分为两份隔离profile，经汇总与旧单profile语义比较，不把拆分当新增观察。

双盘汇总逐字节相同；旧476锁/顺序/策略投影保持。两原ISO/八源hash、双盘14,082完整回填/旧译/未改值、七字体/56 raw回滚、164文件干净工作区复现及24held再次检查。当前204入口依赖不改；TAB literal coverage仍false，离线验证不代表运行验收。

四件证据在build/phase-134-verification：MODIFIED_FILE.json、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh。独立报告副本hash保护回滚恢复原476/210/4981，主汇总保持695/306/4885；不回退玩家资源或译文。精确命令/输入/输出/exit见VERIFICATION.txt。

仅清理核实可再生成的隔离源码pyc；原盘、配置、存档、runs、当前包和必要依赖/基线/回滚/研究证据保留。提交推送核对HEAD/远端和干净状态后，从CSMB02_24后续完整场景及关联任务接续；先按源序预检，不重复695项。没有新ISO、整盘副本、模拟器或生产刷新。
