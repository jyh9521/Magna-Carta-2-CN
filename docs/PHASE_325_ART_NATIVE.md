# Phase 325：装备名字实际消费者、风息岛透明标题修复

本记录涵盖截图 8、9 的非视频修复及其最终纹理增量集成。原始包只读，未启动游戏、
写入 ISO 或生成完整游戏候选树。

## 已验证

### 装备图上的 Juto 不是升级界面的人物图

原始 `MC2Game.xxx` SHA256 为
`13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641`。
`UI_Field_2.Scenes.Equip`（export 44932）与
`UI_Field_2.Scenes.StyleMenu`（export 44976）的
`CountryJuto_Style: CharacterStyleImage` 均具有两个真实 `ObjectProperty`：

| 消费者 | 字段 | 原包逻辑偏移 | 引用 |
|---|---|---:|---:|
| Equip | MainStyle | 19541518 | 55395 |
| Equip | SubStyle | 19541546 | 55395 |
| StyleMenu | MainStyle | 19597010 | 55395 |
| StyleMenu | SubStyle | 19597038 | 55395 |

export 55395 是 `Style_CountryJuto.Style_CountryJuto`，512×512 单 mip BC3。
独立 `Style_CountryJuto.xxx` 的 export 3 是同一张图；两个包的原始 tiled SHA256 相同：
`238f50c3e01cafc02f285d67a2a563ea086705a12682305f2e0c45262b5e3ae7`。
两包均用于第一、二盘。此前 v6 没有绑定这两处，所以其他菜单名字已经汉化并不能覆盖装备图。

本次新增 `gameplay_style_country_juto_name`，沿用现行“朱特”和已锁定的
Noto Serif CJK SC SemiBold 字体。原英文连同抗锯齿/阴影是独立 alpha 连通分量：
2524 像素，包围盒 `(316,304)–(392,350)`；源裁剪 `(316,300,80,52)`。
只把这个分量恢复为透明，叠加新字，其他原始可见人物/笔刷像素 123959 个逐像素不变。

### 风息岛标题跨两个纹理，旧背景修复错误引入绿光块

相关标签：

- `normal_map_terrain_map_highwind_up_03`
- `normal_map_terrain_map_highwind_up_cave_03`
- `normal_map_terrain_map_highwind_down_01`

前两项来自 `Map_View_Highwind.xxx / Map_Highwind_Up` 与
`Map_View_Highwind_2.xxx / Map_Highwind_Up_Cave`；下半张分别绑定两个包的
`Map_Highwind_Down`。第一包用于两盘，第二包用于第一盘，共 6 个物理纹理别名。

旧 restoration patch 在原本应透明的区域填入最高 alpha 239 的绿光，形成截图中的左右亮块。
新配方从锁定原图的 alpha 支持集产生二值遮罩，透明 patch 为全零；不复制附近绿色像素、
不重绘地形或英文。中文的渐变、描边和上/下片注册保持原实现。

亲自检查原生 BC3 解码后的透明合成预览还发现：旧下片裁剪高度 16 漏掉了左侧
`y=16..18` 的韩文阴影尾部，其 alpha 最大值依次为 58、31、10。
下片裁剪扩为 `(320,0,192,20)`，共享渲染画布高度 44→48，裁剪仍从画布 y=28 开始。
新增 4 行的中文渲染 alpha 全为 0，前 16 行字形字节与旧实现相同。
仅多清除 x=320..371 的 88 个源阴影像素；遮罩排除局部矩形 `(52,16,140,4)`。

完整英文 `HighWind Island` 从 x=375 开始；保护矩形 `(372,16,140,40)` 留有边距。
原英文区域 RGBA 和对应原生 4×4 压缩块均保持原始字节。其他地图文字、地形以及
本轮目标裁剪外的原生块也保持基线字节。

## 数据与集成

- `locales/zh-Hans/texture-overlays/gameplay-art-delta-v7.json`：从 v6/尚未合入 art 的 v7
  应用的完整片段，替换 3 个标签、新增 1 个标签、追加 2 个纹理绑定。
- `locales/zh-Hans/texture-overlays/gameplay-art-tail-delta-v7.json`：仅供已经合入早期 art
  片段的 v7，再修复上述 88 像素阴影尾部。**不要在完整片段之后重复应用。**
- `locales/zh-Hans/texture-overlays/gameplay-art-native-contracts-v7.json`：实际消费者、
  6 个原生测试案例、英文和人物保护条件。
- `restorations/gameplay-art-v7-20261027/`：小型二值遮罩与全透明 patch。
  `*-tail-*` 是新文件，旧素材保留供旧构建和回滚使用。

`tools.texture_region_repair.merge_delta(plan, delta)` 不就地修改输入，按旧标签对象 SHA256
及 source header SHA256 校验前置条件。重复合并、其他人已改动同一标签、错包和重名纹理
均报错，而不是覆盖。命令行同样要求完整输入文件 SHA256：

```powershell
python -m tools.texture_region_repair --plan <现有计划> --plan-sha256 <原SHA256> --delta <完整或tail片段> --delta-sha256 <片段SHA256> --output <新的计划文件>
```

