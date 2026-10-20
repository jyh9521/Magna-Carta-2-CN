# 第125阶段：累计字体七别名、共享包与TOC离线合成

2026-10-20，先核对HEAD c8ace83、远端一致、干净工作区、每轮收尾约定和最后翻译批次116。无新增翻译，仍14,082 INT draft、1104 candidate及315字幕；本阶段不虚增翻译批次。

## 计划与语义

locales/zh-Hans/cumulative-font-route/glyphs-0/1/2.json精确组合123的drawable records与124的独立blank record：新增2390/2389/2390。drawable顺序、坐标/metric、字号/ink padding、宽字advance、原透明字修复集合逐项保持；空白只有最后U+3000，TAB不新增/不重写。不是从旧prototype直接把glyph_limit增大冒充补字。

font-0/1/2.json保留原三族来源、GUID、canonical identity、原semantic及TOC hash，分别覆盖General_15三别名、SmallFont两别名、Subtitle两别名。新expected_supplement_semantic_sha256来自已hash核对的124候选完整字形/remap及所有atlas tiled内容。route.json只更新三个font_plans引用，保留raw_packages=true、verify_glyph_ink=true以及原262条text_plan和四个独立字幕计划。scope.json明确区分“字体按全部需求生成”和“累计译文已回填”。

沿用现有tools.build_font_route_probe，不修改通用基础设施。原始七别名source hash/semantic先只读核对；共享font.xxx/Startup_int.xxx按三族顺序编辑，最后再检查全部七个完整语义，防止后编辑覆盖先前字体。旧glyph records/未选remap、旧矩形像素、非选单元/块/padding与无关exports均保持；透明修复1/0/5是显式选中remap，不宣称所有旧remap不变。

## 离线输出与边界

build/phase-125-verification/route-probe只含四个字体包、Coalesced.int、四个字幕及TOC的局部资源，各有controls/candidate/rollback-check/raw-controls和manifest，不是整盘副本。builder核对TOC预期旧size、更新当前候选size，再反向恢复原TOC精确字节。十个资源的独立retained-original rollback-check逐字节等于controls；主candidate保持。

再次从所有hash锁定INT/字幕译文计划收集2451码点，对最终共享包中的每个字体核查：2450非控制映射通过、2448非空白字形有ink、U+3000候选宽27/20/32且解码alpha0。TAB仍由font_coverage返回control-or-format-literal-unverified；all_literal_coverage_verified=false，不改审计让它假绿。全部七别名的非控制字体需求通过，不等于字体选择、空白语义、SmallFont identity转换或视觉质量已经游戏验收。

路由候选的INT仅原262条，不是累计14,082条；字幕仅原四计划，不是全部44计划/315cue。既有resource role/额外字幕16上限、累计TAB控制门禁仍保持。当前测试入口/资源/TOC未刷新；下一阶段必须明确累计文本/独立字幕合成和控制字面量的源保护方案，不能仅凭字体离线成功投放。

## 复现

所有新计划均提交，原资产由用户提供，输出须新建：

```powershell
python -m tools.build_font_route_probe --plan locales/zh-Hans/cumulative-font-route/route.json --game-root build/poc-game/disc1 --project-root . --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/phase-125-verification/rebuilt-route
python -m tools.build_font_route_probe --plan locales/zh-Hans/cumulative-font-route/route.json --project-root . --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-125-verification/rebuilt-route
python -m unittest discover -s tests -p test_cumulative_font_route.py -q
python -m unittest discover -s tests -q
```

独立verify从输出controls重做全部字体、文本、TOC、raw-controls、rollback-check及manifest，逐文件重放相同，不依赖当前游戏目录已修改资源。不得把verify当启动模拟器或运行验收。

## 验证与收尾

基线1518测试，新增7个source-only计划合同测试后修改/索引导出干净源码1525均OK(skipped=1)。覆盖refs hash、完整drawable/blank记录复用、七源原绑定/TOC保持、文本scope262/四字幕不变、控制字不新增、候选semantic显式更新与workflow/source链锁定。

同一123/124累计新增需求，旧route plan缺完整新增集合而exit2，新route plan七别名完整且保持旧262文本scope而exit0。独立副本hash保护回滚恢复旧sample-font route、exit0，重新累计检查恢复exit2；主MODIFIED_FILE.json保留新route。另完整十资源rollback和独立重放通过。四件证据及精确命令/输入/字面输出/退出状态见build/phase-125-verification/VERIFICATION.txt，错hash回滚拒写。

八源/双盘INT hash、18176源值与旧译保持，24剩余分类、164文件工作区复现、64当前入口依赖/配置/XEX、candidate/raw只读核查保持；workflow/terms/subtitle-profile不变。仅清理核实绝对路径的隔离干净源码可再生成pyc；保留原盘、配置、存档、runs、当前包/依赖及本阶段局部候选/源控制/回滚/研究。无ISO/整盘副本/模拟器启动或现有目录增量刷新。

验证清理提交推送、远端相同及工作区干净后自动接续累计文本/TAB源保护/字幕44计划的合成预备，不以本次提交作为汉化完成。
