## 第125阶段：累计字库七别名路由离线合成（2026-10-20）

复用既有raw route builder，组合三族drawable+U+3000计划，并绑定124候选完整语义。七别名共享包顺序编辑后重核，10项局部资源/TOC逆变换与独立原始控制重放通过。
累计2451码点在七字体均有2450非控制映射、2448非布局ink和透明U+3000；TAB仍报告unverified并保留，未绕过控制门禁。路由文本仍旧262条和4字幕计划，不是14,082条/315cue全部投放。
见[PHASE_125_CUMULATIVE_FONT_ROUTE](docs/PHASE_125_CUMULATIVE_FONT_ROUTE.md)。译文和最后批次116保持；未刷新现有测试目录/TOC，验证清理推送后自动接续累计文本控制与字幕合成方案。

## 第124阶段：显式空白advance离线探针（2026-10-20）

新增glyph.layout=blank-advance，仅显式Zs空格分隔符、正整数metric_width和全零alpha；普通空白/TAB/换行门禁保持，禁止替换已有映射或别名借用。三族U+3000候选advance27/20/32，新增独立透明单元，旧记录/像素不变。
选定三族均有2451累计remap及2448个非布局字形ink；U+0009仍保留原值，不把SmallFont原TAB矩形36个可见像素解释成运行行为。不是七别名路由或完整投放，测试包/TOC未刷新。
见[PHASE_124_EXPLICIT_BLANK_ADVANCE](docs/PHASE_124_EXPLICIT_BLANK_ADVANCE.md)。14,082 draft、最后翻译批次116保持；验证清理推送后自动继续别名/路由与TOC预备。

## 第123阶段：累计可绘制字形离线生成（2026-10-20）

显式glyph_limit上限2048→4096、默认128保持，prepare与writer共用同一上限；几何/布局/原资源保护检查不放宽。三族累计可绘制2389/2388/2389字形已在隔离2048x2048包生成并重解码，旧像素与未选remap保持，最大新alpha误差18。
U+3000仍缺显式布局方案，U+0009原值保持；仅三族选定源，不是七别名全覆盖或完整测试包。无新增译文，最后批次116、14,082 draft及1104 candidate保持。
见[PHASE_123_DRAWABLE_FONT_DEMAND](docs/PHASE_123_DRAWABLE_FONT_DEMAND.md)。验证清理推送核对后继续布局/字形ink与别名路由方案，未刷新资源/TOC、未启动模拟器。

## 第122阶段：显式双轴atlas扩展离线验证（2026-10-20）

新增atlas_width受保护选项，重排Xenos BC3块而不重新压缩旧块；原像素矩形/字形记录保持。三族真实源包各1字技术探针通过，2048x2048几何可分配2389/2388/2389位置。
这不是累计字库完成：glyph_limit2048、U+3000布局门禁/U+0009原值仍保持，旧测试包未刷新。译文14,082 draft及最后批次116不变。
见[PHASE_122_ATLAS_AXIS_GROWTH](docs/PHASE_122_ATLAS_AXIS_GROWTH.md)。验证清理推送核对后继续新增字数量与显式布局方案，不生成ISO/整盘副本、不启动模拟器。

## 第121阶段：源字库新增需求与布局门禁（2026-10-20）

三族原始基线核算需新增可绘制字形2389/2388/2389，均超过当前单计划2048限制；现有单atlas仅增高至2048亦放不下。
新增通用需求分类，保留U+3000为待显式布局映射、U+0009保持原值，不送入普通字形栅格化。旧笼统数量失败变为提前说明布局门禁；无字库/资源输出。
译文14,082 draft、候选1104及最后批次116不变。见[PHASE_121_FONT_DEMAND_GATES](docs/PHASE_121_FONT_DEMAND_GATES.md)。验证清理推送核对后继续受保护的容量/布局方案，不绕过门禁或刷新旧测试包。

## 第120阶段：当前测试包累计字形覆盖门禁（2026-10-20）

确认旧262条测试包资源身份完整，但累计14,082条INT/315字幕尚有字形缺口：五别名缺1616个remap、字幕两别名缺1615个，另U+0009保留待查。
累计需求2451码点并非已有覆盖；既有覆盖审计在累计INT范围返回门禁1，未投放新文本、未刷新资源。译文/候选/最后批次116不变。
见[PHASE_120_COVERAGE_READINESS](docs/PHASE_120_COVERAGE_READINESS.md)。验证清理推送核对后继续补字与控制字面量处理方案的离线预备，不绕过覆盖/像素/回滚流程。

## 第119阶段：同源译文上下文审校（2026-10-20）

两组候选均保留上下文变体：教程应答我知道了/我明白了，任务标题讨伐/目标击败；译文仍14,082 draft，1104 candidate，最后批次116不变。
新增通用只读变体审计与源/译文双hash锁定的上下文说明；不自动统一译文，不升级reviewer或人工定稿。
见[PHASE_119_CONTEXT_VARIANTS](docs/PHASE_119_CONTEXT_VARIANTS.md)。验证清理推送核对后继续现有测试包的只读字形需求/覆盖预审；未刷新字库/TOC/入口。

## 第118阶段：跨源边界核对与补零反证（2026-10-20）

译文仍14,082 draft、1104 candidate，最后翻译批次116不变；本阶段不新增猜测译文。
八源hash核对：两盘INT/JPN的MC2Game宽payload逐字节同源，INI/KOR无该模式；统一补零假设会把390字节变401奇数，不能直接当UTF16修复。
只读审计新增naive_nul_insertion尺寸诊断，见[PHASE_118_BOUNDARY_COMPARISON](docs/PHASE_118_BOUNDARY_COMPARISON.md)。验证清理推送核对后继续既有译文/held关联上下文审校；未刷新字库/TOC/入口。

## 第117阶段：剩余文本审计与宽字符串边界（2026-10-20）

译文仍14,082条draft、1104项candidate，translation-workflow最后批次116不变；本阶段不凑翻译数量。
24项原值分类已源hash锁定，新增通用只读宽字符串字节边界审计；双盘发现同一MC2Game.int的11个候选边界，不自动修复或重解释ID。
见[PHASE_117_REMAINDER_AUDIT](docs/PHASE_117_REMAINDER_AUDIT.md)。验证清理推送核对后继续未知格式/孤立笑声引用研究；未刷新字库/TOC/入口。

## 第一百一十六批剩余通信对白（2026-10-20）

新增256条INT draft，累计14,082；Crocell28、Zephi114、Zephie114完整合批，228空白不计，1104项candidate保持。
双拼写表114对精确源/hash核对仍各自保留；55功能换行、6半角~、2全角～和16尾空格保持。
见[BATCH_116_REMAINING_COMMUNICATION](docs/BATCH_116_REMAINING_COMMUNICATION.md)。验证清理推送核对后转入剩余游戏资源分类/未知格式研究，不为凑数翻译编辑器或占位；未刷新字库/TOC/入口。

