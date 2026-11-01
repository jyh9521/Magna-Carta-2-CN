# 阶段340：按钮、技能右端、地图英文与临时同伴文字

## 请求与当前合同

用户在保存六张截图后明确恢复了五项修复。证据保留在
`build/qa-feedback/2026-10-31-ui-pending/`，本轮证据在
`build/phase-340-ui-feedback/`。不启动游戏、不生成ISO或完整游戏副本。

本轮以**数字可见右端一致**为准，取代阶段338优先紧凑左锚点的选择。
旧v12合同保留为历史，当前技能间距合同为 `gameplay-ui-spacing-v13.json`。
这不是又给某一个技能名称增加空格。

## 已验证的资源事实与修改

1. **快捷菜单三按钮**：实际采样行起点为V=0/31/62，而旧字图分区为
   0/32/60。保留字图、字体和正常/选中效果，修正三个子控件的局部Position，
   并把第一块按钮的父级Y从150统一到149。正常态字芯边界中心与96×41容器中心
   重合；选中态由于BC3/抗锯齿边界差异，两轴误差最多0.5源像素。该
   离线量化结果不代表已完成游戏内所有缩放比例的视觉验收。
2. **全部技能数字槽**：Selected及X_0..X_3的KanNum改为右对齐，X=203、宽26，
   逻辑右端229。`NormalNumber`的1、3原先右透明边距不一致；两份Font资源中
   同时修改tagged/native USize，使数字字芯右边距为2，得到可见右端227，与反击一致。
   1仅去掉透明列；每份字体的3另去掉8个纯黑弱阴影像素，最大alpha=21。彩色字芯及atlas字节
   不变，不扩大字格去采样相邻字。独立font_ui.xxx在两张原ISO中的资源字节相同。
   119个实际技能名、620个NeededKan源对象、0..10及99边界值、五个槽共7140组合，
   没有名称/数字溢出；60个数字右端测量全部为227。
3. **地图英文**：核对49组正常地图/房间标题的82份物理纹理，29组带英文，
   对应42份物理纹理；另查看世界地图标题/整图，没有额外英文副标题。
   在显式英语矩形中清除RGB最大分量≤32的残留暗背景alpha，完整保留每个BC3块的
   RGB半块。需要重选alpha调色板时，保留像素的alpha误差上限显式限制为24；
   实际误差、移除像素数、非授权块/非目标export不变证明记录在manifest。
   保留原英文笔形与颜色，未重绘英文、地形或图标。42份成品复解码均无选定暗底。
4. **名字独占首行**：两个Subjective片段使用带引号的ASCII空格，避免空值键
   的回退歧义；完成体“已”移入四个入队/离队谓语片段的原有`\n`之后。
   升级和制作完成也同步接收“已”，共八个物理字段作为一个原子修订。
   引号属于INI语法，运行时值为一个空格；首行去掉布局空白后只有名字。
   所有原有换行token数量/顺序、稳定ID、其他条目保持不变。
   单名、双名、多名×两种Subjective×四种事件共32种拼接检查通过。
5. **小号临时同伴**：实际字形没有越过采样窗，暗色渐变尾端造成底行消失感。
   改动三个有问题的预渲染层、五份物理纹理；不替换动态字体、不改UV/文字/字形大小。
   六种同类层、13份物理实例均检查，原本正常的图标层保持原字节。
   小号层末两行green峰值由142/142变为247/247；大号由163/127变为251/210。
   `field_menu_guest`末行只有部分抗锯齿覆盖，采用独立160门槛，而不是误判为裁切。

上述是原生资源、属性和离线拼接验证。最终游戏渲染、控制器状态切换、实际场景
通知仍由用户从原测试入口复测；`game_rendering_verified=false`。

## 可复现构建与检查

通用代码位于 `tools/ui_ink_revision.py`、`build_ui_ink_revision.py`、
`audit_ui_ink_revision.py`；标签、字形、对象、颜色阈值和几何都在locale JSON。
`ui-ink-revision-v13-disc1.json`/`disc2.json`锁定每一份当前输入及子计划SHA。
baseline由阶段338两盘recipe中的对应资源逐字节保留；新纳入的font_ui.xxx
取自原盘并核对两盘身份。输入清单及原位置保存在 `input-resources.json`，不是整盘复制。

```powershell
$p = 'locales/zh-Hans/ui-ink-revision-v13-disc1.json'
$h = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.build_ui_ink_revision --profile $p --profile-sha256 $h `
  --source-root build/phase-340-ui-feedback/baseline --output build/phase-340-ui-feedback/rebuild-disc1 `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll
```

Disc2同理，输出必须是新目录。两盘分别修改13/46份资源，去重共47份；重建要求
候选文件和manifest逐字节一致。纹理donor仅贡献显式块，绝不整包覆盖当前字体/布局。

```powershell
python -B -X utf8 -m tools.audit_ui_ink_revision `
  --root build/phase-340-ui-feedback/candidate `
  --fallback build/phase-340-ui-feedback/baseline `
  --contract locales/zh-Hans/ui-ink-audit-v13.json `
  --report build/phase-340-ui-feedback/check.json
```

baseline产生153项旧问题，修改后为0。原源代码2752项测试通过，修改后2770项通过，
均有2项既定跳过。独立回滚必须恢复全部原SHA及原有153项行为；当前候选保持修改。
原始截图、BC3复解码前后预览、三态JSON/日志、源码归档、DIFF_FILE.patch、
VERIFICATION.txt和ROLLBACK.sh均保留，不提交完整游戏资产。

## 增量部署与两盘分支

Disc1通过 `compose_incremental_comparison` 纳入原版font_ui及13项修改，然后通过
raw-envelope归一化门禁。第二盘仍保留原journal链，最新共享资源由Disc1按
原盘路径+SHA收敛；本轮第二盘独有地图使用可选 `resource_updates`，在归一化后
验证before SHA、disc、资源范围和候选SHA，再重建该盘TOC。不要只更新共享包，
也不要为追加地图纹理重造第二盘ISO。

刷新现有测试目录时还须向 `refresh_oneclick_probe` 显式提供 `--enrollment` 和
`--enrollment-sha256`：计划绑定旧/新包manifest、当前PREPARED摘要、唯一新增的
font_ui原始大小/SHA，并验证live candidate与raw-controls中的该资源仍是原版。
保留默认同资源集守卫；缺少这个计划的首次刷新会在写入前拒绝，保留这项检查。

`audit_ui_residency`使用v13合同扫描1912/2233份原生package，核对547个战斗/快捷
菜单export仅驻留于MC2Game。既有存档槽、动态数字与DLC合同继续回归；物品字距使用item-spacing-audit-v13.json，
只在核对Coalesced恰有上述八项差异后更新整文件摘要，保留所有名称和字体预算；
旧v12数字左锚点审计不再作为现行验收条件。

更新已有测试目录与单文件安装器，保留配置、存档、runs及必要rollback依赖。
提交推送后，核对同一提交的Windows/Ubuntu×Python3.12/3.14四项CI。