新增独立包 base 与 original 均指向原版 `Style_CountryJuto.xxx`；驻留 MC2Game 继续沿用已有
phase-285 route-probe base，不回退其他字体/文本更改。后续使用既有 texture delta 构建器及
增量刷新路线；不要拿此原生纹理探针输出直接覆盖完整包。

### 最终集成（2026-10-28）

已把 `1718ce2798f1bcc50102e5e14f86a8334f9907124edc05fe24270e9653ef2078`
计划逐字节保存在 `build/phase-325-gameplay-feedback/texture-plan-before-tail.json`，
再只合入 tail 标签。最终主计划 SHA256：
`e8ae524a13ad91f595333b515865b78f10ff03b14f60fdb3c805df5ee30dd936`。
唯一对象变化是 `normal_map_terrain_map_highwind_down_01`，1574 labels / 519 sources，
source 清单未变化。

既有 `disc1-texture-delta` 的 9 包 / 664 层、`disc2-texture-delta` 的 8 包 / 660 层，
均使用 **1718 快照** 独立 `--verify-root` 重放通过；不能使用已经变更的主计划验证它们。
随后从 1718→最终计划只构建并独立验证地图增量：第一盘 2 包 / 10 层，第二盘 1 包 / 6 层。
第二盘不包含 `Map_View_Highwind_2.xxx`。其他大包复用既有候选，没有再次复制或构建。

最终候选选择表是 `build/phase-325-gameplay-feedback/texture-final-resources.json`：
9 / 8 条目逐项列出候选绝对路径、大小和 SHA256，地图取 `disc*-map-tail-delta`，其他取
既有 `disc*-texture-delta`。两盘公共包文件哈希完全一致。该选择表没有执行运行格式
normalization 或部署；统一整合时仍须沿用现有 normalization/增量刷新步骤。

最终资源关联证明来自真正解包后的候选，而不是单独渲染图：

- UI 13 个图像组 / 26 个纹理别名的实际解码像素一致；候选图按消费者 UV 重采样 35/35，
  同一检查在 v6 为 0/35。
- 最终主计划的 64/64 消费者几何合同通过。
- art 两盘 10/10 物理别名的 tiled 与 RGBA SHA256，逐项精确等于本节原生三态探针的修复结果。
- 最终主计划直接运行完整 art 探针仍为 6/6。
- 独立计划副本由新计划写入后，按保留快照恢复成 1718 原始字节；最终主计划保持 e8ae。
- 纹理相关 167 项测试全部通过。消费者合同由 61 扩到 64 后，同步了旧测试计数，并显式锁定
  `back title: pulse registration`、`back title: shadow registration`、
  `Reverse: paired glyph shape` 三项的名称、模式、标签及实际采样窗口。

具体命令、退出码、输出和资源哈希见
`build/phase-325-gameplay-feedback/texture-final-integration/VERIFICATION.txt`；
`native-final-package-sampling.json` 保存每个候选包→纹理→像素哈希的关联。

## 可复现三态与本地证据

```powershell
python -m tools.probe_texture_region_repairs --mode baseline --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json --contract locales/zh-Hans/texture-overlays/gameplay-art-native-contracts-v7.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/phase-325-gameplay-feedback/loading-art/art-native-v1
python -m tools.probe_texture_region_repairs --mode modified --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json --delta locales/zh-Hans/texture-overlays/gameplay-art-delta-v7.json --contract locales/zh-Hans/texture-overlays/gameplay-art-native-contracts-v7.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/phase-325-gameplay-feedback/loading-art/art-native-v1
python -m tools.probe_texture_region_repairs --mode rollback --output build/phase-325-gameplay-feedback/loading-art/art-native-v1
python -m unittest discover -s tests -p '*region_repair*.py' -v
```

- BASELINE：`FAIL BASELINE 0/6 native caption cases`，退出 1，准确复现左右绿块及真实装备图漏译。
- MODIFIED：`PASS MODIFIED 6/6 native caption cases`，退出 0；4/4 透明配方由原生 alpha 重新计算通过。
- ROLLBACK：`PASS ROLLBACK 6/6 native copies restored; MODIFIED unchanged`，退出 0。
  回滚在独立副本逆向应用实际变化单元，6 个副本与基线原生字节一致，修正文件不动。
- 13 个专用测试覆盖邻接图保护、低 alpha 残留、旧源/并发修改拒绝、独立回滚、错误哈希拒绝。

探针使用实际 Xbox BC3 解码/编码与生产 `overlay_profile_regions`；不是只检查 PNG 或字段存在。
生成体量约 5.9 MB。绝对路径、输入/输出 SHA256、完整命令/标准输出/标准错误/退出码保存在
该目录的 `VERIFICATION.txt`、`commands.json` 与各阶段报告；已重新打开校验。
合成预览的纯色背景只用于检查透明度，不是游戏内截图。

## 验收边界

已验证原生消费者、纹理采样、双别名一致、受保护像素/块、三态回滚和可合并数据。
包级增量构建和独立验证已完成；部署由本轮统一整合完成，最终装备和地图页面仍由用户在游戏内验收。
本片段不包含加载视频，也不改变其他人物姿态图。