## 第一百一十五批朱特通信对白（2026-10-20）

新增152条INT draft，累计13,826；MC2_communi_Juto九个完整动作/状态组，9空白不计，1104项candidate保持。
韩文72种源值独立核读，保留初期敬语/后期熟悉与自信口吻，12尾空格保持；不从com/JPN按key搬译。
见[BATCH_115_JUTO_COMMUNICATION](docs/BATCH_115_JUTO_COMMUNICATION.md)。验证清理提交推送核对后继续剩余通信256非空字段；未刷新字库/TOC/入口。

## 第一百一十四批阿尔戈通信对白（2026-10-20）

新增152条INT draft，累计13,674；MC2_communi_Argo九个动作/状态组152非空字段，另9空白不计译文；1104项candidate不变。
实际韩文独立核读，53种逐字相同源才复用，18处尾空格保持；不与com/JPN按key盲对齐。
见[BATCH_114_ARGO_COMMUNICATION](docs/BATCH_114_ARGO_COMMUNICATION.md)。验证清理推送核对后自动接续朱特通信152非空字段；未刷新字库/TOC/入口。

## 第一百一十三批四角色支援（2026-10-20）

289候选核读新增287条，累计13,522条INT draft；朱特71、克罗塞尔68、塞蕾丝汀88、洁菲60，1104项candidate，旧1096保持。
未知反斜线与未完句两条完整held；同section/key的两个occurrence独立回填，485功能换行及特殊空白保持。
见[BATCH_113_REMAINING_SUPPORT](docs/BATCH_113_REMAINING_SUPPORT.md)。验证清理提交推送核对后接续communi_Argo完整152非空字段；未刷新字库/TOC/入口。

## 第一百一十二批邮件与阿尔戈支援（2026-10-20）

160候选新增158，累计13,235条INT草稿；邮件105字段与阿尔戈支援53合批，1096项candidate。
邮件233/235、Argo支援53/53有draft；Test占位与纯省略号主题保留held。段落空行、全角１、100%/70%及源壁/门差异保持。
见[BATCH_112_MAIL_SUPPORT](docs/BATCH_112_MAIL_SUPPORT.md)。统一验证清理推送核对后继续；未刷新字库/TOC/入口。

## 第一百一十一批后续场景与关联物品（2026-10-20）

271候选新增236条，累计13,077条INT草稿；第四章至结局余下交谈/路线感想及物品说明合批，1084项candidate。
35纯省略号原值held；Compose836/921、Valuables154/154有draft，剩余既有held不猜补。红莲水晶/水祭坛、破戒卷轴/火祭坛按源分开。
见[BATCH_111_LATE_COMMENTS](docs/BATCH_111_LATE_COMMENTS.md)。统一验证清理推送核对后自动接续；未刷新字库/TOC/入口。

## 第一百一十批开篇场景与队员交谈（2026-10-20）

新增227条，累计12,841条INT草稿；开篇至第三章场景/可选交谈220及关联物品7合批，1073项candidate。
29纯省略号保持held；Styles与键位顺序、功能换行/半角括号/4 / 3和5 / 3进度、香水左右混色提示不自动修齐。
见[BATCH_110_OPENING_COMMENTS](docs/BATCH_110_OPENING_COMMENTS.md)。统一验证清理推送核对后继续；未刷新字库/TOC/入口。

## 第一百零九批塞蕾丝汀与露装备（2026-10-20）

162候选审读后新增155条，累计12,614条INT草稿；弓/香器/胸针及手里剑/刀/背包合批，1071项candidate。
六字段防御缺值、606刀简述无需字面变化保持held；功能尾空行/前后空格、短刀与刀源差异及604/605数值不自动修齐。
见[BATCH_109_CELESTIN_RUE_EQUIPMENT](docs/BATCH_109_CELESTIN_RUE_EQUIPMENT.md)。统一验证清理推送核对后继续；未刷新字库/TOC/入口。

## 第一百零八批阿尔戈与克罗塞尔装备（2026-10-20）

第107批清理推送核对后直接接续，194候选新增184，累计12,459条INT草稿；1,018项candidate，旧955保持。
8字段属性缺数值、1空白简述、1无需变化的毒炎球名称保持held；309斧加号后空格、数字与功能布局不自动修齐。
见[BATCH_108_ARGO_CROCELL_EQUIPMENT](docs/BATCH_108_ARGO_CROCELL_EQUIPMENT.md)。统一验证清理推送核对后继续；未刷新字库/TOC/入口。

## 第一百零七批朱特与洁菲装备（2026-10-20）

206候选核读后新增202条，累计12,275条INT草稿；朱特剑/肩甲及洁菲扇/杖/手镯合批，955项candidate。
148/151肩甲说明防御+缺值四字段完整held；功能空行/空格/制表符和装备条件保持，不补未知属性或按key纠正名称。
见[BATCH_107_JUTO_ZEPHIE_EQUIPMENT](docs/BATCH_107_JUTO_ZEPHIE_EQUIPMENT.md)。统一验证清理推送核对后自动接续；未刷新字库/TOC/入口。

## 第一百零六批特殊与复合饰品（2026-10-20）

第105批清理推送核对后直接接续，新增225条，累计12,073条INT草稿；Accessory438/438有draft，885项candidate。
全角ＳＩＤ/－/．、猫语两种波浪线、复活一次损坏条件及复合数值差异保持；名称复用配方基础候选，不按数字key映射。
见[BATCH_106_SPECIAL_ACCESSORIES](docs/BATCH_106_SPECIAL_ACCESSORIES.md)。统一验证清理推送核对后继续；未刷新字库/TOC/入口。

## 第一百零五批基础与状态饰品（2026-10-20）

新增212条，累计11,848条INT草稿；Accessory基础属性/状态饰品完整功能组，852项candidate，旧787保持。
旧式key与常规key能力差异、冻疮/寒冷/冻伤、50%与完全免疫及功能布局分别保留，不自动修齐。
见[BATCH_105_ACCESSORIES](docs/BATCH_105_ACCESSORIES.md)。统一验证清理推送核对后继续；字库/TOC/入口未刷新。

## 第一百零四批材料与配方（2026-10-20）

221候选审读后新增220条，累计11,636条INT草稿；材料28、场景动作34、配方158合批，787项candidate。
配方1458_D未知反斜线保留held；全角ＬＶ/括号/数量/全角．/特殊空白和各字段数值差异保持，不自动修齐。
见[BATCH_104_CRAFTING](docs/BATCH_104_CRAFTING.md)。阶段验证、清理、提交推送核对后继续，未刷新字库/TOC/入口。

