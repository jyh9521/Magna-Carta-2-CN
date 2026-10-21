# 第262阶段：阿尔戈恢复预期语气草稿裁决

## 完整上下文及精确修改

阿尔戈韩/日两通信资源13完整分区214物理字段，205已译计划源译全部阅读，9既有调查原值保留。205是复用上下文，不新增primary复核、译文或上下文条数。章节、角色、重复字段和盘别独立保持；韩文印象/看来、条件/问句、协同请求及取消/成功/失败分别按源核对，不把角色发言当作数值机制证明。

唯一修订为batch112、MC2_com_Argo.int/common/Abnormal_bad_02：

```text
源：落ち着け、すぐに\n正常に戻るはずだ\n動かないほうが良い
前：冷静点，很快\n就会恢复正常。\n最好别动。
后：冷静点，很快\n应该会恢复正常。\n最好别动。
```

はずだ表达预期，旧译的直接“就会”缺少该语气；仅第二行补“应该”，保留两次功能换行、其余文字、标点、source ID/hash、资源及盘别。相邻_01すぐに治してやる的直接承诺、_03すぐに良くなる的直接陈述，以及韩文진정해. 곧 괜찮아질 거다.的三个独立ID维持原译，记录五个source/target摘要负对照，不做全局软化。全文保留全角１及明确忘れるな/不要忘记；声音指派、燃尽双关等候选不借此定稿。

新增candidate-decisions/argo-recovery-expectation.json和一个精确回归测试。batch112.review仍draft；human_finalized/runtime_layout_approved/game_rendering_verified均false。

## 译库、旧译及重锁

共享候选九项逐项查源字面：ゼフィ三处/セレスティン一处命中既有目标，其余七项本组零字面命中，不混称全部出现。terms的1104项candidate/unverified及字库/字幕配置不变。累计14082 INT中其余14081旧译、4094未改原值、315独立字幕/44资源、1499保护换行、42语境profile/3页16/16/10保持；5191观察、0待上下文、5191待运行不变。最后翻译批次仍116，不新造117批或重复primary快照。

batch112在原字节/hash和完整条目守卫后精确修改；workflow只重锁该批hash。42profile累计计划header与唯一目标hash、旧battle-utterances-argo-celestin-crocell复核记录显式target_supersession同步，原primary计数不增。原字节在canonical-baseline及独立旧Git源码保留。修改前后字面码点集合相同，font scope的workflow锁及literal-control ledger按等价需求重锁，不重建字库、不改独立字幕。

## 完整验证及现有入口

双盘27/29选定资源重建、独立重放、所有源hash、INT逐值回填、字幕时间轴/旧目标保留、原值、上下文及保护换行分别核对。仅候选Coalesced及必要TOC允许改变；现有dist/MC2-display-repair-disc1通过PREPARED/manifest双hash增量刷新为262包，五个实际变化文件有逐字节备份，旧27资源独立恢复。原盘、配置、存档、runs及261必要依赖保留；不生成ISO或整盘副本，不启动模拟器。

build/phase-262-verification保留MODIFIED_FILE.json（实际batch112修改副本bundle）、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh；验证记录包含准确命令、输入、字面输出、退出码、修改字段及四条绝对路径。独立bundle恢复旧目标且主目录保留新译；源依赖隔离恢复及旧Git源码1750测试验证旧行为，新文件缺席；修改源码和干净Git源码1751测试（1跳过），与双盘回填/旧资源独立回滚分开记录。清理仅限已核实无依赖且绝对路径包含在隔离源码根的pyc；所有入口和研究证据保留。提交、推送后核HEAD远端一致及工作区干净。

辅助脚本最初在完整队列含三条相同韩文源的不同ID时仍沿用“三个负对照”预期：实际为两个日文+三个韩文，共五个，不能按相同文本合并ID。修正后从已完成canonical更新之后恢复，不重复改写、不重复刷新；prepare-resume-evidence.json保留中断与接续依据，五个完整source/target对照均纳入测试。所有文本I/O继续显式UTF-8。

## 可恢复接续

下批为MC2Compose六个完整PartyTalk分区300物理/218已译上下文/82原值，针对既有克罗塞尔놈들译为“杂种们”的语气候选，先核整组角色语气和剧情，不将候选直接定稿。使用当前262包、最新workflow/archive/依赖ledger接续，不复用261旧hash；不重复本轮应该会或前两轮疏忽/这种人修订。离线通过不是游戏、语音或全流程验收完成。
