# 第168阶段：显式有界归档与杜南、风息岛、王之试炼

## 容量问题和新合同（Verified / offline）

从bc41676接续。旧16份profile共512个scope，512个不同document/section，没有可再无损并拢的重复section。直接给旧suite传17份仍必须失败，不能删旧观察、改MAX_PROFILES或把不相干section改成通配条件。

新增独立通用`tools.audit_context_archive`和`locales/zh-Hans/context-archive.json`，**显式引入分页合同**：1–16页，每页仍经原audit_many的1–16 profile、每profile32 scope/1000成员门禁；全归档最多16000独立成员，沿用原单suite的16×1000总预算，不因页数相乘。跨页任何ID重复即拒绝，即使hash一致也不去重。全局policy只有同一源/计划的一套，按源ID集合重算观察与pending，不累计每页pending。context和功能分隔始终按容器源序输出。

本轮为两页、共17份profile：第一页引用原16份，全部原字节/hash不改；第二页只有新277成员/17scope的profile。这是新归档接口支持跨页更多section，**不是声称全项目仍只有16份**；旧两个审计工具、MAX_PROFILES及旧CLI均原字节不变，旧suite仍拒绝第17份。归档上限16页、每页16份、每份32scope明确，有效成员总量仍受16000限制。

索引锁源SHA、计划canonical SHA与两项false审批状态；页ID唯一，profile路径显式相对索引目录且逐个锁原始字节SHA。拒绝重复路径、绝对/盘符/反斜杠/点段/父级跳转/符号链接和越界路径。CLI复核全部输入快照，仅新建输出，失败不覆盖已有文件。新12个纯合成回归验证单页与旧suite等价、页序不改源序、跨页重叠、内外边界/16000、原hash与目标锁、路径、身份/审批、只读CLI和输入漂移。

```powershell
python -m tools.audit_context_archive --source build/disc1-selected/MC2Game/Localization/Coalesced.int --plan build/cumulative-locale-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json --index locales/zh-Hans/context-archive.json --output build/context-archive-check-new.json
```

输出须新路径；盘二替换source后结果相同。第134阶段旧suite命令继续用于单页历史重放，但不再代表完整归档覆盖。报告kind为read-only-line-context-archive-audit，pages和profiles明确记录来源；单页移除新增page provenance、恢复旧kind后，其全部原字段与旧报告一致，不删source/target/邻序/理由或审批字段来凑相等。

## 完整277项场景、任务、关联名物

workflow最后翻译批次仍116，14082 INT草稿、315独立字幕、1104候选术语不变；新增277项为语境观察，零改译，不创建重叠batch117。

- 最后三个NPC段完整52：06_chinook24、06_dunanfield21、06_oldfox7。前轮预读未计数，本轮统一验证后才计观察；全部计划NPC及5498条计划CSMB至此均已覆盖。
- 十二完整计划任务203：06_603_0/1(14/17)、06_601_0(16)、06_602_0(20)、06_605_0/1(16/15)、06_zepi_0/1/2(19/18/21)、06_699_0(17)、06_670_0(15)、06_203_0(15)。护送/湖怪、寻找助手及日记/袋子、驱赶与讨伐盗贼、水火王之试炼、送信/救投降队长、拉提女王链按完整接受/拒绝/进行/完成/DES/目标审读。
- Default十四字段：dunan_worker、tourist1、dunan_master、dunan_2master、dunan_costumer、thiefboss、giveup_North、madmac、North_commander、North_soldier、Ancientsoul、ghost_king、ghost_king_ice、ghost_king_fire。职业标签不推定地图actor绑定，同译王室之魂的两个物理源不合并。
- Valuables八字段：small_box/_D、Alecs_mail/_D、King_token_water/_D、King_token_fire/_D。原键大小写与尾空格保持；水结界媒介确实叫红莲水晶，不因名字像火就交换水/火物品。

52+203+14+8=277。旧9203完整context/理由/源译hash/邻序/策略和272功能分隔逐项保持，没有旧target或reason取代；新11功能分隔总283。累计9480 INT语境/315cue，4959策略已观察、232待上下文；全部5191运行布局仍待核。源/计划/译文/字体/TOC/字幕/玩家入口无差异，共享INT容器但盘别来源和独立字幕不合并。

## 语境与待查原文

风息岛怀孕/即将当父亲不是已出生，替战争死者而来是比喻，不确认转生；孩子盼梅莉莎到场，不用玩家知情去改儿童视角。旅人问湖怪是否变异不确定生物身份；湖怪任务完成只免除这头怪物的危险，不担保整个区域安全。助手先找自己的日记、后发现拜泽恩日记，是叙事转折，不统一成同一本。铁匠宝剑下落未知，不能凭旧物品“名匠打造”就确定是幻影之刃。

先驱赶休息站盗贼、再攻其窝点，不把前项完成当清空全部盗贼；仇人指控是人物说法，不能当已核定朱特杀人。古王要求各族认可，水之民认可和水之魂试炼不是同一步；第二位王后裔让火之魂困惑，不擅自确认另一人的身份或解释未知力量。亚历克斯独断发信令人疑惑，不能提前写出阴谋实情；麦德麦克任务明确代部下被抓，与2236_2省略句不同，不能跨角色补被俘谓语。旧省略句候选仍未应用，非人工定稿。

两条未计划源分别是06_603_0/603_0与06_zepi_1/order_2，存在单反斜杠直接接韩文的未知格式；保留原始字节/hash，明确keys排除，不擅自正规化为\n或补译。十二任务物理源205/计划203，不能宣称全205已译。新增调查两项后清单42，与旧24held无重叠，双盘均保持原值。

## 验证、回滚、清理、推送与接续

基线1647、修改及干净源码1659测试通过(skipped=1)。四证据位于build/phase-168-verification：MODIFIED_FILE.json、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh。报告隔离回滚恢复9203/4804/387；隔离目录保存原16份逐字节profile并恢复单页索引，实际CLI重算，除明确新增的归档kind/pages外与原suite全字段等价。主工作区保留9480/4959/232及双页归档。错误hash回滚不写，原16份未修改。

统一核两原镜像/八提取源hash，双盘27/29资源独立重放与原始资源回滚，18176源值/14082回填/4094原值，24held/42调查原文，315cue/44资源有效锁及历史三目标取代，164文件工作区复现。本轮原2779依赖全部字节保持，新增归档工具/合成回归/profile/索引四项形成phase168闭包2783；现有phase164包无差异不刷新。

只清理核实为可再生且无入口依赖的隔离缓存；原盘/配置/存档/runs/当前包和基线/回滚/研究保留。无新ISO或整盘副本，无模拟器启动。提交推送并核本地/远端HEAD一致、工作区干净后，按归档索引接续剩余完整第七章及后续任务，不再只装载第一页16份漏算；离线通过不代替游戏验收。