## 第一百零三批特殊卡蒙德与恢复物品（2026-10-20）

新增296条，累计11,416条INT草稿；特殊卡蒙德102及Recover194完整功能组合批，708项candidate，旧612保持。
Karmond309/309、Recover207/207现均有draft，非全部物品/全游戏或运行验收；日韩混合源、数值/布局与字段差异保持。
见[BATCH_103_SPECIAL_RECOVER](docs/BATCH_103_SPECIAL_RECOVER.md)。阶段验证、清理、提交推送核对后自动接续，字库/TOC/入口未刷新。

## 第一百零二批卡蒙德能力与状态（2026-10-20）

新增204条，累计11,120条INT草稿；68种卡蒙德名称/简述/全述完整三联组，612项candidate，旧575保持。
LV/数字/140加号/18百分号/83功能换行及状态免疫范围保留；眩晕异名待统一QA，不合并源ID或静默改旧译。
见[BATCH_102_KAMOND_FAMILIES](docs/BATCH_102_KAMOND_FAMILIES.md)。阶段完成后统一验证、清理、提交推送核对并继续；未刷新字库/TOC/入口。

## 第一百零一批其余技能与强化加成（2026-10-20）

新增181条，累计10,916条INT草稿；其余三名角色六风格145与卡蒙德强化加成36合批，575项candidate。
数字/加号/百分号/逐行空白、潜隐限制和水冰源差异保持；有限跨源字形参考不覆盖INT动作或旧候选。
见[BATCH_101_REMAINING_SKILLS](docs/BATCH_101_REMAINING_SKILLS.md)。每阶段统一验证、清理、提交推送核对后自动接续，不等待逐次确认。

## 第一百批六风格技能（2026-10-20）

第99批推送核对后接续，新增164条，累计10,735条INT草稿；朱特/阿尔戈/洁菲六风格及通用说明合批，526项candidate。
10条属性增长拼接片段保持held；名称/普通/战斗说明独立ID、数值与功能布局保持，朱特汉字名有限参照JPN实际字段。
见[BATCH_100_STYLE_SKILLS](docs/BATCH_100_STYLE_SKILLS.md)。统一验证/清理/推送，未刷新字库/TOC/入口，离线非游戏验收。

## 第九十九批强化、设置与完整教程（2026-10-20）

新增200条INT草稿，累计10,571条；强化/设置/影片目录/晶柱传送及剩余完整教程合批，475项candidate。
45条日志/助词/升级拼接片段保持held；数值、Styles、逐行空白和功能换行保留。
见[BATCH_099_SYSTEM_TUTORIAL](docs/BATCH_099_SYSTEM_TUTORIAL.md)。统一验证、清理、提交推送；字库/TOC/入口未刷新，离线非游戏验收。

## 第十六批祖先之门与归途（2026-10-19）

新增INT179条，累计2,821条草稿、176项candidate；字幕新增14cue，累计141/315。
CSMB03为687/688条draft，未知转义1条保留；KotaMare四个独立状态118条均有draft。
范围与重建见 [BATCH_016_TOMB](docs/BATCH_016_TOMB.md)；本批不更新字库/TOC/可玩入口。

## 第十五批结盟与身世（2026-10-19）

新增INT122条，累计2,642条草稿、172项candidate；字幕新增14cue，累计127/315。
KotaMare_02 26条已回填，空白pay保留不计已译；csm01四份字幕24cue已有draft。
见 [BATCH_015_ALLIANCE](docs/BATCH_015_ALLIANCE.md)；本批不更新字库/TOC/可玩入口。

## 第十四批湿地防卫与铃铛任务（2026-10-19）

新增INT123条，累计2,520条草稿、168项candidate；字幕新增2cue，累计113/315。
KotaMare_01 40条与重复key分别保留，三份csm03字幕16cue已有draft；其他状态仍待推进。
见 [BATCH_014_DEFENSE](docs/BATCH_014_DEFENSE.md)；本批不更新字库/TOC/可玩入口。

## 第十三批归村与字幕补缺（2026-10-19）

新增INT151条，累计2,397条草稿、165项candidate；字幕新增18cue，累计111/315。
02_oldfox 14条及Ch03_KotaMare初始27条有draft，其他状态仍待后续；胡安送信与物品字段同步推进。
见 [BATCH_013_RETURN](docs/BATCH_013_RETURN.md)；本批不更新字库/TOC/可玩入口。

## 第十二批海底洞窟与城镇尾段（2026-10-19）

新增INT144条，累计2,246条草稿、161项candidate；字幕新增27cue，累计93/315。
Ch02_Abazet已遍历276条：274条draft、2条纯标记保留；csm02四份字幕30cue已有draft。
范围限定与重建见 [BATCH_012_RESCUE](docs/BATCH_012_RESCUE.md)；本批不更新字库/TOC/可玩入口。

## 第十一批柯塔马雷与火之KAN（2026-10-19）

新增INT213条，累计2,102条草稿、154项candidate；字幕新增9cue，累计66/315。
城镇新增18条，两条纯标记不计已译；累计220条draft，索引遍历至221，重复key分别保留。
见 [BATCH_011_KOTAMARE](docs/BATCH_011_KOTAMARE.md)；仅离线回填，字库/TOC/可玩入口未更新。

## 第十批灾祸种与独立字幕（2026-10-19）

新增INT113条，累计1,889条草稿、146项candidate；城镇202/276条。另新增相邻字幕8cue，累计57/315。
一条新未知转义保留待查，不计已译；精华提取条件/换行及Quest:前缀保留。
见 [BATCH_010_CALAMITY](docs/BATCH_010_CALAMITY.md)；仅离线回填，不更新字库/TOC/可玩入口。

## 第九批强化与峡谷剧情（2026-10-19）

新增144条，累计1,776条INT草稿、143项candidate；当前CSMB02可提取剧情585条均有draft，
不包括独立动画字幕等资源，也不代表整章完成。城镇182/276条，营救任务及关联名称同步推进。
详见 [BATCH_009_CANYON](docs/BATCH_009_CANYON.md)；旧1,632条不变，本批不更新字库/TOC/可玩入口。

## 第八批军议与炸弹运送（2026-10-19）

新增131条，累计1,632条INT草稿、134项candidate；剧情接至CSMB02_41，城镇162/276条。
旧1,501条和字幕不变，任务混合key及QUEST:前缀保留；见 [BATCH_008_COUNCIL](docs/BATCH_008_COUNCIL.md)。
本批仅离线文本回填，不更新字库/TOC/可玩入口；验证推送核对后继续下一批。

