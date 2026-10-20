# 第124阶段：显式空白advance与累计ink核对

2026-10-20，先核对HEAD a94deaa、远端相同与干净状态，接续123。无新增翻译，最后批次116、14,082 INT draft、1104 candidate及315字幕保持。

## 显式合同

通用supplement计划glyph新增可选layout=blank-advance：必须为BMP Unicode Zs separator，提供正整数metric_width且不超过cell宽；禁控制字符、TAB、换行、Zl/Zp、可见字、未知layout值、已有映射替换和remap别名。普通glyph没有layout时继续拒绝空白。保留block对齐、重叠、atlas/metric、源hash、u16、旧记录/像素和alpha长度检查。

rasterize_plan验证原字体hash，显式blank不调用draw、不要求该separator的字体cmap、不伪造ink，生成全零alpha并返回raster_kind=explicit-blank-advance和空bbox。普通glyph仍走原cmap/ink/共享baseline逻辑。writer拒绝任意非零blank alpha；BC3重解码后整个cell alpha必须严格为0，不能使用普通alpha误差18放过微弱可见墨迹。report单列explicit_layout_glyphs及decoded_alpha_zero，不把空白说成有ink。

## 三族源链与结果

输入是123阶段三族累计drawable输出，逐个与已提交drawable-demand-probes/manifest.json的output_sha256核对；source原包/Noto/plan链可按123文档复建。新layout-advance-probes/manifest.json锁定前一manifest和三个输入/计划/输出身份，不复制整盘，不修改原资源。

U+3000候选width分别27/20/32，显式采用当前字号+5的宽字符候选advance，不推断引擎空白语义、不盲借ASCII SPACE宽9/5/13。独立first-fit cell与旧记录无重叠；原4997/2644/3648条增至4998/2645/3649。三包旧remap/tagged/native记录、旧像素与非选单元/无关exports保持，新blank alpha误差0且完整cell透明；没有新增字距人工定稿或游戏验收。

重新读取所有hash锁定的14,082 INT及315字幕计划，累计2451码点。在这三个选定字体的候选包里missing-remap均0；2448个非空白非控制字形逐个解码查ink，均有可见alpha。SPACE和U+3000以布局身份分开，TAB原值/原映射不变。三族原TAB矩形可见像素0/36/0，而SPACE均0；原始结构/像素事实不等于TAB渲染行为，SmallFont36像素尤其禁止据此统一别名或清零。观察元数据见layout-advance-probes/original-layout-observations.json。

首次派生SmallFont候选计划误继承原identity-256转换选项，生产检查拒绝已转换字体再次转换。已从新派生计划删除该一次性转换选项，保留失败日志，未改转换守卫。普通prepare仍提前报告缺少显式layout方案，不自动扩大空白允许范围或自动合并这些探针。

## 复现

先按123文档生成其三个累计drawable输入，确保其output_sha256与前一manifest逐个匹配，再执行（输出须新建）：

```powershell
$e = (Get-Content locales/zh-Hans/layout-advance-probes/manifest.json -Raw | ConvertFrom-Json).fonts[0]
python -m tools.supplement_font $e.input_path --package-sha256 $e.input_sha256 --font-file build/font-source/NotoSansCJKsc-Regular.otf --font-sha256 $e.font_source_sha256 --font-object $e.font_object --plan $e.plan --lzx-library build/lzx/native-verified/ue3_lzx.dll --raw-atlas --output build/phase-124-verification/rebuilt-font-0.xxx --report build/phase-124-verification/rebuilt-font-0.json
python -m unittest discover -s tests -p test_blank_advance.py -q
python -m unittest discover -s tests -q
```

fonts[1]/[2]对应其他两族。输入目录只是有hash的可再生字体派生包，不是隐含原游戏依赖；没有完整原资产提交Git。

## 验证、收尾、接续

基线1504，新增14项后修改及索引导出干净源码1518项均OK(skipped=1)。覆盖Zs限定、正宽/上界、普通空白仍拒绝、控制/行分隔/BMP外/未知类型、已有remap替换、非零alpha与坏长度、原像素/记录保持、无draw/无空白cmap需求、两种metric高、混合普通/blank记录和overlap拒绝。

同一U+3000/metric_width22/alpha0合成包，旧writer拒绝unsupported glyph plan fields、exit2；新writer独立记录/透明cell通过、exit0。隔离副本hash保护回滚恢复旧layout拒绝、exit0，重跑旧行为exit2；主MODIFIED_FILE.py保留显式blank实现。四件证据及精确命令/输入/字面输出/状态见build/phase-124-verification/VERIFICATION.txt，错hash回滚拒写。

双盘源hash/18176值/14082旧译、24剩余分类、八源hash、164文件复现、64当前包依赖/配置/XEX与candidate/raw资源核查均保持，workflow/terms/subtitle-profile不变。只清理核实绝对路径的隔离干净源码pyc，保留原盘、配置、存档、runs、现有包、派生字库和基线/回滚/研究。无ISO/整盘副本/模拟器启动、无测试包/TOC刷新。

只完成选定三族的离线累计remap/ink/blank条件，不是全部七别名及路线重建/TOC逆变换、完整资源包独立回滚或运行验收。验证清理提交推送、远端与干净核对后继续这些门禁，不把本阶段作为翻译项目结束。
