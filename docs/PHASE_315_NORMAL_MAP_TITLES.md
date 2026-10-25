# 阶段315：正常地图标题图组

已将首批27个真实地图标题图组作为正常原生纹理采用：36个完整文字层、28个物理别名，复用当前INT地名/试炼锚点，不从旧图猜译。英文副题、数字、原地图地形与引线均保留；与阶段314流派树修复一并进入阶段316统一验证和发布。

## 可复现证据

- 原生候选与字形清理：`build/phase-315-normal-map-captions/map-title-native-batch-complete.json`、各组 `native-proof.json`。
- 实际namespace、原始包SHA/GUID、原始RGBA和payload锁：`build/phase-315-normal-map-captions/map-title27-all28-aliases-native-locked.json`。
- 当前译文锚点：`build/phase-315-normal-map-captions/map-title-family-language-definitions.json`。
- 决策数据：`locales/zh-Hans/candidate-decisions/normal-map-view-titles.json`。
- 正式阶段316累计验证、刷新、回滚和远端身份记录：`build/phase-316-map-terrain-captions/VERIFICATION.txt`。

阶段315没有单独刷新测试副本或提交；避免覆盖阶段314尚未刷新的旧测试检查点。双盘全量纹理、合成、对照与冷回放在阶段316累计计划中运行，然后对原有阶段313测试副本作一次哈希保护的增量刷新。
