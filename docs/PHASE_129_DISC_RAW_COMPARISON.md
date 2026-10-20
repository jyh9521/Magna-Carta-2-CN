# 第129阶段：分盘原文raw对照与只读检查适配

2026-10-20。开始核对HEAD 620118b、干净工作区、BUILDING收尾及workflow最后批次116。本阶段不新增译文：14,082 INT、315字幕仍draft，1104术语仍candidate。

## Verified：源派生raw阶段

新增tools.build_locale_comparison与locales/zh-Hans/locale-comparisons/disc1.json、disc2.json。计划hash锁定128合成计划及manifest，先完整独立重放累计INT/字体/本盘字幕、像素、控制与TOC。原128输出及组件不修改，也不把新包伪装成旧font-route kind。

只从本盘controls派生raw-controls：显式四字体包中三个LZX包用既有decompress_copy解压并清标记；一个原非外层压缩包逐字节不变。解压器复核对象表和logical payload；四个raw字体又逐字节核对125已锁原文raw组件。INT与所有字幕保持本盘原文，绝不对中文候选包做解压当原文对照。

raw TOC从各盘原表只合并三项解压size差异；精确逆更新、零自引用与未知字段保持。盘一raw TOC197989→197991，盘二199817→199819；它们各自hash不同，不能跨盘复用。中文candidate沿用128统一TOC，未取任何局部TOC覆盖。每盘仍27/29项局部资源，不生成整盘目录或ISO。

每项raw-controls经restore_copy在另一文件实际写入raw候选再恢复controls，生成raw-rollback-check；两盘共56项字节回滚。原candidate/controls/rollback-check与128逐文件相同，主raw/candidate保留。独立verify再次从源controls派生raw、重放128合成并比较精确树/字节，不把manifest hash存在当作重放。

## 新kind与旧门禁

新manifest kind=offline-disc-locale-raw-comparison，显式raw_package_outputs、disc1/2、上游manifest及比较计划canonical SHA、raw_control_method；资源行另含raw_sha256/raw_size。verify_resource_phase只读检查器显式接受此kind并验证新合同，raw phase还核对资源行hash和严格整数size；保留manifest hash、重复键/路径、32资源上限、稳定快照及原候选/controls合同。

旧offline-font-route-probe路径和raw规则兼容，未适配的offline-disc-locale-composition仍拒绝。新kind只代表字节检查格式，报告game_started/resource_writes_performed/deployment_performed/game_rendering_verified仍false。TAB原保留、literal coverage=false、5191旧显式换行策略均继承，未新增语义批准或换行重排。

## 现有玩家目录：只读兼容预检

旧十项raw（含原文INT、旧字幕和TOC）与新第一盘raw逐字节相同。新增17份字幕在现有candidate和raw-controls两根都匹配本盘原文SHA，可供后续显式登记；本阶段未登记、未刷新入口/PREPARED或资源。

旧refresh_oneclick_probe同资源集合检查不改，仍拒绝10→27隐式扩展。下一阶段实现有界、源hash锁定的登记/增量刷新事务，测试失败回滚、配置/XEX/runs/存档保持，再处理现有第一盘测试根。第二盘只保留局部离线包，不新建整盘副本。离线成功不是游戏验收。

## 复现

先按128文档复现已hash锁定组件。输出目录必须新建，与组件互不包含：

```powershell
python -m tools.build_locale_comparison --plan locales/zh-Hans/locale-comparisons/disc1.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/locale-comparison-disc1
python -m tools.build_locale_comparison --plan locales/zh-Hans/locale-comparisons/disc1.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/locale-comparison-disc1
python -m tools.build_locale_comparison --plan locales/zh-Hans/locale-comparisons/disc2.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/locale-comparison-disc2
python -m tools.build_locale_comparison --plan locales/zh-Hans/locale-comparisons/disc2.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/locale-comparison-disc2
python -m tools.verify_resource_phase --packet-root build/locale-comparison-disc1 --manifest-sha256 <manifest-SHA256> --resource-root build/locale-comparison-disc1/raw-controls --phase raw-controls --output build/disc1-raw-report.json
python -m unittest discover -s tests -p test_locale_comparison.py -q
python -m unittest discover -s tests -q
```

## 验证与清理

基线1562、新增13项后修改/干净索引源码1575均OK(skipped=1)。新增自造包检查原文保持、解压payload与TOC逆、坏包、角色/越界/别名/数量拒绝；新kind三阶段只读、原kind兼容、未适配kind拒绝、错raw行/hash/size/盘/状态拒绝。

双盘真实构建及独立重放、六次三阶段字节检查、56项新raw回滚通过。源hash、双盘回填/旧译与未改值、164工作区复现、24held分类、当前64入口依赖、配置/XEX、旧候选/raw检查及原组件身份保持。仅清理核实可再生的隔离索引源码pyc；保留原盘、所有所需组件、局部包、控制、回滚和研究证据。

四件证据保存在build/phase-129-verification：修改副本为verify_resource_phase；基线自造新kind报unsupported packet manifest(exit2)，新只读raw检查2/2(exit0)，隔离hash保护回滚exit0并恢复旧拒绝exit2，主修改保留。精确命令/字面输出见VERIFICATION.txt。源码、计划与文档验证清理推送后，核对HEAD/远端和干净状态，接续登记事务。
