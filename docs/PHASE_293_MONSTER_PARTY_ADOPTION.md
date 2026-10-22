# 第293阶段：完整怪物名称族与队伍图集实际汉化

## 已采用范围 / Verified source and offline artifacts

UI_Monster_Name_Jpn全部199图、UI_Name_Jpn的Monster_Name117图，以及三NPC/五UI标题/三人名图集共11图，合计新增327图/342文字层；累计405图片组、434文字层、1800双盘真实别名（895/905）。这是两个明确名称族及关联标签的实际采用，不是UI_Name184全包已经结束。每个源namespace保留独立图片ID，即便像素相同也不按leaf混填。

新增目标1400：D1 697别名/148资源，D2 703/207，243资源并集。与旧28源只在MC2Game重叠，累计270源；纹理组件各171/228资源，独立组合/对照包各197/256资源。原盘355个disc/path成员重新hash；全部目标单mip、Format7、atlas可解析。无同路径源冲突；MC2Game交集6导出在既有Font底包原payload/tiled保持。误命中的FX_Pattern.Name（Format05/9mip）和North_crowd.North_01（12mip）明确排除，不拿未解码图假设相等。

## 译名与核字

逐张原图读数、INT/JPN采用字段与最终display-fix、既有图片术语或新可读原文译法均写入 locales/zh-Hans/candidate-decisions/monster-party-image-labels.json。新音译为草稿审读结果，不声称官方定名；保留KAN既有字段语义，不按英语变量猜名。Boss_Ch11_Melissa实际原图푸 르 손，采用普尔森，而非梅莉莎。

旧研究不覆盖，附独立勘误：27팔/칼纠正为修亚伦的手臂，67겔/젤区分格尔鱼与水母；132实际로얄가드，采用皇家卫兵，撤回错误守护者阿尔加特；120实际데스발리스타，中文死亡弩炮不变。新增“相同尺寸+RGBA原图须有一致原串与译文”回归门，捕获按错误读数自分组遗漏的两处冲突。四次核字纠正均落实到实际locale数据，不仅留研究日志。

## 布局和通用技术

原32源/128层/128导出/64包成员边界确实拒绝本轮完整资源族，因此有界扩展为512源、1024层、每包512导出、512包成员。显式增量纳入上限共用512包成员边界，刷新journal上限为512候选+3元数据，仍严格排除raw/config/save/runs和链接。16M文字层总像素、64MiB字体、单层尺寸、16区域/图、输入hash、预期payload/tiles、对象唯一性及非选导出/原块保持均不放宽；512/513与1024/1025边界有自写fixture测试。不是只改两个独立包而漏地图resident。

通用align支持left/center/right，默认实际ink居中公式与旧版本逐字节一致。小名称与图集按原左锚点绘制，非全体强制居中；171无盘提示和12张Boss大标题保持原居中。12标题逐图保留两侧翼饰，137/155/180保留左侧32像素原花饰；NPC绿、红/白/灰队伍状态、完成率金色保留。源背景透明RGB不被误当不透明底。

175原行距25与BC3四像素格不一致：采用不重叠授权mask，检查每行新字形及stroke落在名义25像素行内，细小模糊阴影仍限制在各自授权mask；此为原图坐标与glyph证明，不冒称已恢复runtime DrawTile UV。右侧空白和174未选区域有独立crop hash。最终blend/采样/动态加载与实际UI验收仍需游戏测试，当前不启动游戏。

327源图均按实际BC3编码再解码审看，修正了初稿NPC色彩、132错名、标题花饰和171对齐；旧78组实际RGBA保持。phase292菜单source_text_sha元数据改为真实可见源串而非leaf，不改旧图像素。

## 可复现构建与原件恢复

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-293-verification/disc1-texture-bundle
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-293-verification/disc2-texture-bundle
```

首次构建换全新--output-dir。原件按第290阶段清单配方从匹配原镜像精确提取270个选中资源，已存在文件hash必须匹配，不覆盖；不能复制完整游戏或生成ISO。字体仍按既有固定Font流程生成，MC2Game叠加Font底包，其余叠加原件。完整游戏资源/字体/PNG及构建输出不入Git。来源调查的结构证据见配套命名空间文档。

## 收尾与后续

基线/隔离旧源码1868测试，修改与清洁源码1889测试；每个包非选导出、区域外BC3块、padding、输入hash和七Font/14159 INT/315字幕保持。旧50资源检查点和270纹理资源/旧源码均在隔离副本回滚，当前保留新405图。现有D1测试根显式增加147原资源，刷新147候选+MC2Game+TOC和三元数据共152文件；保留原件、配置、存档、runs，不生成ISO/整盘副本。完整命令/输入/输出/exit与远端身份在build/phase-293-verification/VERIFICATION.txt。

仍待：UI_Name其余菜单/技能atlas、其他UI/教程、原扫描111项覆盖缺口、不同名/动态加载路径及原生可见硬编码，未知UI/성쇄只凭新证据推进。整游戏汉化与游戏验收仍未完成，不以本轮离线数量代替最终完成率。
