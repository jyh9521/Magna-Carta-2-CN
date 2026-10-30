# 主界面读档与游戏内存读档的字体、右边界修正

## 根因与证据等级

**Verified / 文件与原生像素：** 阶段335只修改、检查了 `UI_Pillar.xxx`。
同名 `UI_Pillar_Title.Scenes.GameStart_Load` 还驻留在 `TitleMap_MSPT.xxx`；
后者三个槽位的标题 X 仍是 754 / 798，而不是前者的 765 / 794。
对当前测试资源新增标题地图检查得到 `CHECKS=12 FAILURES=6 RESULT=FAIL`。
不能因为包内存在 `GameStart_Load` 名字就把另一物理副本算作已经修复。

**Verified / 绘制算法：** 两个标题的旧 `font_size` 都是16，原生可见字芯也都为13高，
但 `source-style-v1` 原来将每串字各自裁到墨迹后撑满13高。
锁定 Noto 字体的64px测量中，“游戏时间”的字形高度为61，`SID`为49；
分别撑满会把 Latin 字母额外放大约24%。相同配置字号或相同大写字高不代表相同 em 缩放。

**Verified / 控件：** 两份场景包共九个槽位的时间、SID数值都使用同一
`StringStyle.AssignedStyleID`，且 `TextAlignment[0]=2`、`bOverrideAlignment=1`。
但每对 X 相差约0.1359，SID控件高为23.9995，时间为24。
修正只将 SID 的 X/高度精确复制为同槽时间的值，保留 Y、宽度、样式和数值来源。
这些序列化值的单位不在本轮擅自换算为屏幕像素。

**高置信解释：** 标题地图中的旧副本解释了用户“游戏内已齐、主界面没齐”的差异；
同名对象并不能确定实际加载的是哪份包。本轮没有启动游戏，最终三个入口的画面仍由用户复测。

## 有界修正

- `font_scale_reference` 是可选的、语言无关的绘制参数。语言数据指定“游戏时间”为
  共同的字形高度参照，使这两个标签使用相同 em 缩放，保持原来的底线、颜色和描边。
  默认绘制行为不变；缺字、空参照、混合字号、外部字形蒙版和高度越界明确报错。
- 两份 `Field_MainMenu_Info_Tex04` 原生贴图（`MC2Game.xxx` 与 `UI_Field.xxx`）同步重建。
  字芯高度现在为中文13 / Latin10，这是同一字体比例下的自然字形高度，不再强行拉大 SID。
  时间右端相对 UV 起点仍为75，SID由46变为41。
- 存读档三个槽位中的 `PlayTime_Title.X=765`、`SID_Title.X=799`，原生字芯右端均为840。
  `UI_Pillar.xxx` 的保存/读取共用场景和标题读取副本，以及 `TitleMap_MSPT.xxx` 的标题副本均覆盖。
  普通场景菜单的共享贴图也获得同一字体比例；它的左对齐位置不变。
- 唯一游戏资源写集为上述四个包。工具对整包、整导出及字段原值做SHA/类型守卫；
  图集仅转移 `[152,16,80,32]` 的原生块，所有非选导出和区域外块保持。

## 可复现入口

数据位于 `locales/zh-Hans/save-slot-{title,save}-fields.json`、
`save-slot-textures.json`、`save-slot-geometry.json` 和
`texture-overlays/save-slot-labels.json`。字段profile的对象前后摘要锁定阶段335资源；
不可把它直接用于未知包或直接用于原盘压缩包。

```powershell
python -m tools.patch_tagged_fields apply SOURCE --source-sha256 SHA --profile PROFILE --profile-sha256 PROFILE_SHA --output NEW --report REPORT
python -m tools.build_texture_region_update --profile locales/zh-Hans/save-slot-textures.json --profile-sha256 PROFILE_SHA --input-root BASELINE --output NEW_TEXTURES --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -m tools.audit_ui_geometry --root CANDIDATE --plan locales/zh-Hans/save-slot-geometry.json --report NEW_REPORT
```

本轮153项检查沿实际 `ImageComponent → ImageRef → ImageTexture` 引用读取UV及原生BC字芯，
检查两份贴图、三个场景副本的全部槽位、标题底线/右端、数值的边界/样式/对齐覆盖开关。
不是只给 X 加一个脱离当前贴图的常数。新增夹具验证“游戏内正确、标题副本错误”和
“右端正确、字高错误”都能单独失败。阶段335的存档标题墨迹偏移合同是历史值，
当前存读档验收改用本文件的新合同；战斗和商店合同继续保留。

基线为 `CHECKS=153 FAILURES=42 RESULT=FAIL`；修改为
`CHECKS=153 FAILURES=0 RESULT=PASS`。四包独立回滚应逐字节恢复基线并重现42项失败，
不把重新出现旧问题算作修复成功。完整命令、哈希、退出码及回滚入口保存在
忽略的 `build/phase-336-save-slot-alignment/VERIFICATION.txt`。

合成仍走 `compose_incremental_comparison` → `normalize_runtime_comparison build` →
`refresh_oneclick_probe`，沿用现有测试目录，不生成ISO或完整游戏副本。
双盘安装器输入通过原盘路径与原始摘要一致性共享修正，不复制完整游戏来验证。

## 用户画面复测

1. 完全退出上一次游戏进程，再从主界面进入读取存档，查看三个槽位。
2. 在游戏内分别进入保存、读取，查看三个槽位以及选中/未选中状态。
3. 核对“游戏时间”与SID的字体比例、两行标题右端及两行数值右端；确认长时间和大额SID仍正常。

旧的独立ZAR/ISO不会被测试目录增量刷新自动改变。使用更新后的安装器生成的内容，
或现有的“开始中文测试”目录入口进行复测；不把旧容器的截图当作新资源的结果。
