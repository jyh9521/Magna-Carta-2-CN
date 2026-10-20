# 第121阶段：源字库需求分类与提前布局门禁

2026-10-20，接续120覆盖缺口。无新增翻译batch/改译：INT14,082 draft、1104 candidate、44字幕315cue及workflow最后116保持。

## 源基线实测

沿既有readability-fonts/route.json与三族font plan的源hash/semantic hash，读原始poc-game字体包、现有LZX库和hash匹配OTF；只读解码/指纹/remap/alpha统计，不栅格化、不输出游戏包。总需求仍2451码点，不能拿已补字测试包的1616缺口当从原始基线开始的新增数。
General_15：源缺2389、已映射透明183修复1，新增集合2390；Subtitle：源缺2385、已映射透明183/8212/8230/65311/65324修复5，集合2390。两族各含未映射U+3000布局需求，因此可绘制2389。
SmallFont为256字形非remapped模式，按现有identity conversion合同计算新增2389，含U+3000一项，可绘制2388。初探把空remap当零映射的结果不作为正式计数，保留在本地证据中并注明；typed-source-demand.json与公开font-expansion-readiness.json才是本阶段正式模型。没有宣称任意non-remapped字体都遵从此模型。
U+0009原值保留，当前覆盖审计仍标未核控制字面量；本阶段不删它、不把它转换为可见字。SPACE/U+3000等需求不从集合消失；未映射布局项需要显式方案，不能交普通可见字形栅格器猜测。

## 数量与atlas容量是独立门禁

三族可绘制新增2389/2388/2389均超过现有单计划glyph_limit2048。另按现有模板调用allocate进行只读分配试验，原宽保持、仅将高度候选设2048，三族均insufficient unused atlas cells：General原512x64、格28x28；Small原256x256、格20x20；Subtitle原512x512、格32x32。没有生成或提交失败中间字库；这是现有工具/布局方案不足，不是Xbox/引擎全局上限结论。

## 可复用修正

prepare_text_sample新增classify_font_demand(font, codepoints, transparent=())：严格Unicode scalar检查，识别显式remap与既有256-glyph identity conversion；透明修复必须属于已请求/已映射集合。报告保留requested/missing/transparent/required，分别给drawable/layout_or_control/outside_bmp，不归一化或丢需求。
普通prepare在布局/控制新增时提前给出显式映射门禁，BMP外也单列；无此问题的旧有效路径仍沿用原数量/atlas/像素合同。没有放宽glyph_limit、atlas高度、栅格器或控制字符限制，没有语言专用硬编码。
本地prepare_check.py基线与修改均使用累计hash计划及44字幕计划、原始route/source/Noto、glyph_limit2048与既有字距选项：

```powershell
python build/phase-121-verification/prepare_check.py baseline
python build/phase-121-verification/prepare_check.py modified
```

基线exit2：sample must require 1..2048 additional glyphs；修改exit2：sample needs explicit layout/control mappings: U+3000。两个结果都是预期生成门禁，均不创建尝试目录；不是已生成累计字体或已解决字库缺口。classify_font_demand与现有context/select_font/fingerprint/parse_font_payload/ink_records/allocate按上述锁定三族源可复核计数/容量，正式报告保留源定位/hash/尺寸及集合，本地证据不含对原包的修改。

## 验证与回滚

基线1476测试，新增8项source-free需求分类合同，修改及索引导出干净源码1484测试均OK(skipped=1)。合成合同覆盖原值/输入保持、256转换、未知non-remapped拒绝、布局控制保留、透明去重、BMP外单列、无效scalar/bool拒绝和总需求/新增数区分。
八源hash/24余项分类、64项当前测试包依赖/配置/XEX及candidate/raw各10资源保持；全部18176值/14082旧译、历史held、workflow/terms/subtitle-profile不变；164文件复现与116工作区逐字节相同。
独立准备器副本回滚恢复旧代码hash，并重跑复现旧数量exit2；主MODIFIED_FILE.py保留新提前布局门禁。可执行ROLLBACK.sh、错误hash拒写及MODIFIED_FILE.py/DIFF_FILE.json/VERIFICATION.txt在build/phase-121-verification，记录精确命令/输入/字面输出/退出状态。只清理绝对路径核实的隔离干净源码可再生成pyc，保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。
下一阶段设计受保护的通用容量扩展及显式布局映射，先核对grow_atlas/tile/原像素保持与序列化边界，再决定双轴扩展或多atlas，不简单提数字绕门禁。未经完整离线/回滚验证不刷新现有测试目录，不新造ISO/整盘副本、不启动模拟器；离线成功仍非游戏验收。验证清理推送核对后自动接续。
