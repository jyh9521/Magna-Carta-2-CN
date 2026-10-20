# 第130阶段：显式资源登记与累计第一盘增量刷新

2026-10-20。起点HEAD 2091468、干净工作区，核对129文档、BUILDING收尾及workflow最后批次116。本阶段不重复翻译或升级审核：14,082 INT/315cue仍draft、1104术语仍candidate。

## Verified：新合同不替代旧门禁

refresh_oneclick_probe新增可选enrollment/enrollment_sha256，旧调用仍要求完全相同资源集合；没有显式计划的10→27仍拒绝。新schema1/kind=explicit-resource-enrollment计划锁定PREPARED、旧/新packet manifest SHA、盘别，以及每个新增资源的原文SHA和整数size；17份字幕逐条列入locales/zh-Hans/resource-enrollments/disc1.json。

只允许严格增加而不删除旧资源，登记集合必须等于new-old且无大小写重复。新packet必须为129的disc raw-comparison合同；新controls逐项校验。新增raw必须等于原始controls，现有candidate/raw两根中的每个新增文件也必须等于原文。既有raw仍全量匹配新包，所以本轮raw零写入。坏hash、旧PREPARED、错误盘、缺项/多项、已改值/丢失原文件、译文伪装raw、缺少hash或无实际增加均在备份/写入前拒绝。

保持资源路径/32项上限和稳定快照，新增对默认XEX与非写集输入的提交后复核。登记模式检查目标链上的symlink/junction及待写硬链接，防止间接改动其他文件。配置、模拟器程序及XEX只读，raw对照不写，存档/runs不复制、不清理。

## 写前日志与失败回滚

只备份差异candidate与两入口/PREPARED，先逐文件回读原件再写REFRESH.json(status=prepared)。每项atomic replacement前记录写意图，因此原子替换后才抛异常也能按after-hash恢复；尚未改变的文件略过。资源检查与非写集快照通过后才将journal记committed。中途失败或最终journal失败恢复写集并记录rolled-back；检测到外部修改则不盲覆盖其数据。

这提供进程内异常回滚和保留原件/写前证据，不宣称断电恢复或自动重放崩溃日志已经实现。后续要补受保护的独立还原/中断恢复入口；本轮实际还原证明在局部隔离文件上完成，主玩家候选保持新版。

## 实际第一盘结果

刷新前再次独立重放两盘129包，复核所有字体semantic/解码像素、累计INT逆重建、原控制保留、字幕和各盘统一TOC。沿用dist/MC2-display-repair-disc1现有目录，实际只改26文件：23个candidate资源（四字体、完整INT、TOC、17新增字幕）及两启动脚本/PREPARED。旧四开场字幕字节已经相同，无需重写。

candidate从旧262条升级为14,082 INT、七字体及本盘21字幕/152cue；raw仍原文且27/27匹配。PREPARED两phase resource_count更新为27，入口改指build/phase-129-verification/disc1-comparison并锁其manifest；同一入口路径不改。4034个非写集文件size/mtime保持，配置/模拟器/XEX与现有runs/save散列保持。

26项真实备份在build/phase-130-verification/live-backup；每项又在独立rollback-check先写当前候选再按SHA恢复原件，旧十项candidate只读检查通过。主候选与元数据不回退，candidate/raw27项分别重新检查通过。原64项基线引用中仅6个既有live candidate资源有意变化且有备份，其余58项不变；这不是把旧64全体不变的过时结论继续沿用。

第二盘只保留29项局部离线包、14,082 INT和163cue，不生成第二盘整盘测试目录。无ISO、整盘副本或模拟器启动。新增资源登记只是清单合同，不批准TAB运行语义、SmallFont identity、2048 atlas或5191项既有换行策略；literal coverage仍false，离线结果不等于游戏验收。

## 复现与一次性登记

先按125/127/128/129文档复现依赖。登记计划是针对旧PREPARED的单次事务，已刷新目录再次套用会因SHA不符拒绝；不要为重跑随意改hash：

```powershell
python -m unittest discover -s tests -p test_refresh_enrollment.py -q
python -m unittest discover -s tests -q
python -m tools.refresh_oneclick_probe --root dist/MC2-display-repair-disc1 --prepared-sha256 <旧PREPARED-SHA256> --packet build/phase-129-verification/disc1-comparison --manifest-sha256 <新manifest-SHA256> --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --backup build/本轮新建备份 --enrollment locales/zh-Hans/resource-enrollments/disc1.json --enrollment-sha256 <登记计划-SHA256>
```

实际命令、输入和字面输出保存在build/phase-130-verification/VERIFICATION.txt及LIVE_REFRESH.log；不运行CMD入口进行验证。

## 验证、清理、接续

基线1575、新增14项后修改与干净索引源码1589均OK(skipped=1)。自造样本覆盖默认拒绝/显式成功、精确增量/原文/盘/hash/size合同、raw译文拒绝、缺失/用户改值、硬链接拒绝、原子替换前/后中断、最终journal失败、XEX被外部改变时其他写集恢复且保留外部变化、旧API兼容。

双盘源哈希/原ISO、全量合成重放、旧译/未改值、164工作区逐字节复现、24held分类、字幕/字体组件与56 raw回滚再核。四件证据为MODIFIED_FILE.py、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh；修改副本对应refresh模块，旧模块显式登记API缺失exit2，新2→3登记exit0，隔离hash回滚exit0，恢复旧API缺失exit2。真实玩家26项隔离恢复另有证据，不以模块回滚替代资源回滚。

只清理已核实的隔离干净源码pyc，保留原盘、配置、存档、runs、旧/新包及全部必要组件、控制、回滚和研究。提交推送后核对远端/HEAD及干净状态。下一步补独立受保护还原与中断journal审计，再继续存量换行策略/场景上下文复核，不把测试包更新当全部翻译工作的结束。
