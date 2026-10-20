# 第131阶段：独立journal审计与受保护还原

2026-10-20。从b195f43干净状态接续，核对BUILDING收尾及workflow最后批次116。翻译仍14,082 INT/315cue draft、1104 candidate；本阶段不回退现有第一盘候选、不新增翻译或人工定稿。

## 独立入口与边界

新增tools.restore_probe_refresh，refresh模块只加audit_refresh_journal/restore_refresh_journal两个薄API；原refresh/enrollment/atomic_write/main函数体逐段AST源比较保持。原默认同清单门禁及显式新增资源合同不变。

审计必须提供显式root、backup和REFRESH.json的SHA256；journal根必须是所选根，两个目录互不包含。支持既有prepared/committed/rolled-back标签，但实际before/after/conflict状态逐文件按散列判断，不凭标签推断成功。备份before散列、严格数量3..35、三个已安装入口元数据、重复键/大小写路径、受保护路径、symlink/junction/硬链接及原游戏source_root重叠均检查。

写集只允许candidate下的局部资源及既有PREPARED/两CMD入口。raw-controls、配置、XEX/程序、runs/storage/save、用户存档和任意根级文件均不进入还原写集。审计只读：缺失/被改成第三种字节为conflict，CLI输出报告exit1；坏备份、身份或合同为exit2。正常可还原报告exit0，不执行游戏或自动前滚。

显式restore仅对after状态写回原件；已经before的项略过。所有目标必须先通过审计、稳定快照及备份散列，任何冲突均零写入。写意图在替换前登记，异常时回到调用前已观察的状态，包括替换后才抛出的异常；外部未知字节不盲覆盖。成功重核所有before散列并生成新receipt，原journal/备份保持原样；再次执行是0写入且产生另一份receipt。

新输出必须位于两个根外并且不存在。receipt记录源journal SHA、root/backup、恢复数量、already-before及全部before状态，不把旧committed journal改写成一份伪历史。

## Verified：真实资产的局部隔离恢复

实际玩家根只执行一次audit：130的26项全部after、0冲突，root未回退。当前candidate/raw各27项、204项入口依赖/配置/XEX/runs散列全保持，仍14,082 INT/本盘152cue与七字体。

用130的26项真实当前字节和保留原件分别制作两组有界局部副本，没有XEX、原盘或其他游戏资产目录。复制journal只将root改为明确的隔离根，并另记原journal SHA后重新计算本地journal SHA；原journal不修改，也不把改根副本当作原始运行日志。

- committed副本：26 after，独立CLI实际还原26项；
- prepared中断副本：13 before/13 after，独立CLI只还原13项；
- 两组全部26项最终匹配原件，补齐仅4份未改字幕后，旧10项candidate检查均通过；
- 两组备份与journal逐字节保持，当前204依赖再核不变，真实玩家根没有rollback。

这是已落盘完整journal及已知before/after字节混合的离线恢复验证，不是实际断电试验；损坏/丢失journal、未知第三态、磁盘损坏或fsync持久性不由本阶段证明。

## 使用

先审计当前根；只有明确需要还原该次刷新时才选择restore。根和journal SHA必须与保留记录一致，输出须新建：

```powershell
python -m tools.restore_probe_refresh --mode audit --root dist/MC2-display-repair-disc1 --backup build/phase-130-verification/live-backup --journal-sha256 <REFRESH.json-SHA256> --output build/本次新建审计.json
python -m tools.restore_probe_refresh --mode restore --root <待还原的已绑定测试根> --backup <对应备份> --journal-sha256 <对应REFRESH.json-SHA256> --output build/本次新建还原凭据.json
python -m unittest discover -s tests -p test_restore_probe_refresh.py -q
python -m unittest discover -s tests -q
```

不运行CMD/Xenia验证这些命令。还原到旧包后不能继续声称最新累计译文在该根；应依据实际PREPARED与packet重新检查。

## 验证、清理与接续

基线1589，新增13项后修改/干净索引源码1602均OK(skipped=1)。覆盖只读审计、完整/混合中断/已还原幂等、冲突/缺失零写、错hash/root/status/count、坏备份/缺元数据、受保护/穿越/重复路径、硬链接、receipt范围、中断前/后异常逆恢复、receipt失败和原始source重叠。真实26/13恢复另行验证，不以自造测试代替。

再次核对两原ISO、八源hash、双盘完整回填/逆重建、七字体及原TAB保留、315字幕分盘来源、56 raw回滚、164工作区逐字节复现及24held。literal coverage仍false，5191项原显式换行策略未改变/升级批准。

四项证据保存在build/phase-131-verification；旧模块无独立恢复API exit2，新自造5项目标还原exit0，隔离模块hash回滚exit0后恢复API缺失exit2。主源码及真实测试包均保留新版。仅清理核实可再生成的隔离索引源码pyc，保留所有原盘、当前包、依赖、配置、存档、runs、原件与研究证据。

提交推送并核对HEAD/远端与干净状态后，继续已有5191换行策略的场景/上下文审计；只读建立候选队列，不把布局计数证明当语义批准，不改未知格式或为凑条数重复翻译。
