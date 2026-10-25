# 阶段316：剩余地图文字与研究室图组

本阶段闭合阶段315列出的剩余正常地图图组，与阶段314流派树及阶段315的27个地图标题一并验证、刷新并发布。地图命名只采用当前INT或可核验的形态/语法锚点；无锚的 `원수의 언덕` 保留原字，不采纳仅有英文地名线索的猜名。三组纯地形 `Map_View_Lastrada_03` 保持原样。

## 采用范围

- 原生对象证明：17个地图地形对象、6个研究室/地图对象，共23个对象；99个新增完整标签层，4个研究室标签均有当前名称锚点。
- 锁定56个文字namespace使用组：55组新增，1组既有Senti标题图扩展；68个物理别名（分盘记录）。保留1组纯地形对象，不创建文字层。
- Abazet跨片两处短语先在真实共享画布上排字，再用实测 `(0,0)`／`(207,512)` 渲染窗口回填两个组件；旧层ID保留，4个物理片段合并为2个完整短语，前后其他像素、英文保护区及邻接地形/引线守卫通过。
- 阶段314的21图、102标签、84别名及阶段315的27图、36标签、28别名与本阶段同一最终计划累计：832图组、1560层、3869别名、518源路径。教程108张插图保持原图。
- `MAX_TEXTURE_SOURCES` 从512有界提高到1024，新增518源集合/越界拒绝与逐盘选择测试；其余上限未改。源补集只从核对过的双盘清单提取22个需要的包（28个物理源），没有重建ISO或完整游戏副本。

## 主要证据

- 语言锚点与待证项：[map-terrain-language-definitions.json](../build/map-name-research/map-terrain-language-definitions.json)。
- 56组/68别名原盘SHA、GUID、payload、tiled与native RGBA锁：[map-terrain-all-aliases-native-locked.json](../build/phase-316-map-terrain-captions/map-terrain-all-aliases-native-locked.json)。
- 17个地形对象原生构建与逐对象像素/引线/英文守卫：`build/phase-316-map-terrain-captions/terrain-prepared/`；6个研究室图组：`room-prepared/`；跨片合并回放：`linked-prepared/merged-final-v1/`。
- 新采用决策与源清单：`locales/zh-Hans/candidate-decisions/normal-map-terrain-captions.json`、`locales/zh-Hans/source-resources/normal-map-terrain-captions.json`。
- 完整累积验证、原测试副本增量刷新、隔离回滚、commit、push与远端SHA核验：`build/phase-316-map-terrain-captions/VERIFICATION.txt`。

## 验收边界

文字mask只覆盖原字芯/阴影的稀疏像素；新增字在原生BC纹理中离线回放，mask外BC块与受保护引线/地形/拉丁字节保持原样。文字遮挡下无法从叠印源恢复原始底图像素，局部遮挡色彩只在mask内插值；不采用整图地形重建，且不以未知地名猜译。地图/房间原生PNG作过逐对象目视审查。离线与包级验证不等同于启动游戏渲染验证；本阶段没有启动游戏。
