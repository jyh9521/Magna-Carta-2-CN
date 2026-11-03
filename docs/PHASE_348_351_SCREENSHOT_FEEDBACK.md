# 阶段348–351：菜单、译名、技能数字与句末标点

本轮基线为 `80cde30a590eb4f0db1d0b01c9f936102a23c56c` 的阶段347资源，依照用户顺序处理四类截图；最后追加的“选项左边缘”纠正也包含在最终候选中。

## Verified：菜单与追加的左对齐

- `Field_MainMenu_Big_Title0` 旧文字阴影越过原清理边界，残留在 x=33..35。两份物理图集共754个暗色非透明像素；六行统一清理后为0。x=32的橙色图标光晕、文字和其他区域保持。
- “选项”复制“道具”的完整字体、字号、渐变、描边、发光与投影配置，而非只换字体。Noto Serif CJK SC SemiBold，描边0.45、投影偏移[1,1]，保留既有字号及36px行高。
- 用户追加左对齐后，选项 ink_box.x 从10改为5。原生BC3可见左边缘为38，与编队/技能/装备/强化/道具/信息一致；主菜单原有字形的光学边缘39保持。两别名左对齐审计通过。
- 输入/输出：`menu-title-cleanup-v21.json`、`menu-title-style-v21.json`、`menu-title-style-update-v21.json`、`menu-title-audit-v21.json`。

## Verified：图片与文本译名

全量清点既有1599条图片文字、544个来源描述及18176条实际INT记录，并以原文哈希、已确认读法、稳定文本ID和韩/日同字段建立对照。136个自动候选逐项处置；语境修饰、全名/简称、同形异义词不做盲目替换。

- 修正45个图片文字层、136个纹理别名，涉及86条资源路径。包括克洛珀斯→克洛普斯、拉珀斯→拉普斯、蓬→蓬蓬、剧毒蠕虫→毒蠕虫、兽化野猪→野猪人等。
- 9条文本修订统一编队菜单、语音剧和狼人盗贼。剧情中的普通动词“编成潜入部队”保持，避免把术语替换扩散到普通语法。
- `로드` 的菜单“读取”和武器“法杖”不是译名冲突；未采用的候选术语、无相同原文身份的怪物及旧日文技能变体不合并。
- 新的 `build_texture_alias_update` 只从原始资源重绘的供体复制明确BC块。所有当前资源、原纹理、供体计划和字体依赖均校验哈希；无关导出及块保持。支持显式的双盘/单盘物理别名，不按文件名猜测绑定。
- 原生审计的136个修订窗口来自独立重绘供体，不是从被检查的输出反抄期望值。基线136失败，修改后0失败。
- 数据：`name-consistency-v22.delta.json`、`name-consistency-v22.json`、`name-alias-update-v22.json`、`name-text-consistency-v22.json`、`name-native-audit-v22.json`；完整候选处置见 `candidate-decisions/name-consistency-20261103.json`。

## Verified：技能名称与数字

只将Selected及X_0..X_3的Skill父节点 X 从200移至208；五处字段同尺寸修改，子文字及四层阴影一起移动。数字位置/字体/右对齐完全不改。

- “凌空震踢”与1的原生字芯间隙23→15px，数字右边缘仍为227，与下方“反击”一致。
- 119个实际中文技能名、620个NeededKan来源、实际0..10数值域、5个槽位组成6545个包络组合。全部可见间隙10..24→2..16px，无字芯重叠；真实双位数10也覆盖。
- 旧阶段340额外构造的99不属于已核验的游戏消耗域。新合同从实际620个来源确认最大值10；未来若出现更大的数值，审计报错，不默默扩大允许范围。未修改数值或声称实现动态自动间距。
- 数据：`skill-number-fields-v23.json`、`gameplay-ui-spacing-v23.json`；检查器同时使用原生字格和实际白色字芯，避免把透明边距误判为相交。

## Verified：完整逻辑消息的句末标点

旧检查只检测“多余句号”，且描述按视觉行分割；逗号在上一行、句尾在下一行时没有反向缺失检查。

- 按已存在的122份审阅分类数据扫描18176条记录，其中14159条有已采用分类；452条补全句末标点。剧情、字幕、名称与未完成运行时片段保持。
- 43条任务说明、141条技能说明等包含在452条中；用户截图的克洛普斯任务现以“克洛普斯。”结束。
- 视觉 `\\n` 不代表句子结束；数值属性行、计数括注、选择项分行各自处理。问号、感叹号、省略号和语气延长符保持；标记、占位符、数字、换行和其顺序保持。
- 45个有已核验UI尺寸绑定的改动段落另做原生字宽/行数检查，全部通过，新增换行0；新增所需字形0。其他字段的最终自动折行仍属于游戏内画面验收。
- 当前构建必须运行 `tools.audit_terminal_punctuation`；历史batch不重写，增量记录为 `terminal-punctuation-fix-v24.json`，分类与规则在 `terminal-punctuation-v24.json`。

## 可复建入口

依次以阶段347候选为基线：先按v21清理/重绘菜单并合成增量包，再以该候选构建v22别名和文本修订，再应用v23字段，最后应用v24文本。每个输入的资源/导出/字段哈希均在对应计划中；输入不匹配即停止。通用工具不包含中文译名。

```powershell
python -m tools.build_texture_alias_update --profile locales/zh-Hans/texture-overlays/name-alias-update-v22.json --profile-sha256 PROFILE_SHA256 --project-root . --source-root CURRENT_RESOURCE_COPY --output NEW_ALIAS_OUTPUT --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -m tools.audit_texture_alignment --root CURRENT_RESOURCE_COPY --fallback CURRENT_RESOURCE_COPY --contract locales/zh-Hans/name-native-audit-v22.json --report NEW_NAME_REPORT.json
python -m tools.audit_skill_number_spacing --root CURRENT_RESOURCE_COPY --fallback USER_GAME_COPY --plan locales/zh-Hans/gameplay-ui-spacing-v23.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --report NEW_SPACING_REPORT.json
python -m tools.audit_terminal_punctuation --input CURRENT_COALESCED_INT --contract locales/zh-Hans/terminal-punctuation-v24.json --report NEW_PUNCTUATION_REPORT.json
```

`tools.patch_tagged_fields` 提供v23的apply/verify/rollback；`tools.build_coalesced` 应用v22/v24的稳定ID和整文件哈希增量；`tools.compose_incremental_comparison` 按各阶段replacement manifest合成。禁止把供体整个包覆盖当前包，否则会丢失之前的字体、标题和UI修复。

## 交付与证据

最终双盘仍为442/543个资源及2个DLC，资源集合和版本v1.0不变。相比阶段347，第一盘61、第二盘64个资源身份变化（含各盘独立TOC）；共88个内容路径及2份TOC。既有测试副本通过哈希守卫增量刷新，不生成ISO/整盘，不启动游戏。

实际命令、退出码、三态报告、独立重建、原安装器及保护清单保存在忽略目录 `build/phase-351-punctuation/VERIFICATION.txt` 与各阶段证据目录。最终菜单预览为 `build/phase-348-menu-titles/comparison.png`。隔离回滚恢复原哈希和四类基线行为，修改候选保持；发布身份、测试及同提交四组Actions须在最终凭据中核验，不以本文代替执行记录。