## 第七批司令部与新命令（2026-10-19）

新增112条，累计1,501条INT草稿、131项candidate；剧情含CSMB02_38_1/2分支，城镇142/276条。
旧译1,389条保持不变，狩猎任务保留功能换行、QUEST%s前缀与占位符。
范围与重建见 [BATCH_007_ORDERS](docs/BATCH_007_ORDERS.md)，不更新字库/TOC/可玩入口；推送核对后直接接续。

## 连续推进与第六批（2026-10-19）

用户要求每批整理、验证、清理、提交推送并核对后直接继续，不等待反复确认；接续点见
[TRANSLATION_QUEUE](docs/TRANSLATION_QUEUE.md)。第六批新增272条，累计1,389条INT草稿、124项candidate。
范围和重建见 [BATCH_006_TEAM](docs/BATCH_006_TEAM.md)，本轮不更新字库/TOC/可玩入口。

## 第五批阿巴泽特到访（2026-10-19）

新增276条，累计1,117条INT草稿，102项candidate术语。包含6场剧情、城镇前84条NPC、
首任务21条及关联名称11条；选择分支和任务段落保留功能性换行。
重建与证据见 [BATCH_005_ABAZET](docs/BATCH_005_ABAZET.md)。本轮不更新字库/TOC/可玩入口。

## 第四批洞窟与海岸防卫（2026-10-19）

新增308条，累计841条INT草稿，75项candidate术语。上述Coalesced开场两章剧情427条均有draft，
对应NPC155/156条，异常反斜线1条继续保留。范围和重建见 [BATCH_004_ISLAND](docs/BATCH_004_ISLAND.md)。
本轮仍为文本离线回填；不生成ISO/整盘副本、不更新字库/TOC/可玩入口。

## 第三批开场剧情（2026-10-19）

新增217条开场/NPC/关联名称，累计533条草稿；59项术语仍为candidate。
构建、场景覆盖与回滚证据见 [BATCH_003_OPENING](docs/BATCH_003_OPENING.md)。
本轮只回填文本，不更新字库/TOC/可玩入口；继续沿用现有测试目录，不生成ISO或完整游戏副本。

## 共享译库与第二批草稿（2026-10-19）

用户决定暂缓双盘合一；不复制两套译文，也不新建整盘测试副本。
可复现工作区、独立字幕提取、统计与验证见 [SHARED_TRANSLATION_WORKFLOW](docs/SHARED_TRANSLATION_WORKFLOW.md)。
`translation-workflow.json` 显式组合既有262条与新增54条，不按文件名自动挑选“最新”。
双盘 Coalesced 输出316条一致草稿，另保留44份动画字幕目录及既有49条字幕译文。
本轮只完成文本资源离线回填，未更新字体/TOC/可玩入口；现有测试目录及其配置、存档、runs不变。

## GitHub Actions 干净环境验证（2026-10-19）

CI须先执行`python tools/series_terms.py fetch`获取series.lock固定的9份参考文件，
再执行`python tools/series_terms.py check --with-references`；不能依赖开发机build缓存，
也不能跳过引用核验。Windows runner的checkout可能在D盘、TEMP在C盘，
相对路径测试必须以自己的fixture为工作目录，不能跨盘调用无start的relpath。
失败原因、跨盘复现与回归说明见[CI_FAILURES](docs/CI_FAILURES.md)。

## 每轮收尾约定

- 2026-10-20用户约定：按完整场景/任务链及关联文本合批，通常每批150–300条；批内做格式检查，合批后统一完整验证、清理、提交和推送，不再每几十条单独收尾。遇到未知格式独立留待查，不为凑数量扩写或降质。

