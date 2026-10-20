# 第123阶段：累计可绘制字形与显式计数上限

2026-10-20，接续122双轴扩展。源hash、HEAD和干净工作区已先核对；本阶段属于字库工程，不伪造翻译批次。最后翻译批次116、14,082 INT draft、1104 candidate、315字幕均保持。

## 修改

supplement_font.MAX_ADDITIONAL_GLYPHS=4096，计划仍默认128，仅显式glyph_limit可提高。prepare_text_sample复用同一常量，避免两个验证入口漂移。4096是受控工具计数上限，不是引擎容量结论；仍逐项核查BMP/非控制非空白、重复、glyph数、BC3位置/重叠、字体cmap、alpha、remap、原记录/像素与源hash。prepare的自动几何策略仍只增高，未静默启用增宽。

## 真实源离线结果

从workflow每个hash锁定plan的14,082项与subtitle-profile的315项重新收集2451码点，与原三族语义及透明修复集合核对。drawable-demand-probes/glyphs-0/1/2.json列出的2389/2388/2389项与分类结果逐个相等；U+3000不混入这些普通字形，U+0009保持原映射。新计划显式2048x2048、glyph_limit4096，保持既有字号、宽字advance=字号+5及左2/右3留白。

三个源包均hash核对，重建包及逐字栅格报告在build/phase-123-verification/font-0/1/2.xxx、对应-report.json。原2608/256/1259条记录保留，候选4997/2644/3648；透明修复1/0/5个旧remap明确转向新字形，因此不是“全部旧remap不变”。其余remap与所有旧字形记录、旧矩形像素、非选单元像素/块/padding、无关exports保持。三个输出最大BC3 alpha误差均18；rasterization_quality_verified和runtime_rendering_verified仍false，不以数值误差界替代视觉验收。

仅选定三族源包已生成，不是七别名完整路由。U+3000布局、SmallFont identity256运行等价、全体别名语义/ink、TOC、完整独立回滚及游戏验收仍待完成；测试目录和入口仍是旧262条。manifest记录源/plan/output/Noto身份及未完成状态，原包、字体、atlas不入Git。

## 复现

现有通用CLI直接读取提交的结构化计划，不依赖临时生成脚本：

```powershell
python -m tools.supplement_font build/poc-game/disc1/MC2Game/CookedXenon/font.xxx --package-sha256 b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6 --font-file build/font-source/NotoSansCJKsc-Regular.otf --font-sha256 2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b --font-object General_15 --plan locales/zh-Hans/drawable-demand-probes/glyphs-0.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --raw-atlas --output build/phase-123-verification/rebuilt-font-0.xxx --report build/phase-123-verification/rebuilt-font-0.json
python -m unittest discover -s tests -p test_glyph_count_optin.py -q
python -m unittest discover -s tests -q
```

其余两族source/object/hash从drawable-demand-probes/manifest.json取，Noto身份相同。输出须新建，保留盘别来源；本阶段不刷新或合并双盘。

## 验证与接续

基线1495测试；新增9项后修改/索引导出干净源码1504测试均OK(skipped=1)。首次全套测试发现旧opening测试仍把2049视为非法；同步边界到4097后重新全套，保留初次失败日志，未削弱任何几何或布局检查。默认128、2048/2049/2388/2389/4096边界、4097/坏类型/重复、布局/控制/BMP外、重叠拒绝和prepare入口一致均有回归。

同一2389条合成计划显式glyph_limit4096：旧writer返回ERROR: glyph_limit must be within 1..2048 / exit2，新writer接受 / exit0。独立副本hash保护回滚恢复旧2048门禁 / exit0，重跑旧拒绝 / exit2；主MODIFIED_FILE.py保留4096。四件证据及精确命令/输入/字面输出/退出状态见build/phase-123-verification/VERIFICATION.txt，错hash回滚拒写。

八源hash、24剩余分类、双盘18176值与旧译、164文件工作区复现、64当前包依赖/配置/XEX及candidate/raw只读核对；workflow/terms/subtitle-profile保持。只清理核实绝对路径的隔离干净源码pyc；保留原盘/配置/存档/runs/现有包、当前候选字体与基线/回滚/研究。无ISO/整盘副本/模拟器启动。验证清理提交推送、核对远端与干净后，自动接续显式布局方案与字体ink/别名路由，离线成功不等于游戏验收。
