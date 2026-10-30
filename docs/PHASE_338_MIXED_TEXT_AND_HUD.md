# 阶段338：混排间距与战斗技能行居中

## 输入与结论

基线为 `0bab051a7b1f1c8a89ab4928f9083075993421f0`，延续阶段337资源，
不撤回此前 loading、物品和三个存读档入口的修订。

**Verified：** 当前五个KAN数字槽宽26，不是阶段330的历史36；阶段335为了固定
右边界而恢复了右对齐，使单数字远离技能名。当前需求以紧凑混排优先，替代旧的
`cost_right_edge=231`合同，而不是继续放宽旧间距阈值。

**Verified：** `Font.General_15`中全角１字格宽27、可见字芯范围9..17，也有多余留白。
问题不只是文本空格，汉字/数字两个方向都需要检查。

**Verified：** 30高背景中的技能子节点Y=-1.1，文字框Y=3、高26，字体单元高25。
119个技能名的字芯中心为11..12，原来相对行中心偏上0.6..1.6。垂直居中标记
不代表可见字芯居中。B文字继承GeneralFont样式，A和五个X文字显式覆盖字体。

## 修改范围

- `hud-mixed-fields-v12.json`：5个数字槽X=205→202、水平对齐2→0；保留26宽以容纳
  0..10和99边界。名字仍右对齐，数字以紧邻名字的左边界为锚，不再要求数字右端固定。
- 7组主文字及28个阴影的Y同步增加1.6；保留字形、字号、行高、图标和阴影相对位移。
  覆盖Selected、X_0..3、普攻A、反击B，不逐个技能硬编码坐标。
- `mixed-font-padding-v12.json`：七字体副本中选择全部2363个已映射汉字和11个数字
  （0..9、全角１），沿用左2/右3的透明边距，绝不裁非零alpha。16,618个字格中
  9,863个advance改变；纹理字节、字芯像素、垂直指标和映射不变。
- `mixed-text-v12.json`：源摘要锁定20处译文值，只收紧名称、类型、进度和数量相关空格。
  298个字段的属性分隔保持原样，例如“攻击+24 防御+5”；不合并不同属性。
  字段ID、数字数值、标点和控制码保持原样。

四份字体包加Coalesced共5个资源，另由composition更新TOC。游戏文件只留在忽略目录。

## 离线度量

`mixed-text-layout-v12.json`结合原生atlas字芯与序列化UI坐标，不使用替代TTF。

| 检查 | 基线 | 修改后 |
| --- | --- | --- |
| 七副本汉字/数字双向组合 | 最大15..21 | 全部5..8 |
| 119名 × 12个消耗边界 × 5槽 | 可见间距8..26 | 全部5..7 |
| 技能行字芯相对中心 | -1.6..-0.6 | 约0..+1 |
| 普攻/反击相对中心 | -1.6 | 约0 |

共363,902个混排组合、7,140个技能/消耗组合。消耗来自620个实际资源实例及真实CDO默认值，
另覆盖99；这是穷举组合包络，不声称每个组合实际绑定于某个技能。
中心容差1.01原生坐标单位容纳字形外框差异和浮点舍入，不表示逐字光学中心完全相同。

数值使用原生`font_ui.NormalNumber`，不是朱雀数字。六个WhiteNumber样式状态、
六个GeneralFont状态及覆盖开关均核对。独立font_ui包的atlas含外部TFC bulk，
只与其核对native字格；像素取MC2Game完整驻留atlas，不声称读取了外部TFC像素。

两盘完整安装视图由`audit_ui_residency`扫描1912/2233个原生包，匹配完整和短对象路径。
预期498个相关导出均在各盘MC2Game包中；出现额外驻留副本则失败，不按同名去重。

**High-confidence deduction：** 同一组HUD消费者将此位移用于全部角色对应技能。
**Unverified：** 模拟器最终缩放、动态状态切换与屏幕观感。离线通过不等于游戏内验收。

## 重建与审计

使用阶段337源身份的已有测试目录，输出必须为新目录，原件不写入：

```powershell
$p = 'locales/zh-Hans/metric-revision-v12.json'
$sha = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -X utf8 -m tools.build_metric_revision --profile $p --profile-sha256 $sha `
  --project-root . --source-root dist/MC2-display-repair-disc1/candidate `
  --output build/phase-338-hud-mixed-spacing/revision
```

入口组合`fit_font_padding`、`patch_tagged_fields`、`build_coalesced`，验证源摘要、
双份字格、字段前后像、UI逆变换、控制码和输出回读。`manifest.json`保留证据；
`replacements.json`直接输入`compose_incremental_comparison`。第二次重建须逐文件相同。

```powershell
python -X utf8 -m tools.audit_mixed_text_layout `
  --root dist/MC2-display-repair-disc1/candidate `
  --overlay build/phase-338-hud-mixed-spacing/revision/candidate `
  --plan locales/zh-Hans/mixed-text-layout-v12.json `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll `
  --output build/phase-338-hud-mixed-spacing/check-new.json
```

组合包须先通过阶段332`normalize_runtime_comparison`，再刷新已有目录。
`prepare_installer_sources`的两盘recipe须核对五个共享资源相同；使用该recipe、其摘要、
上述plan、`--disc 1`/`--disc 2`分别运行`tools.audit_ui_residency`。

回归继续使用`save-slot-geometry.json`、`font-numerals-audit-v9.json`；物品检查使用
`item-spacing-audit-v12.json`，DLC字宽使用`mixed-font-metrics-v12.json`。
后者只替换advance摘要，保留原布局预算。v11及阶段335固定右端合同作为历史保留。

## 收尾与复测

证据根为`build/phase-338-hud-mixed-spacing/`。`VERIFICATION.txt`记录准确命令、输入、输出、
退出码、资源SHA及回滚；`ROLLBACK.sh`只在新副本上验证恢复，不回退当前测试目录。
源代码另由baseline/modified归档验证逆补丁后逐文件同一。保留原件、配置、DLC、存档、runs和包依赖。

增量更新已有`dist/MC2-display-repair-disc1`及单文件安装器；不创建新ISO/完整游戏副本，
不自动启动游戏。推送后核对同一提交的Windows/Ubuntu × Python3.12/3.14四项CI。

复测从既有中文测试入口进入：观察“凌空震踢1”、消耗0/1/10、展开列表及普攻/反击，
再检查类型1..4、全角１与汉字相邻处。此前独立ISO/ZAR不随测试目录增量更新。
