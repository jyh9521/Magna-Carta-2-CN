# 第160阶段：露指代修订、动物回忆短剧与有界scope整合

2026-10-21，从48a7214干净HEAD/远端一致、workflow最后INT批次116接续。落实前轮两候选并合批Live3六完整场景175及三关联UI，共178新上下文观察、2处已有draft修订。不追加批次117覆盖旧ID，14082 INT/315cue draft与1104 candidate保持，非人工定稿。

## 两处已有草稿修订

原batch096的CSMB_Live2_004/voc_csmb_Live2004_09：回想起对露的感谢，句中“他总是”改“她总是”；voc_csmb_Live2004_24：“丢下他”改“丢下她”。同一露在Q11被称姐姐，故统一汉语指代；韩文这两句无性别字，源不改。精确ID/源译hash/旧新全文与来源见前轮PHASE_159及本轮candidate-revision-followups.json。只替换两个唯一标量，两个entry的review/draft/行策略等其余元数据逐项相同；原批次其他值和全计划14080旧值保持。

workflow只更新batch096计划hash，重新生成完整共享计划及164文件工作区；16份context的计划canonical锁明确重锁，两个目标hash以INT-context-supersessions.json明确取代。149的batch047措辞修订保留，不回退。字体字面字符需求仍2446、无新增/删除，原font-only实验scope仅更新workflow身份并保留历史未部署/未验收字段。literal-control ledger源回放证明控制形状未变，只重锁完整计划身份；不借措辞变更放行TAB或其他控制码。

## 七组scope整合与82理由注释

16份profile均32scope，成员远低于1000；不加第17份、不放宽上限。仅合并同一profile中同document/section、complete_section=false且键集合不交的七对：

- mare-medicine-alliance：CharacterName/Default索引10+26，Item/Valuables14+25，Compose/Chapter11的22+30，共释放3。
- opening-layout：CharacterName/Default6+25，UI/information10+31，共释放2。
- party-tutorial-werewolf：CharacterName/Default12+31，释放1。
- identity-contract-trust：Item/Valuables11+28，释放1。

索引为48a7214旧profile的0基scope索引。完整原scope、键、理由均保存在阶段160baseline/预检以及Git历史；新scope保留连接后的原理由。明确键并集没有扩大选择：Chapter11并集41仍非全部42源字段，未计划27继续排除。隔离预检505scope的套件与旧512scope在所有ID/源译hash/邻序/disposition、策略及保护分隔上相同，82条reason文本变化逐一映射。不能声称整个context行字节未变，也不把理由变化混入目标修订。释放7后用于本轮7scope，最后仍16×32，各成员≤1000，schema/工具门禁不变。

## Live3六完整场景175字段

CSMB_Live3_001–006分别22/35/22/48/10/38，物理源与计划完整。前轮22预读本轮统一计入，不另开小批。

001幼兽铖被带回、南部军宿舍禁止养宠物、朱特被咬，猜迷路/戒备/自己吓人各是角色判断；002后续明确接受恢复术，治疗时间不提前到受伤前。旧岛上母狗产仔敏感、拿饲料逗鹅后被追、小狗对比，是朱特讲述及洁菲质疑，不能无条件认定所有动物天生憎恨朱特。

003、005转到阿尔戈与塞蕾丝汀，偷听、向南部军学来的打趣、黏人、理想型与自夸，保留双方不同回应，不改成共同承认恋情或宿舍已同意养宠物。阿尔戈说上战场没人照料，塞蕾丝汀设想不用照料的聪明动物，不是已通过的例外规则。

004回忆兔子咬鼻后肿如草莓，不是单纯变红；旧猫占床/生仔、邻居接走、体弱没活多久、临终望向朱特家是回忆及转述，保留“好像/听说/或许”。朱特害怕拿真剑见血、动物可能闻到血腥味与知晓其未知过去，均是自我推测；洁菲提出时间、相处诀窍的其他解释，没有确认隐藏身份或动物AI机制。猫离世后的后悔不写成已证实恨他。

006害怕恢复记忆、洁菲母亲去世后独立的对照与支持按当时知情层次保留；承诺今后努力亲近动物不是已完成治愈。塞蕾丝汀带来会说话的猫猫想当宠物，被解释猫猫并非宠物；食物承诺与其准备离开保留。该短剧与其他分支的猫猫认识程度不据排列强行串成固定时间轴。

MC2UI_Field/Live Drama明确选择Drama3_Name/Character/Story三键，原8UI键不重计；现11计划UI键全部观察。梗概的源译前导空格、两段功能换行保持，新增1保护分隔。铖/쳉等11候选术语锚点复核，candidate/unverified不升级；旧角色名/315字幕不重计。

分配：mare-medicine-alliance接前三scene，opening-layout接第四/五，party-tutorial-werewolf接第六，identity-contract-trust接三UI一scope；所有新增178源序锁与完整源范围逐项核。累计7404 INT/315cue，策略3673→3772，上下文待审1518→1419，保护分隔210→211，全部5191运行布局/TAB仍待核。

## 统一验证、增量刷新与恢复

基线/修改/索引导出干净源码各1635通过(skipped=1)，双盘上下文CLI同报告。25个canonical输入隔离还原（原batch096、workflow、共享计划、font scope、literal ledger、16profiles、双盘composition/comparison计划），重算旧16套件回到7226/3673/1518；主修改保持2修订及7404上下文。两目标/82理由之外，旧观察身份/邻序/策略保持。

两个原镜像、八提取源、双盘18176实际值、14082回填、其他18174值及4094未计划原值、24held和11调查原文保持；315字幕/44资源有效锁延续146三处明确取代。双盘27/29资源独立重放，56原始资源逆恢复；所有字体/字幕与原文对照不变。164文件新工作区可重现，不将149旧工作区误称当前。

现有dist/MC2-display-repair-disc1按PREPARED和新packet manifest双hash增量刷新；仅实际变化资源与入口元数据写入，逐文件before/after备份。等长指代修订的TOC以实际比较决定，不强造差异。旧149包27资源在独立目录恢复并实际核对；原盘、配置、XEX、存档、runs及未涉及文件元数据保留。新活动包为build/phase-160-verification/disc1-comparison，活动依赖表同目录current-packet-hash-preflight.json，旧149组件和两轮必要回滚均保留。不生成ISO/整盘副本、不启动模拟器，离线验证不替代游戏验收。

四件证据为MODIFIED_FILE.json（修改后的batch096副本）、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh，均在build/phase-160-verification并结束前重开。精确基线/修改/回滚命令、输入、字面输出与退出码见VERIFICATION。只清理已核实可再生无入口依赖的隔离测试pyc，保留失败预检/回滚/研究。提交推送核对HEAD=远端及工作区干净后继续：先核CSMB计划覆盖及五处未计划源，不翻占位凑数，再从未审NPC/任务/关联系统按完整上下文接续；不以一次提交视为全部汉化结束。

实测增量刷新4文件：candidate/MC2Game/Localization/Coalesced.int、PREPARED.json及两个既有测试入口cmd；TOC字节完全不变，未写入。旧1363依赖1335原hash保持、28项为其中24canonical输入及4实时刷新有意变化；新增原batch096直接hash锁（此前通过workflow摘要间接锁定）；新闭包1834项逐一核hash。旧149包27资源独立恢复通过，当前candidate/raw各27资源匹配，配置/XEX/存档/runs及其他文件元数据保持。
