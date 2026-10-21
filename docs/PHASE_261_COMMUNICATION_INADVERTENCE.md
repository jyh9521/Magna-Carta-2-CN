# 第261阶段：通信失败三处疏忽语义修订

## 完整上下文与来源保留

克罗塞尔韩/日通信两资源、塞蕾丝汀日文语音资源共21完整分区318物理/184已译计划/134既有调查原值，184源译已完整阅读，原值全部保留不为凑数翻译。按源保留图体大台词分配给Juto而非根据体型猜改Argo；公主/露的条件式反应、塞蕾丝汀对阿尔戈的爱意、克罗塞尔自夸/火焰语气、马雷族与水KAN分别核对。重复Overheat_ch3_01的不同occurrence/ID不合并。184是已复核上下文，不新增primary、翻译或上下文条数。

## 三项源支持草稿裁决

batch116/MC2_communi_Crocell/communi_failure/Juto_ch1_01及batch113/MC2_com_Crocell/common/Communi_failure_01的うっかりしちまった仅表示疏忽，未给出忘记的动作。本轮末行由“一不留神就忘了。”改为“一时疏忽了。”；前两行“打得太投入”/“战斗太投入”独立保持，不把两资源全文归一。

batch113/MC2_com_Celestin/Argo/Communi_failure_ch1_01的うっかりしてたヨ末行由“刚才不小心忘了。”改为“刚才一时疏忽了。”，保留呼唤阿尔戈、道歉、时间语气。三个字段原两次功能换行、标点、资源ID、章节和盘别均保持，不新增遗忘对象或失误种类。

两条明确含忘れない/助けるの忘れてた的塞蕾丝汀台词完整保留“不会忘记了”/“忘记帮你了”，另有源/目标hash负对照，避免将语义裁决误做全局删除忘记。其余181旧目标与134原值不变。新candidate-decisions/communication-inadvertence.json及一个精确回归测试记录三处修订/两个保留对照；仍为draft，非人工定稿、官方译法或运行验收。

## 共享库与显式取代

9项共享候选ゼフィ/セレスティン/ルウ/ジュト/クロセル/アルゴ/マレ/大地のタミ/水のタミ逐项命中既有目标；terms的candidate/unverified不变。笑声口癖、角色运行指派和先前燃尽双关继续保留待查，不因语义修订宣称声音已验收。

batch113/116按原hash与精确原条目/目标改写，workflow仅重锁这两批hash；最后翻译批次仍116。42语境profile只更新累计计划header与3旧目标摘要，已有battle-communication-argo-crocell和battle-utterances-argo-celestin-crocell两持久复核记录显式取代3目标hash，原primary数量不变，旧字节在隔离基线/Git历史保留。上下文14082、315独立字幕、4094原值、1499保护换行、42profiles/3页16/16/10、5191观察/0待上下文/5191待运行与工具边界保持；其余14079累计目标不变。

## 构建、回滚与收尾

修改前后字面码点集合完全相同，字库需求等价，字体/字幕/原文对照不变；scope/control ledger及双盘组合/比较引用防御性重锁。双盘27/29资源重建并独立重放，仅候选Coalesced及必要TOC允许改变，现有dist/MC2-display-repair-disc1通过PREPARED/manifest双hash增量刷新至261包。保留260包、原盘/配置/存档/runs及必要基线/回滚研究，不新建ISO或整盘副本，不启动模拟器。

build/phase-261-verification四件MODIFIED_FILE.json（实际batch113/116修改副本bundle）、DIFF_FILE.json、VERIFICATION.txt和可执行ROLLBACK.sh保留修改/原副本hash，列精确命令/输入/字面输出/退出码。独立bundle回滚恢复三处旧译；全部源依赖和旧语境在隔离根恢复，原Git源码1749测试验证旧行为/新文件缺席；主目录保留三项新草稿、显式hash取代和261包。修改及干净Git源码1750测试（1跳过），旧27资源隔离回滚通过；仅清理核实无依赖且绝对路径包含隔离源码的pyc。

合批验证、卫生检查、清理后提交推送核HEAD远端一致与工作区干净，接续未决候选；离线成功不替代游戏画面/语音/全流程验收，所有human_finalized/runtime_layout_approved/game_rendering_verified仍为false。

## 可恢复接续

下一批阿尔戈韩/日两完整通信资源13分区214物理/205已译上下文/9调查原值，针对正常に戻るはずだ的预期语气未在现中文就会恢复正常中显式保留这一候选，核完整事件上下文后裁决；不把205重复累计primary。以当前261包、更新后的workflow/42语境与动态依赖ledger为基线，不套用旧260/199资源身份。本轮三处疏忽与上轮四处这种人已修订，不重复处理。

### 第261阶段验证辅助脚本编码修复

首次完整资源核验在日文忘れ保留对照处失败：辅助脚本一次省略encoding的read_text在Windows默认代码页解码后将日文断言字面量变成乱码。修改源码1750和独立旧Git源码1749测试均已通过，双盘重放和同目录增量刷新已完成；失败没有修改译文或放宽断言。保留verify-phase.failed-encoding.py及verify_phase.failed-encoding.log，重新从260原脚本按UTF-8生成261验证脚本，仍断言同一忘れ来源与原目标hash；改用新的source-rollback-utf8和reproduced-workspace-full-resource-utf8隔离输出完整复验，不重复刷新/重建或删除旧证据。后续所有文本read_text/write_text须显式encoding=UTF-8。
