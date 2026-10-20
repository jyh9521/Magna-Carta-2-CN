# 第122阶段：受保护的显式双轴atlas扩展

2026-10-20，接续121容量门禁。无新增翻译/批次：INT14,082 draft、1104 candidate、44字幕315cue和最后批次116保持。仅推进离线字体技术，不刷新旧测试目录。

## 实现与保留合同

supplement_font计划增加可选atlas_width：整数二次幂128..2048，禁止缩小/无增长/多mip，必须显式raw_atlas。未指定width仍走原grow_atlas；指定相同width仅增高也产生与旧路径相同包字节，不自动改变准备器的选择策略。
宽变化会改变Xenos tiled地址，不能像仅增高一样追加零字节。grow_atlas_axes复用ue3_textures已有UEViewer派生块地址函数，把旧对齐矩形的16字节BC3块逐块搬至新地址（包括padding）；不解压重编码旧BC3。检查地址范围/重复目标，原解码RGBA矩形按新stride裁回后逐字节相等。旧块物理位置不同，不能声称新载荷原前缀不变。
同时更新tagged SizeX/SizeY、native mip宽高、raw bulk count/size，重解析及载荷比较；调用方后续仍验证原字形tagged/native记录、未选择remap、旧字形像素、非选单元像素和无关export/源逻辑范围。报告明确original_tiled_bytes_retained=false、original_block_values_relocated=true与original_decoded_rectangle_identical=true。
无glyph_limit上限放宽，无多atlas序列化，无控制/布局栅格规则放宽。U+3000和U+0009仍按121门禁保持。

## 三族真实源探针与几何

locales/zh-Hans/axis-growth-probes/glyphs-0/1/2.json各仅一个原基线缺少的汉字，使用已锁Noto字体栅格与既有字距/度量选项；raw atlas显式2048x2048。原三族plan/source/semantic/Noto hash均沿用既有声明，源包未变。
三个选定源字体包各完成单字append-only输出与重解码，原像素/字形记录/未选remap/无关export保持，输出仅在build/phase-122-verification/font-0/1/2.xxx及报告。SmallFont仍按既有显式identity-256转换，runtime_equivalence未验证；不是任意直索引模式可改。
用同三族原font、当前模板和2048x2048几何只读allocate，全体可绘制2389/2388/2389位置可以分配。但这只是几何可行，不是已生成这些字形；现有单计划glyph_limit仍2048，布局映射、累计覆盖、alpha/atlas与7别名路由/游戏显示均还有各自门禁。

## 复现入口

三个探针可使用现有CLI，不依赖新私有构建器：

```powershell
python -m tools.supplement_font build/poc-game/disc1/MC2Game/CookedXenon/font.xxx --package-sha256 b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6 --font-file build/font-source/NotoSansCJKsc-Regular.otf --font-sha256 2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b --font-object General_15 --plan locales/zh-Hans/axis-growth-probes/glyphs-0.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --raw-atlas --output build/phase-122-verification/rebuilt-font-0.xxx --report build/phase-122-verification/rebuilt-font-0.json
python -m unittest discover -s tests -p test_atlas_axis_growth.py -q
python -m unittest discover -s tests -q
```

其余源/object/hash取原readability-fonts/font-1/2.json首个source，glyphs-1/2对应；输出必须新建。测试合成包完整保留，不提交原包/字库/atlas资产。复用tile公式的上游NOTICE/许可保持，不将其称为本阶段新发现。

## 验证与收尾

基线1484测试，11项新source-free测试后修改与索引导出干净源码1495测试均OK(skipped=1)。覆盖单轴/双轴、压缩原atlas、tagged/native/bulk一致、精确块/padding搬移、坏宽度/bool/缩小/隐式raw拒绝、旧高度路径包字节一致、确定性与原输入保持。初次合成直接传serial_offset=0触发严格bulk offset错误，已改测试绑定真实export位置，没有放宽生产检查。
同一128x128合成源、新glyph位于旧宽之外：旧代码exit2（cell outside atlas），新代码exit0（256x256、旧像素/记录保持）。独立副本回滚旧writer hash并重跑复现旧exit2，主MODIFIED_FILE.py保留新功能；可执行ROLLBACK.sh、错hash拒写及DIFF_FILE.json/VERIFICATION.txt在build/phase-122-verification，含精确命令/输入/字面结果/退出状态。
八源hash/24分类、64当前包依赖/配置/XEX、candidate/raw各10资源保持；全部18176值/14082旧译、历史held、workflow/terms/subtitle-profile不变；164文件复现与116工作区逐字节一致。仅清理绝对路径核实的隔离干净源码可再生成pyc，保留原盘/配置/存档/runs/当前包/依赖/真实探针/基线回滚研究。无ISO/整盘副本/模拟器或游戏资源刷新。
下一阶段继续独立新增字计数与显式布局方案；不把单字探针当累计字库、不把几何成功当游戏验收。全套离线覆盖/像素/TOC/独立回滚通过后才按既有hash保护增量刷新。验证清理推送核对后自动接续。
