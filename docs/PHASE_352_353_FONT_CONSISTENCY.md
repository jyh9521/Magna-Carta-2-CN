# 阶段352–353：数字字高与怪物名称字体

本轮承接阶段351的资源，处理用户追加的两张预览反馈，不撤回菜单残留、选项左对齐、译名和句末标点修订。

## Verified：数字不是只缺少位移

旧技能数字实际绑定 `font_ui.NormalNumber`，不是朱雀：字芯14–15px，汉字19–21px。
同一个 WhiteNumber 样式有379个显式字符串消费者，直接放大共享字库会波及HP、等级、数量等固定槽，因此保留该样式和旧数字字库。

- 使用用户提供的霞鹜臻楷 Slab GB v0.827 数字轮廓，源SHA256 `bf4ea8c39b51784469020120125715d3075137233fe337b5d0a7327f9dfc03bd`。
- General_15 的三个物理字体副本统一0–9及全角１，共33个映射；数字采用显式20px字芯目标、25px字格、13px半角advance，保留2px右边距和1px黑色投影。BC3解码后的可见字芯19–20px；“1”和“10”均20px。
- 只有Selected/X_0..X_3五个KAN消费者增加 `TextStyleCustomization.DrawFont` 与 `bOverrideDrawFont`，绑定已驻留的General_15。名字继续使用朱雀，其他WhiteNumber消费者、字号样式及旧数字atlas不变。
- 五个Skill父节点X由208改201；五个KanNum的Y由-5改-3.5。数字X=203、宽26及右对齐不变。`Default__UILabel`实际继承高度40，参与垂直字芯计算，不拿预览摆放代替序列化几何。
- 119技能名、620消耗实例、0..10数值域、5槽，6545组合全部通过；原生间隙4–18px。数字右字芯227（7的抗锯齿边界相差1px），与下方反击对齐；字芯上下缘相对误差最多2px，容纳不同汉字19–21px的实际外框。

General_15中其他文本引用的这11个数字也随同获得统一字高；三个副本字形一致，advance不比原来更宽，行高不变。全部非选中字形指标/纹理块及其他字体保持。数字值、文本、控制码均未修改。

`set_ui_font_overrides`仅追加选中renderer payload并修改其导出串行偏移/长度；无新增名称、导入、导出或共享样式。旧payload保留，逆变换还原原字节。追加后必须使用既有runtime normalization补齐32768字节边界，再进入增量组合。

## Verified：原图有两类，而不是所有图片都同一字体

逐张检查两份原始名字纹理的307个名字区域：295个普通怪物名/小型首领名使用一致的黑体字形处理；12个大型首领标题本来就是另一种宋体风格。纹理不包含原始字体文件名称，不能据此断言具体商业字体身份。

- 295个小型名称统一Noto Sans CJK SC Bold；213个需要字体/效果数据修订，82个已有同一配置；12个大型标题另保留字体并校正黑描边和黑投影。
- 范围按实际对象族定义，含Monster_Name、Boss_Name、North_Name、Object_Name、Senti_Name及Boss_Name_Big，不漏掉截图中的暗黑特雷瓦及其头领；友方Battle_Npc不是本次敌方名称族。
- 第一段修订覆盖178条资源路径、538个物理别名。完整家族842个别名连同此前改名的其余7个窗口一起核验，共849个窗口。通用构建器的单资源纹理上限有界扩至256，当前最大190，257拒绝发布。
- 全家族原生检查继续检出23个配置已一致的名称仍有96个旧栅格副本不匹配，分布在58条资源路径。第二段 `monster-font-native-reconcile-v26.json` 单独按哈希锁定修复这些窗口，文本/字体配置不变。不能以JSON选中了相同字体替代真实纹理验收；第一次整合的96处失败报告保留，最终须达到849窗口零失败。
- 两段合计实际重建248个名称区域、634个物理别名，覆盖203条资源路径；其余名称窗口由完整原生合同核验保持。双盘资源总数仍为442/543，含数字和TOC的最终增量分别114/175项；2个DLC及文本文件保持阶段351身份。
- 保留每张原图测得的独立渐变、位置、字高及字距；按原小型名称保留黑描边和偏移黑投影，去掉误套的橙色光晕。大标题保留字体、颜色、花饰与布局，原图的黑描边和黑投影单独恢复，不改成小型名称的黑体。
- 遗留 `img_ui_name_jpn_96` 没有appearance定义；它与 `img_ui_monster_name_jpn_55` 原始tiled SHA256完全相同，复用同源的样式定义，不猜测颜色。
- 当前“克洛普斯”等已统一译名保持，不把字体修订回退为旧译名。剧情、字幕、战斗数值与其他图片不作修改。

## 重建入口

以阶段351候选为输入，依次执行：

1. `tools.build_font_reface`，计划 `dynamic-font-numerals-v25.json`；生成三个字体资源副本。
2. `tools.set_ui_font_overrides`，计划 `skill-number-font-binding-v25.json`；再用 `tools.patch_tagged_fields` 应用 `skill-number-fields-v25.json`。
3. 使用 `tools.normalize_runtime_comparison` 相同的raw envelope规范补齐追加payload的运行时包。
4. `tools.build_texture_alias_update`，计划 `texture-overlays/monster-font-alias-update-v26.json`；所有输入及供体依赖必须满足哈希。
5. 合成第一段候选后，再用相同工具应用 `texture-overlays/monster-font-native-reconcile-v26.json`；其输入锁定第一段实际资源，不应用到更早的资源上。
6. 用 `tools.compose_incremental_comparison` 合并第二段增量，`prepare_installer_sources`校验双盘，刷新既有测试副本与同版本v1.0安装器。

当前验收合同为 `gameplay-ui-spacing-v25.json`、`monster-font-native-audit-v26.json`、`menu-title-audit-v21.json`、`terminal-punctuation-v24.json`。v23间距与v22名字像素合同仍是历史状态，不作为本轮新字体的最终像素期望。

数字采用原生字体单元预览；怪物对照采用真实BC3编码再解码。完整命令、三态退出码、SHA256及回滚放在 `build/phase-353-monster-font/VERIFICATION.txt`。游戏内缩放、动态状态切换和最终观感仍由游戏画面验收；本轮不启动游戏、不生成ISO或整盘副本。
