# 第295阶段：战斗、教程文字图与有界packed BC纹理回填

## Verified / 采用范围

本轮采用46个独立图片组、139层（138语言层及1个派生mask），覆盖92个双盘真实别名。累计507组、847层、2096别名（D1/D2为1043/1053），源包并集276；纹理组件176/233资源，对照包201/260资源。INT仍14159/batch121、七个Font和315字幕。本轮没有新INT草稿。46组包括43张UI_Battle实际候选及3个独立Tutorial标题；MAX119按HUD惯例保留，并非技术控制码。保留MAX的2个别名不计入新增回填92个。

每个别名锁定disc、完整resource路径、对象身份、原文件、payload、tiled hash和尺寸。Tutorial_01/32与Tutorial_02/27虽然RGBA相同，namespace/GUID不同，分别保留；不能用像素相同推断身份相同。既有461组逐项像素保持。

## 源图审看与修正

已有INT/JPN同字段仅作明确关联证据，不能按leaf或同key盲填。任せて!的同key曾指向长篇试炼段落；此处按实际通讯句译为交给我。原图61两句待て/待って均为灰色（主色RGB181/178/181），不按初始肉眼误判改黑。

实际编码后逐图对照发现160的特效图最后一行是『氷の媒質』破壊，和156普通图的足蹴り不同。冻结研究误将二者同排复制；正式采用独立纠正源读法、source-text hash及译文为破坏冰之媒质，普通156仍踢击。不能让自动测试证明了错误的映射后就直接采用。

保留87战败红描边；135序言第一物理行采用兰兹海姆南北两大势力的内战，避免长句缩为小字。172将完整句重新分为需要塞蕾丝汀的 / “冰之大炼换阵” / 才行。所有文字保留原图尺寸、逻辑矩形和锚点；显式减少纵向留白并去除小灰字模糊投影，提高通讯和剧情字图可读性。四张16px高反馈词使用10px字体与ink_padding{x:4,y:1}，不采用旧font4候选。

## 通用实现及来源

`tools/texture_layout.py`提供显式opt-in的xbox-inline-bc-v1单mip格式5(BC1)/7(BC3)读写。格式、power-of-two逻辑尺寸、128px对齐物理分配、独立inline SourceArt、bulk flags/count/size/绝对指针、native尺寸和export结尾均严格验证。最短边≤16的首层packed origin按长宽为(0,4)或(4,0)个4px块，不把逻辑64×16误改成128×32。只改授权块，padding和保护块保持。

来源为Xenia固定commit28b69c21的GetPackedMipOffset（Ben Vanik，BSD-3-Clause）与既有UEViewer tiled寻址/格式证据；作者、固定路径/hash与许可证见NOTICE.md、references/texture-layout-research.lock.json及licenses/。没有提交完整上游代码或游戏资源。111个历史格式失败项/121逻辑mip的完整研究只支持研究结论；本轮生产模块只启用已采用的单mip BC1/BC3子集，不宣称已支持多mip/Format2/外置TFC。

109为alpha全255的BC1灰度RGB图，必须显式opaque-luma；它使用与108相同文字alpha转为灰度RGB，非RGBA透明平面。原START控制器图标与外围块/crop hash保持。双图已编码、重开及独立像素验证，但shader真实消费者和游戏内UV裁剪仍未验证，不声称离线等于实际游戏验收。

默认旧BC3路径、默认4px留白与所有旧图片像素保持。可选ink_padding只接受0..16整数x/y，墨迹/描边仍需真实装入矩形；不是取消fit守卫。其他32编辑区域/16保护区域/1024层等边界保持。

## 复现与收尾

按纹理计划hash锁定original引用，从用户原盘仅提取缺失资源；保留Font底包链。首次用全新output-dir，复核用verify-root，不覆盖旧检查点：

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-295-verification/disc1-texture-bundle
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-295-verification/disc2-texture-bundle
```

本轮验证档位为基线1904、修改/清洁源码1932、隔离旧源码1904测试。完整实际结果/命令/输入/字面输出/退出状态保存在build/phase-295-verification/VERIFICATION.txt；276旧本地化或原件检查点和旧461/708计划保留，可隔离恢复。旧模块恢复、新模块仅在隔离copy移除；当前507组不回退。现有测试目录显式纳入3个Tutorial原成员再增量刷新；不启动游戏，不制作ISO或整盘副本，保留配置/存档/runs。

## 尚未完成

继续字体表之外的credits职务/配音角色及品牌职务语言标签、未采用格式资源、全量资产覆盖、未知原生UI及未知术语裁决。游戏实际显示、shader/UV、动态字符串与完整双盘流程仍由用户最终验收。此阶段完成不等于全部汉化完成。

完整字体cmap逐层重新加载会反复建立TTFont/CFF对象图；三个冷重放并发及随后未缓存的单独重试曾触发Windows MemoryError，均在输出发布前失败。失败日志保留，先串行复测，缓存修复后按实测内存余量最多并行两条冷重放，并将glyph检查的不可变码点集按完整字体bytes有界缓存1份；字体变化必重验，仍不缓存绘制结果。三项缓存测试、847层真实渲染（1次cmap解析/846次命中，139新增层hash保持）及旧461组实际重放检查语义/字节保持。
