# 第263阶段：队伍闲谈敌意语气草稿裁决

## 完整场景与角色上下文

MC2Compose六个完整PartyTalk分区300物理字段、218已译计划逐项源译阅读，82已调查原值保留；218是既有primary的上下文复用，不重复累计复核或翻译条数。朱特的疑问/希望/复仇、阿尔戈的简洁任务指令、洁菲的职责/赎罪、露的敬语报告、塞蕾丝汀的好奇和称呼分别保持。第一任务/第二场战斗、东北/西北、KAN地雷与卡尔玛/卡蒙德、任务链先后和章节12/13重复台词独立ID均核对；不重插已有自动折行策略移除的源物理换行，不翻译占位省略号凑数量。

## 唯一源支持草稿修改

batch110、PartyTalk_Crocell/Ch02_09_09：

```text
源：늙은 여우 협곡의 북부군 놈들.\n각오해!
前：老狐峡谷的北部军杂种们。\n给我等着！
后：老狐峡谷的北部军混蛋们。\n给我等着！
```

完整语境下，놈들和각오해明确是对敌军的蔑称/威胁，但“杂种”另加出身式辱骂。最初“家伙们”候选没有直接采纳：同角色Ch03_09_10的北部军这帮混蛋、Ch06_04_04的北部军混蛋显示既有强敌意语域，“混蛋们”保留粗鲁威胁而不另加出身含义。仅改该词，地名、给我等着、一次功能换行、标点、ID/hash和盘别不变。仍是source-grounded draft，不声称人工或声音表演定稿。

同角色Ch03_05_07家伙/什么货色、Ch03_09_10这帮混蛋、Ch05_12_13那帮家伙、Ch06_04_04北部军混蛋四项source/target hash对照全部保留，不机械统一所有놈들/자식들。火焰威胁、北部军平民惨案及对同伴抱怨按各源保留。新增candidate-decisions/crocell-party-pejorative.json和一个精确测试，旧compose-party-talk复核记录仅显式取代该目标hash，primary数量不增。

## 共享库与资源验证

十项共享候选实际源字面命中：주토15、제피7、크로셀3、아르고7、카몬드5、라 스트라다13、늙은 여우 협곡9、코타마레13、듀난 언덕14、세레스틴2，目标字面均命中；不将루在루할트内的子串误作露。1104术语candidate/unverified保持，不引入新定名。

workflow只重锁batch110，最后翻译批次仍116；42语境profile累计计划header及一目标摘要、archive、font scope的workflow引用、literal-control ledger、双盘composition/comparison引用随精确变更重锁。字面码点集合等价，字体/字幕不改。14082累计INT中14081旧目标、4094未改原值、315独立字幕/44资源、1499保护换行、42profile/3页16/16/10及5191观察/0待上下文/5191待运行保持。

双盘27/29选定资源重建及独立重放、源hash、逐值回填/原值/字幕保留、语境及功能换行核验完成后，仅通过PREPARED/manifest双hash增量刷新现有dist/MC2-display-repair-disc1至263包。允许候选Coalesced及必要TOC变化，现有入口四个变化文件逐字节备份（候选Coalesced、PREPARED及两个入口脚本；TOC大小和字节不变）；独立恢复旧27资源。原盘、配置、存档、runs、262依赖和必要研究证据保留；没有ISO或整盘复制，不启动模拟器。

build/phase-263-verification的MODIFIED_FILE.json为实际batch110修改副本bundle，DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh记录字段、四条绝对路径及BASELINE/MODIFIED/ROLLBACK精确命令/输入/字面输出/退出码。独立bundle/源依赖及旧Git源码1751测试验证恢复旧目标和新文件缺席，主目录保留新草稿。修改及干净Git源码1752测试（1跳过），双盘回填与旧资源独立回滚分开证明；只清理绝对路径包含在隔离源码根且无依赖的可再生pyc。验证、卫生检查、清理后提交推送，核HEAD远端一致和工作区干净。human_finalized/runtime_layout_approved/game_rendering_verified全部false。

## 可恢复接续

下一组选择Karmond剩余55完整家庭165字段（整个分区309中的显式部分），接续黄金clover命名、通常技/普通攻击、어지러움/スタン等既有候选，核名称/短描述/长描述和共享名称，不直接按字面推断机制或植物叶片数。selection.source_ids/family_keys和full_section_physical=309明确保留，不将165称为整个分区。使用当前263包/新workflow与archive/hash ledger，不复用旧资源身份，不重复本轮或先前三轮已修订目标。离线成功不替代游戏画面、语音和全流程验收。
