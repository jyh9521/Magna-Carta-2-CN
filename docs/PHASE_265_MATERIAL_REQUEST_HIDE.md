# 第265阶段：材料请求与怪物皮说明草稿修订

## 合批上下文

Ingredient38与Valuables154两个完整分区192字段全部源译阅读，再关联完整Ch01_105_0送工具任务20字段，共212。212是既有primary上下文复用，不新增翻译、primary或上下文数量。材料名/来源/用途、关键物品请求方/收件方、传说语气、配方用途、尾空格及同key_laboratory不同occurrence保持；不把名称为卡片而描述为钥匙等源差异擅自归一。

## 两处实际草稿修改

- batch089、Ingredient/tool_box_D，빌터 아저씨가 부탁한 공구.：“比尔特大叔托人拿来的工具”改为“比尔特大叔要的工具”。完整任务明确比尔特委托海因格尔，后者转托朱特，从箱中取出工具送往海边比尔特；完成对话才说送来了。旧句未必表示相反运输方向，本轮不将其强判为供给方错误；新句直接保留请求关系，去掉物品说明中已拿来/视点不清的额外表达。
- batch044、Valuables/monster_leather_D，가죽을 가진 몬스터에게서 얻을 수 있다.：“可从长有皮革的怪物身上取得”改为“可从有皮的怪物身上取得”。去掉生物长有加工皮革的不自然搭配，不增补皮毛、怪物种类或掉落率；怪物皮名称本身保持。

两项均无功能换行，ID/source hash及标点策略不变。20任务字段全部保留source/target hash作对照，包含“村长家前/旁”的原文差异、正在委托/已交付的阶段区别及QUEST%s和计数占位符，不因物品描述修订而改任务阶段。新增candidate-decisions/material-request-and-hide.json及一项精确回归测试；仍draft，非人工定稿或游戏验收。

## 译库与工程验证

七项既有共享候选实际字面命中：카몬드14、빌터10、네코네코6、후안2、메레4、리안나1、공구9，目标均匹配；terms及1104项candidate/unverified保持，本轮不改术语。使用264阶段状态词修订后的真实terms hash作资源验证基线，不回退181阶段的旧术语身份。

workflow只重锁batch044/089两个计划，最后翻译批次仍116；42语境profile累计header及两项目标摘要、archive、font scope工作流hash、literal-control ledger和双盘资源引用随精确变更重锁。materials-field-valuables旧复核显式取代两个目标hash，primary数量不增。字面码点集合等价，字库与字幕不改。其余14080累计INT目标、4094原值、315独立字幕/44资源、1499保护换行、42profiles/3页16/16/10、5191观察/0待上下文/5191待运行保持。

双盘27/29选定资源重建及独立重放，逐值回填、未改原值/旧译、源hash、字幕/语境与保护换行分别验证。现有dist/MC2-display-repair-disc1只通过PREPARED/manifest双hash增量刷新至265包；允许候选Coalesced及必要TOC变化，保留264包、原盘、配置、存档、runs和基线/回滚/研究依赖。不生成ISO或整盘副本，不启动模拟器。

build/phase-265-verification保留实际两批修改副本bundle MODIFIED_FILE.json、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh，记录修改字段、四条绝对路径及BASELINE/MODIFIED/ROLLBACK精确命令/输入/字面输出/退出码。独立bundle/源依赖与旧Git源码1753测试恢复旧行为，主目录保留两项新草稿；修改与干净Git源码1754测试（1跳过），旧27资源独立回滚另证。只清理绝对路径包含在隔离源码根、已核实可再生无依赖的pyc。验证、仓库卫生、清理后提交推送，核HEAD远端一致及工作区干净。

## 接续

下一组朱特、洁菲、阿尔戈的六完整武器分区215物理/213计划/2调查原值，核既有压倒敌人/睡眠比喻及名称候选；未完攻击+原值不补数值，未知机制不按比喻断言。两处物品修订及前阶段26状态词修订已经完成，不重复累计primary。所有human_finalized/runtime_layout_approved/game_rendering_verified均false；离线成功不替代画面、语音和全流程验收。