- 普通翻译、字库、排版及资源修复只增量刷新现有测试目录，不逐轮生成 ISO 或完整游戏副本；需要额外整盘副本时先说明理由并征求用户同意。
- 结束前排查：执行与本轮改动相关的验证，检查差异、资源身份、入口依赖及仓库卫生；区分离线验证与真实游戏验收。
- 验证后清理：仅删除已确认可再生成、无入口依赖的临时产物和失败中间文件。先核实绝对路径及引用关系；不按目录名批量删除历史研究。
- 保留原始游戏/ISO、用户配置、存档、运行记录、当前测试包及其 manifest 引用资源，以及必要的基线、回滚和研究证据。
- 完成清理后提交并推送本轮源码/译文/文档，核对 HEAD 与远端及工作区状态；不提交完整游戏资源。
- 最终简报说明修改、验证、清理和推送结果；普通迭代沿用原一键入口。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](docs/TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## 显示修复与独立字幕资源（2026-10-19）

`display-fonts/route.json` 在七个字体别名上实际检查 alpha，而不只检查 remap；
同包生成四个带时间轴字幕 txt、262 条 Coalesced 回填和 TOC。新入口为 dist/MC2-display-repair-disc1。
完整构建命令和旧包失败/新包通过的针对性检查见 docs/DIALOGUE_DISPLAY_REPAIR.md。

## NPC、教程与菜单累计测试包（2026-10-19）

累计 231 条、三类字体七别名的新批次构建与原文对照入口见 [OPENING_BATCH_TEST](docs/OPENING_BATCH_TEST.md)。
新字形指标显式增长，不缩改译文；开发阶段仅离线构建，用户负责游戏内验收。

## 正式文本提取与首批回填（2026-10-19）

双盘原始 Coalesced 提取后，按 locales/zh-Hans/extraction-profile.json 固定 hash
导出 80 份本地目录；命令、标点规则和首批源锁定计划见 docs/TRANSLATION_PIPELINE.md。
首批容器回填不等于已生成可玩的新包，新增字符仍须重建字库和 TOC 并由用户验收。

## 正文空白后的新 Subtitle 测试入口（2026-10-19）

旧剧情样本已收到游戏内空白反馈。新增独立入口 `dist/MC2-story-subtitle-disc1/开始中文测试.cmd`，
原九句不变，补齐此前遗漏的 Subtitle 两别名；默认不装原生行宽补丁。
构建计划 `locales/zh-Hans/story-subtitle/route.json`；原候选保留作对照。
自动覆盖通过不等于画面恢复，详见 docs/STORY_DIALOGUE_SAMPLE.md 顶部更正。

## 真实剧情宽框样本（2026-10-19）

九条真实开场/NPC 对话与可编辑提取→回填流程已建立，详见 [STORY_DIALOGUE_SAMPLE](docs/STORY_DIALOGUE_SAMPLE.md)。
一键入口：`dist/MC2-story-test-disc1/开始中文测试.cmd`；同目录保留同中文无修复及原文对照。
仅离线自动验证，不启动游戏；标题警告保持原文，用户从新游戏进入开场剧情验收。

# 当前可执行流程（2026-10-18）

2026-10-19 原生强制折行宽度修复候选见 [WRAP_WIDTH_FIX](docs/WRAP_WIDTH_FIX.md)：
只补扣行起点，不改样本/字库/框体，不添加手动换行。
新入口 `dist/MC2-layout-fix-disc1/开始中文测试.cmd`；同目录有同中文资源、无修复的 A/B 对照。
新增显式 `--patch-bundle/--patch-manifest-sha256` 只在每次 run/storage/patches 下装配，原配置不变。

2026-10-19 扩展中文长句/标点/自动换行测试见 [TEXT_LAYOUT_PROBE](docs/TEXT_LAYOUT_PROBE.md)：
新入口 `dist/MC2-layout-test-disc1/开始中文测试.cmd`，旧两字入口保留。
源样本、自动收字/空位分配、显式字图扩高、构建/复核命令与用户验收步骤均在该文档。

Python 3.12+，核心工具/默认测试仅标准库；加密XEX还原的显式可选依赖另见下文。本次本地 Python 3.14.2。尚无汉化补丁构建命令。包表/字体只读解析和容器副本回写见 docs/UE3_PACKAGE_RESEARCH.md、docs/FONT_RESEARCH.md、docs/COALESCED_REBUILD.md；它们不等于完整补丁构建。

```powershell
python -m unittest discover -s tests -v
python tools/check_repository.py
python -m compileall -q tools tests
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --hash-image --output build/disc1.json --extract MC2Game/Localization/Coalesced.int --extract MC2Game/Localization/Coalesced.jpn --extract MC2Game/Localization/Coalesced.kor --extract MC2Game/Config/Xenon/Cooked/Coalesced.ini --extract-dir build/disc1-selected
```

Disc 2 同法指定独立输出及目录；首次解出后再次提取应使用新目录，工具拒绝覆盖。`--hash-files` 可为全部成员流式散列。版本、ISO SHA-256、XEX 身份见 docs/RESOURCE_SURVEY.md。

实际文本解析命令与 hash 见 docs/COALESCED_SURVEY.md；提取范围受 hash 和结构校验。现有 Coalesced 副本回写、字体候选和 TOC 大小更新工具见下文及对应研究文档；它们尚非可用汉化补丁，也没有 ISO 重封装。系列来源复现见 docs/SERIES_TERMS.md。

原件保持不变；派生资源在被忽略的 build/。最新约定为游戏测试全部由用户执行，开发阶段不自行启动模拟器或部署候选。未来中文验收应由用户在隔离副本中进行同场景前/后/回退录证。

## 字体使用方离线扫描

Font属性声明使用 `inspect_property_declarations.py --class Font --bind-structs`，可审计Array/Map引用、嵌套类型和local Next边界；不会解码容器值或计算native偏移。源hash、命令与opaque Map边界见 docs/FONT_DECLARATIONS.md。

新增显式 `font-metrics-measurement-path.json`，在13项initialized绑定后检查TextSize caller/helper/metric三窗口与常量。旧initialized计划输出不变，不解释执行指令或推断运行Font；命令与LF hash见 docs/TEXT_MEASUREMENT_PATH.md。

测量调查新增 `inspect_function_metadata.py --class ... --native-only` 与 `inspect_initialized_natives.py`；前三个Class的完整native-only报告生成方式、SHA及initialized row8计划见 docs/INITIALIZED_NATIVE_TABLES.md。它与既有cold row12 inspector分离，默认旧元数据输出不变，不调用目标代码。

新增第六个显式native计划 `references/probes/ui-style-reference-helper.json`，核对判定函数helper及三条class-name/tag参数链。旧五个计划不变；命令/计划LF hash见 docs/STYLE_REFERENCE_HELPER.md。工具仅静态读取，不调用目标函数。

native静态调查新增显式 `references/probes/ui-draw-string-selection-predicate.json`：在既有class-table证明后核验slot124完整判定函数，旧计划/CLI输出不变。命令和LF计划hash见 docs/STYLE_SELECTION_PREDICATE.md；不执行目标代码或游戏。

`inspect_ui_fonts.py --deep --audit-bindings` 现在同时输出匹配标签的 `owner_primary_style_audit`，保留 PrimaryStyle / DefaultStyleTag 及嵌套文本 CDO 的字体观察；原组件链计数不变。新默认字体观察会加入 namespace 指纹审计，可能扩大解码范围；完整证据与非运行边界见 docs/OWNER_PRIMARY_STYLE.md。默认573项合成回归通过。

继承/命名空间审计加 `--deep --audit-bindings`；双盘全 .xxx 类表扫描用 `tools/inventory_font_namespaces.py`。`tools/build_font_binding_probe.py` 按 references/probes/ 下 hash 锁定计划，一次构建三别名的 raw 对照、geometry 候选、独立反向检查及对应 TOC；只写全新隔离目录、不部署、不启动游戏。完整命令和证据边界见 docs/FONT_BINDING_AUDIT.md。

新增 `tools/inspect_ui_fonts.py --deep --text-token TOKEN`：在显式 hash 锁定的参考包间解析组件前缀、已知嵌套结构、STYLE_ID 和 UIStyle 状态表，输出静态字体候选路径。`tools/probe_ui_style_font.py` 在 raw 副本上构建同尺寸字体引用探针；不部署、不启动游戏。完整参数、原版/对照/候选 hash 与覆盖边界见 docs/UI_STYLE_GRAPH.md。

`tools/inspect_font_references.py --consumers` 枚举可解析 tagged 对象中的直接 Font/MultiFont ObjectProperty 引用，保留 import/export 身份、逻辑偏移与覆盖缺口。它与 `--inventory` / `--object` 互斥，不启动游戏、不修改资源。命令、62 包实测和组件前缀缺口见 docs/FONT_CONSUMERS.md。

## 最小补字原型（独立输出，未获游戏验收）

Xenia 测试必须基于用户提供的 `xenia/xenia-canary.config.toml`，不得静默替换为默认配置或覆盖画质、分辨率、时序及输入设置。`tools/launch_xenia.py` 保存逐字节配置快照，仅隔离 storage/content/cache/log；启动及加载核对见 [XENIA_TESTING](docs/XENIA_TESTING.md)。配置加载成功不代表中文显示通过。

可选依赖：`python -m pip install -r requirements-font.txt`。Noto 字体固定来源及 hash 在 references/font-sources.lock.json，字体原件只放本地 build/font-source。LZX 的本地构建、固定源码与许可见 docs/LZX_RESEARCH.md。

补字 CLI、hash 参数及两字计划见 docs/FONT_SUPPLEMENT.md；独立字体、Startup 与 MC2Game 驻留别名都应按锁定计划处理。补字输出只存 build，不覆盖原件。TOC 只更新明确验证的文件大小字段，见 docs/TOC_SIZE_REBUILD.md；它不证明所有运行索引均有效。四份候选文件的本地清单为 build/font-supplement/v2/deployment-plan.json，目前未部署中文试验。

## 三别名最小补字装配（2026-10-19）

`tools/build_font_supplement.py` 按 locales/zh-Hans/font-build-disc1.json 或 locales/zh-Hans/font-build-disc2.json一次构建三别名补字候选、该盘仅字体大小变更的 TOC、原始字节对照和独立备份恢复检查。完整命令、输入提取、依赖、schema 与恢复边界见 [FONT_BUNDLE_BUILD](docs/FONT_BUNDLE_BUILD.md)。要求全新隔离输出；不部署、不改文本、不运行游戏，不把两字技术候选当发布补丁。

## 文本候选与字体覆盖（2026-10-19）

通用 `tools/audit_text_font_coverage.py` 按原容器 hash、稳定 ID、源值 hash/原文和保护标记顺序验证修改计划，内存回写/反向还原后检查所有显式 Font 的字面字符 remap 与指标；只写新报告、不选运行字体。`locales/zh-Hans/text-probe.json` 已保存仅一条两字技术探针的源值 hash 计划，不需要私有 changes 文件；`build_coalesced.py` 可直接用同一计划构建独立文本副本。完整命令、双盘/负对照/逆向证据及边界见 [TEXT_FONT_COVERAGE](docs/TEXT_FONT_COVERAGE.md)。未开始批量翻译。

## 字体/文本/TOC最小候选装配（2026-10-19）

`tools/build_locale_candidate.py` 按 locales/zh-Hans/candidate-disc1.json / candidate-disc2.json 校验所有依赖真实字节，再一次生成原路径形状的5资源候选、原始对照和备份恢复检查。拒绝原件/字体输入目录内输出，不信任上游manifest成功标志，不启动或部署。命令、依赖、schema、双盘与整树复现证据见 [LOCALE_CANDIDATE](docs/LOCALE_CANDIDATE.md)。它是离线技术候选，不是完整游戏目录、安装包或发布补丁。

## 搬移候选的独立复核（2026-10-19）

`tools/verify_locale_candidate.py` 无需原游戏根目录或原字体bundle，只读候选内的已校验对照/候选/恢复文件及可信repo计划，独立重放Font、文本、TOC并比对metadata；不调用构建器、不信任成功布尔值。要求严格闭合文件集，拒绝多余文件/链接/错盘/伪报告。原manifest可信hash可显式锚定；不传时不会宣称原metadata字节身份已证明。完整命令和真实负对照见 [CANDIDATE_REVALIDATION](docs/CANDIDATE_REVALIDATION.md)。报告必须写在候选树之外，不部署、不启动游戏。

## 双盘差异报告（只读）

在两份完整哈希清单准备后，执行：

```powershell
python tools/compare_discs.py build/disc1-hashed.json build/disc2-hashed.json --output build/multidisc-research/disc-comparison.json
```

输出包含双方身份、逐文件 SHA256/大小/位置及四种分类，不执行整合。已有输出拒绝覆盖。未来整合→汉化回写的规划见 docs/MULTIDISC_RESEARCH.md；目前没有正式合盘构建命令，汉化可以独立推进。

## 原始通用规范（下列命令仅示例）

---

# Building

This document defines how to rebuild the localization project from a clean repository checkout plus user-supplied original game files.

The build process should be reproducible, documented, and independent from private local working directories or undocumented manual steps.

---

# 1. Supported Game Version

Document the exact supported game build here.

Include when applicable:

- game title
- platform
- region
- distribution or store version
- executable or ELF filename
- version number
- file size
- SHA-256
- important archive hashes

Example:

```text
Game:
Platform:
Region:
Distribution:
Version:
Executable:
File size:
SHA-256:
```

Binary patches must not silently modify unsupported or unknown versions.

---

# 2. Requirements

List all required tools and dependencies.

Examples:

- Python 3.x
- Visual Studio Build Tools
- CMake
- Ninja
- Pillow
- ffmpeg
- external archive tools
- original game files
- specific redistributable fonts

Do not assume dependencies are already installed.

Where practical, provide exact installation commands or version requirements.

Example:

```bash
python -m pip install -r requirements.txt
```

---

# 3. Original Game Files

Clearly list all original files that the user must provide.

Do not include copyrighted original game files in the repository unless redistribution is explicitly permitted.

Example:

```text
original/
  GAME.EXE
  DATA.PAK
```

Document where each file comes from and how its version is verified.

If the game requires files from multiple regions or releases, document each source separately.

---

# 4. Repository Preparation

A clean build should start from a fresh clone.

Example:

```bash
git clone <repository-url>
cd <repository-directory>
```

Do not require the user to copy undocumented private work directories into the repository.

If local configuration is necessary, provide a documented file such as:

```text
config.local.json
```

and include a safe template such as:

```text
config.example.json
```

Local-only configuration should normally be excluded through `.gitignore`.

---

# 5. Preferred Build Entry Point

The build process should expose one obvious entry point whenever practical.

Examples:

```bash
python build.py --locale <locale>
```

or:

```powershell
./build.ps1 -Locale <locale>
```

or:

```bash
cmake --build build
```

Avoid requiring contributors to manually run a long undocumented sequence of unrelated commands.

---

# 6. Recommended Build Pipeline

Where applicable, the build system should perform the following steps:

1. verify dependencies
2. verify original game files
3. extract source resources
4. import localization data
5. validate translations
6. collect required characters
7. generate fonts or glyph tables
8. patch executable or runtime code
9. rebuild archives or containers
10. verify rebuilt resources
11. assemble final output
12. generate checksums or manifests
13. package release files

Not every project needs every step.

The build pipeline should reflect the actual technical requirements of the game.

---

# 7. Version Verification

Before modifying original files, verify one or more of:

- SHA-256
- file size
- expected version metadata
- expected byte sequences
- archive identifiers

Example behavior:

```text
Expected:
GAME.EXE SHA-256 = ...

Found:
GAME.EXE SHA-256 = ...

Result:
Supported
```

If the version does not match, stop with a clear error message.

Do not silently continue on unknown binaries.

---

# 8. Build Output

Generated files should go into a dedicated output directory.

Preferred directories:

```text
build/
dist/
out/
```

Example:

```text
dist/
  <project-name>-<locale>/
```

Generated files should not be scattered across source directories.

Temporary intermediate files should be placed under a build directory and should normally be excluded from version control.

---

# 9. Validation

Before producing a usable or release build, validation should check as many of the following as applicable:

- unsupported original game version
- missing dependency
- missing input file
- invalid translation encoding
- unsupported characters
- missing glyphs
- placeholder mismatch
- control-code mismatch
- malformed markup
- fixed-slot overflow
- invalid string lengths
- duplicate IDs
- linked-string inconsistencies
- broken archive structure
- invalid offsets
- unexpected file sizes
- missing generated resources
- failed binary patches
- checksum mismatch

If a validation error can cause corruption or crashes, the build must stop.

Warnings may be used for non-fatal issues such as possible UI clipping.

---

# 10. Rebuilding From Scratch

A future developer should ideally be able to:

1. clone the repository
2. obtain the required original game files
3. install documented dependencies
4. place original files in the documented location
5. run the documented build command
6. obtain a functional localization build

The project should not depend on:

- old private build directories
- manually modified intermediate files
- deleted binaries
- undocumented local tools
- chat-only instructions
- one developer's filesystem layout

Any unavoidable manual requirement must be documented explicitly.

---

# 11. Locale Selection

If the project supports multiple locales, the build system should accept the locale as a parameter.

Preferred example:

```bash
python build.py --locale zh-CN
```

Potential future usage:

```bash
python build.py --locale zh-TW
python build.py --locale ja-JP
python build.py --locale ko-KR
```

Generic tooling should not assume one locale unless the game itself requires that limitation.

---

# 12. Dependency Management

Document all project dependencies.

Where practical, include standard dependency files such as:

```text
requirements.txt
pyproject.toml
CMakeLists.txt
vcpkg.json
package.json
```

Pin versions when reproducibility requires it.

If an external proprietary tool is required, document:

- tool name
- required version
- download source
- whether redistribution is allowed
- where the user should install or configure it

Do not bundle third-party tools without confirming redistribution rights.

---

# 13. Fonts

If the build requires external fonts, document:

- font name
- source
- license
- required style or weight
- expected file location
- fallback behavior

Prefer redistributable open fonts when practical.

Do not commit proprietary operating-system fonts merely because they are installed locally.

If the build uses a system font, document that dependency clearly.

---

# 14. Archive and Resource Tools

If the project depends on custom extraction or repacking tools, document whether they are:

- included in this repository
- built from source
- provided by an upstream project
- external dependencies

If a tool is custom, include enough documentation to rebuild or replace it.

Do not make the project depend on an unexplained executable with unknown provenance.

---

# 15. Binary Patching

Binary patching must be deterministic and defensive.

Patch tools should:

1. verify the target version
2. verify expected original bytes
3. patch only intended ranges
4. fail on mismatch
5. verify patched output

Where practical, generate a report such as:

```text
Patched file:
GAME.EXE

Verified version:
SHA-256 ...

Applied patches:
- text decoder
- glyph lookup
- line width calculation
```

Do not rely on undocumented manual hex editing for release builds.

---

# 16. Build Logs

Build output should clearly show:

- detected game version
- selected locale
- validation results
- generated character count
- generated files
- patch status
- archive rebuild status
- final output path

Errors should explain what failed and how the user can fix it.

Avoid vague failures such as:

```text
Build failed.
```

Prefer:

```text
Unsupported executable version.
Expected SHA-256: ...
Found SHA-256: ...
```

---

# 17. Release Build

Document a dedicated release build command when appropriate.

Example:

```bash
python build.py release --locale <locale>
```

A release build may additionally:

- clean previous output
- run strict validation
- build optimized binaries
- generate checksums
- generate manifests
- copy documentation
- assemble installation instructions
- create an archive

The exact process should be reproducible.

---

# 18. GitHub Release Packaging

The source repository should normally contain:

- source code
- translation data
- build scripts
- documentation
- patches
- reproducible assets

GitHub Releases may contain:

- ready-to-use localization packages
- installers
- prebuilt redistributable tools
- large generated files
- optional media subtitle packages

Do not use the repository root as a storage area for release archives.

---

# 19. Clean Build Test

Before a major release, perform a clean build test.

Recommended procedure:

1. create a fresh clone in a new directory
2. do not copy any old build output
3. provide only documented original game files
4. install only documented dependencies
5. run the documented build command
6. compare the result with the expected release output

This test helps detect hidden dependencies on the developer's local environment.

---

# 20. Reproducibility Notes

Perfect byte-for-byte reproducibility may not always be possible.

Possible causes include:

- archive timestamps
- compiler version differences
- non-deterministic compression
- external proprietary tools
- media encoders
- file ordering

If output is not byte-identical, document what level of reproducibility is expected.

Examples:

- byte-identical output
- functionally identical output
- identical translation resources but different archive timestamps

Do not claim deterministic output unless it has been verified.

---

# 21. Troubleshooting

Document known build failures and solutions here or in:

```text
docs/PITFALLS.md
```

Typical issues include:

- incorrect game version
- missing dependencies
- wrong file paths
- encoding failures
- font coverage failures
- archive rebuild errors
- compiler architecture mismatch
- missing external tools
- antivirus interference
- path length problems

Important troubleshooting knowledge should not remain only in chat history.

---

# 22. Project-Specific Build Notes

Use this section for project-specific information that does not belong in the generic sections above.

Examples:

- required regional assets
- special disc extraction steps
- emulator-specific testing requirements
- console image rebuilding
- source-port dependencies
- unusual asset conversion steps

Remove unused template notes when adapting this document to a real project.

---

# 23. Final Build Standard

A mature project should make it possible for another developer to rebuild the localization using:

- a clean repository checkout
- documented dependencies
- documented original game files
- documented build commands

The build process should not depend on the original author's memory or private local environment.

## Experimental runtime diagnostic copies (2026-10-18)

These commands require locally supplied originals and an explicitly built native
LZX decoder (see docs/FONT_RESEARCH.md). They are not a release pipeline:

```powershell
python tools/decompress_package.py INPUT_PACKAGE --sha256 ORIGINAL_SHA256 --lzx-library PATH_TO_DECODER --output NEW_PACKAGE --report NEW_REPORT
python tools/launch_xenia.py --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --game build/poc-game/disc1/default.xex --run-dir build/UNIQUE_RUN --keyboard-test-input --launch
```

`decompress_package.py` defaults to zero-padding to 32768 bytes, accepts only the
verified profile, preserves decoded object tables/payload and clears all three
compression states. `supplement_font.py --raw-atlas` is opt-in raw bulk output.
Neither command implies Chinese display or console compatibility. For table/TOC
updates and exact runtime boundaries see docs/RUNTIME_TEXT_BINDING.md. Keep all
originals and restore deployed resource copies before another control test.

### Existing-glyph binding probe

`tools/probe_font_mapping.py` is an opt-in same-size diagnostic for an existing
remap entry, not a font supplement or translation builder. Require the original
package hash, Font object path, codepoint and expected glyph. Never target an
unknown version. See docs/RUNTIME_TEXT_BINDING.md for the exact CLI shape and
negative-result boundaries; generated game packages remain local under build/.

### Duplicated geometry diagnostic

`probe_font_mapping.py --geometry` opts into same-size donor-metric copying in
both tagged/native records while preserving remap and texture bytes. Original
hash/mapping/donor bounds remain mandatory. Reports carry old/new patch bytes for
an independent inverse-copy check. See docs/FONT_REFERENCES.md; no diagnostic
candidate should be mistaken for Chinese display acceptance.


For embedded Font discovery, `tools/inspect_font_references.py --inventory`
accepts the same hash/decoder/output arguments as the default inspector and lists
Font/MultiFont class candidates without assuming a font-named package. It is
exclusive with `--object`. See docs/FONT_REFERENCES.md for the newly identified
MC2Game.xxx copy and its still-pending raw-package interactive control.


## UI ScriptStruct默认值与原生声明（2026-10-19）

`tools/inspect_struct_defaults.py` 只读解析明确hash锁定的446/25元数据、继承声明和持久默认值；`inspect_ui_fonts.py --deep --audit-bindings --audit-struct-defaults` 进一步按Class/outer/类型引用绑定renderer字段。Bool值偏移已修正为tag-header位置，非空payload位置；不修改游戏资源。完整命令、6定义/4绑定结果和原生运行边界见 docs/STRUCT_DEFAULTS.md。


## UI函数声明与native参数桩（2026-10-19）

`tools/inspect_function_metadata.py` 只读验证hash锁定的446/25 Function声明与精确native参数桩。`--object FULL_PATH`可重复；`--class UIComp_DrawString`清点该Class直属Function，不能与--object并用。全类23项中18项通过、5项非native脚本显式保留，返回exit1；定点11个native方法返回exit0。输出必须全新，复读后重查原包；不执行函数。命令/字段/测试及未验证边界见 docs/FUNCTION_METADATA.md。


## UI布局脚本的显式opt-in分析（2026-10-19）

在函数审计命令加`--include-scripted --reference-package Core <Core.xxx> <SHA256>`，按有界语法解析5个layout wrapper并绑定Core.Object操作符声明；全类由默认18通过/5未解析变为23通过/0未解析。输出含typed AST、source-like语句和纯语法控制边，既不执行也不部署。原/引用包hash与profile在加载可选decoder前全部校验。完整命令与Context skip、动态数组索引和native实现未验证边界见 docs/SCRIPTED_UI_LAYOUT.md。


## XEX原生映像只读还原（2026-10-19）

`tools/extract_xex_image.py` 支持hash锁定XEX2 none/basic profile，输出新分析映像/报告及可选原始容器逆向副本；不启动游戏、不补签、不写回原件。显式加密backend的可选版本在requirements-crypto.txt，默认测试仍仅标准库。双盘/双AES实现还原共同映像、原始XEX全字节恢复、PE虚拟布局及认证未验证边界见 docs/NATIVE_IMAGE.md。所有产物只放build/，不进入Git。


## 原生方法静态绑定与字段指令链（2026-10-19）

`tools/inspect_native_bindings.py` 用确切image/plan/native-report hash验证名称表、cold descriptor初始化及查找形状，不执行PPC代码。新VirtualImage只提供有界虚拟字节读取，不按PE raw pointer重映射。18项绑定、字体word/mask指令链、元数据依赖复现命令与运行未验证边界见 docs/NATIVE_BINDINGS.md；工具和20项合成回归仅标准库。

显式换用 references/probes/ui-draw-string-style-selection.json 可增加getter/双条件font overlay与CE/PPC .pdata声明范围验证；原plan输出保持兼容。完整hash/命令、两次bypass与leaf无.pdata条目的区别见 docs/NATIVE_STYLE_SELECTION.md。仍只读文件，不调用游戏函数。

进一步换用 references/probes/ui-draw-string-class-tables.json，显式启用完整U类名前缀→name+2参数→callback写入的只读table→slot128 getter关联，以及getter的双来源分支；见 docs/NATIVE_CLASS_TABLES.md。默认native/style计划保持原报告字节，不推断活动实例或未写字体字段的初值。

references/probes/ui-object-initialization.json 进一步启用metadata size/callback存储链、callback调用点和中间zero-fill调用的只读验证。区间模型只做整数几何，不运行PPC；clear之后仍有未验证初始化调用，不能将中间零值当有效字体默认值。hash/命令和合成验证见 docs/OBJECT_INITIALIZATION.md。

## 启动警告的源值锁定prefix探针

当前双盘candidate计划改用 locales/zh-Hans/text-probe-login.json，将原有两字技术marker用于真正关联两处警告MarkupString的LogIn_NewGame记录；不再把旧Kick候选当警告候选。新增通用sha256-utf8-prefix模式保留源suffix和控制码，不在locale数据中复制完整原文。构建/独立复核命令、精确作用域与未实测边界见 docs/LOGIN_PROBE.md；旧text-probe.json保留为历史独立诊断。
# Offline Font serialization inspection

`tools/inspect_font_serialization.py` consumes a hash-locked reconstructed image
and `references/probes/font-serialization.json`; see docs/FONT_SERIALIZATION.md
for exact invocation and evidence boundaries. Reports must be new. Default
self-authored tests need no game files, decoder, Capstone or target execution.
## Warning font-route candidate

See docs/WARNING_FONT_ROUTE_PROBE.md and tools/build_font_route_probe.py for
the combined five-Font/six-resource candidate, raw controls, explicit identity-
256 option, user-operated QA sequence and read-only full-byte replay. The normal
supplement path still rejects non-remapped Fonts without the exact opt-in.

The standalone `tools/verify_resource_phase.py` checks a selected packet phase
against an explicit resource directory using a mandatory trusted manifest SHA.
It needs neither the font file nor an LZX decoder. Exit0 means resource bytes
match only; exit1 gives mismatches/missing files and exit2 rejects invalid input.
The new JSON report must be outside both input directories. See the warning
probe document for the exact invocation and game-acceptance distinction.

For a player who wants double-click/drag-drop testing, use
`tools/prepare_oneclick_probe.py`. It makes two full independent copies and
publishes the two user-click CMD files only after validation. Preparation never
launches a game and never changes original resources/configuration. Exact
arguments, space needs and local-path dependency behavior are in
docs/WARNING_FONT_ROUTE_PROBE.md.
