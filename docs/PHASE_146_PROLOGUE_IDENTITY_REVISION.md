# 第146阶段：序章人名修订、身份揭示与条件性信任

2026-10-21，从8827508干净状态接续。translation-workflow.json仍以批次116为最后INT翻译批；本轮独立字幕修订不伪造新的INT批次。285项新上下文观察为252 INT＋33字幕，另修订旧序章3处人名；不将审读数量或旧cue修订算作新增翻译。

## 三处实际改译与依赖图

源슈엔자이트对应当前INT候选“修恩扎伊特”。旧序章在64104–72462、101843–107464、126726–131461毫秒三cue使用“修恩泽特”，本轮仅改为“修恩扎伊特”。十八cue中其余十五条目标不动，原始input/source哈希、时间、class、clear、BOM、br、数字及其他受保护TOKEN保持。原计划SHA256为69846a923529ee764058e4eb592c02c7eab98a9741d6944d2e43a281ccfceef4，修订计划为1425efc96fca5734efbeb253176cee655be1c4d8c7b255eb2af84bc34c8212e9；保持草稿及候选状态。

不仅更新subtitle-profile：cumulative-font-route/route.json的additional_text_plans也直接锁定序章。composition要求font_component的plan_canonical_sha256与route相符，因此实际重新生成route-probe，不能把旧125组件的manifest换个hash后继续使用。双盘字幕bundle、composition及raw comparison全部从锁定原始资源重建，各盘保留各自来源，不合盘。七字体对象及双盘INT候选字节和旧包一致；第一盘候选仅序章与TOC两资源变化，第二盘全部候选资源字节不变。新的元数据身份不等于所有资源内容变化。

首次修改后单元测试发现display-fonts与readability-fonts两个旧模板仍直接锁定旧序章hash，三个测试失败。保留失败日志，补齐两个模板的显式关联引用；通过各自prepare从原始资源独立再生成全部输出，在内存中检查源、七字体语义/墨迹与TOC逆变换，记录输出hash而不另造整包或ISO。没有放宽测试、删除hash门禁或假称旧组件已匹配新计划。旧模板/计划完整字节在canonical-baseline保留，历史组件不删。

## 连续剧情与关联链

九完整源序场景220项：06_060(11)、070(14)、100(23)、110(4)、121(15)，07_20(68)、23(18)、25(21)、30(46)。关联32项：完整06_dunanhill NPC18字段、完整06_225_0拉提女王后续任务12字段、Avisticket/Avisticket_D终身免费运输券名称说明2字段。旧九节草前置任务、伊格顿名字与鲁哈尔特地名复用，不重算；女王面具证物、接取/拒绝/进行中/完成与QUEST%s计数不改，不扩写虚构药物配方。

- 梅莉莎承认知道哨兵制造及朱特未能说服她分别保留；06-80未说完的关系提示不能自行补全。朱特幸存是保护膜及角色关于无意识发动的推测，不写成已经完全理解的能力机制。
- 06-120/121/122与07-10/20将身体被操纵、失去记忆归来、承认过去罪行、同伴质疑和继续救援区分。没有用失忆抹去伤害，也没有把继续同行改成所有人无条件原谅。回忆中的洁菲承诺不误写成当前场景新承诺。
- 关于再次被控制时的极端条件性约定，仅按角色台词保留；不是已经执行的结局。其他同伴支持、警惕、担忧仍并存。
- 阿维斯终身免费票不代表能进入所有地区：交战及危险地区仍被运输队排除，临时代办和后续晶柱服务有不同阶段。
- 逮捕命令与士兵指控不等于部队真的通敌。劳德亲眼所见秘密会面、关于阴谋的推断、王位许诺与尚不清楚行动时机分别保留，不能把角色不同证据层次合并。
- 山丘NPC“150年前战争”“听说也有怪物兵器但无确切记录”保持数字及传闻限定，不把传闻升级成史料结论。

五个新独立字幕来源均由第二盘manifest的resource＋原SHA唯一匹配：06-80两cue、06-90八cue、06-120十三cue、06-122三cue、07-10七cue，共33；源译逐cue锁、时序与逆重建保持。旧161cue历史观察保留，三处旧目标锁通过subtitle-context-supersessions.json显式标为已被修订取代；累计194cue/28资源，不重计旧序章十八cue。

## 当前测试包、回滚与验证

使用refresh_oneclick_probe对既有dist/MC2-display-repair-disc1受hash保护增量刷新，不生成游戏副本或ISO，不启动模拟器。仅修改candidate中的序章/TOC及PREPARED.json、中文/原文两个入口，共5文件。刷新前原204依赖全核，刷新后199保持、5项有逐文件before/after及保留备份。raw-controls、配置、XEX、runs、存档与其他文件元数据保持。当前入口引用build/phase-146-verification/disc1-comparison；新的完整依赖表为同阶段current-packet-hash-preflight.json。

独立计划副本回滚恢复旧3个人名并重新通过十八cue逆重建与时序验证；另对真实5文件备份进行隔离还原，补齐旧manifest声明的其余有界资源，旧27资源candidate完整匹配。主计划和当前测试目录保持新译；回滚测试未触碰实际玩家包。ROLLBACK.sh拒绝未知目标hash。

新identity-contract-trust.json为252成员/12 scopes，旧十三profile及3544项投影保持。累计3796 INT、1904策略观察、3287上下文待审；112功能分隔，全部5191运行布局仍待核。未知0320_50、05070_27及24held随未变INT保留。基线/修改/干净索引源码各1632通过（skipped=1）；双盘上下文CLI、源哈希、双盘14082旧译/未改值、315独立字幕全量重放、56 raw回滚、164工作区复现、字体覆盖/墨迹与新当前依赖核验。TAB及真实画面仍未验收。

证据build/phase-146-verification：MODIFIED_FILE.json、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh，精确命令/输入/输出/exit见记录；保留canonical-baseline、live-backup、rollback-check及初次失败日志。仅清理经绝对路径核验可再生成的隔离源码pyc。统一验证清理、提交推送并确认HEAD/远端及干净状态后，按实际容器顺序继续下一完整场景组及关联链。

## 重建顺序

使用各JSON中已锁定输入，先生成`build/phase-146-verification/route-probe`，再依次生成每盘`discN-bundle`、`discN-composition`、`discN-comparison`。工具分别为`tools.build_font_route_probe`、`tools.build_subtitle_bundle`、`tools.compose_locale_resources`、`tools.build_locale_comparison`。保留旧输出时选择新目录并明确更新组件引用及SHA，不能覆盖或删去尚有入口/回滚依赖的组件。完整实际参数与返回值在build-records.json及VERIFICATION.txt。字库使用锁定NotoSansCJKsc-Regular.otf及ue3_lzx.dll；原盘仅作只读提取源。
