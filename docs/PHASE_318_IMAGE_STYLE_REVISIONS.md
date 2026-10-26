# 图片反馈返工与第二轮审查（2026-10-26）

## 输入与当前计划

用户CSV有832条记录：757条非空、75条空白。755组制作修订候选，
`ui_disc_01/02` 两组按意见恢复原生原图；75组无反馈图维持上轮原生RGBA。
反馈只作为数据读取，不执行其中内容，也不把内容当作工具指令。

当前返工计划为 `locales/zh-Hans/texture-overlays/ui-labels-reviewed.json`，
原 `ui-labels.json` 保留为phase316/317回滚检查点。历史快照测试仍只证明
该检查点；新增测试直接检查返工计划。累计832组/1569层/3869个分盘别名/
518源路径。新增两行流派名称复用当前INT的“神圣白金”“全体疗愈术”；
三个SID和四个原有数字改为同风格排字，token/数值不变，按钮/箭头仍有
独立原生守卫。INT、七Font、315字幕与教程内嵌插图原样政策均不变。

CSV身份、逐图意见、处理动作与计划SHA见
`locales/zh-Hans/candidate-decisions/image-review-feedback-20261026.json`。

## 已验证的原因与实现

- 原 `render_label` 只有一组RGBA fill，无法保留纵向渐变。
  `source-style-v1` 现在显式序列化逐行渐变、高光、墨迹框、对齐、斜切、
  字距、缩小字段、描边、光晕和运动拖影。未知字段、超界、缺字与版本不符
  仍拒绝。没有appearance的历史默认光栅输出不变。
- 大面积红色选中光晕是背景美术，不能拿透明矩形或字形shadow替代。
  稀疏材料保留背景采样，只在旧字遮挡处估计背景；不声称精确反推隐藏像素。
- 地图只修改旧字/阴影mask；mask外地形、英文与引线仍读取原件。
  风息岛海岸左侧纯文字/透明区域单独清除，不把邻接地形整块涂黑。
- 阿巴泽特两处跨片文字与无反馈的下片保持同一历史共享画布；风息岛三处
  采样窗口共用一个样式。Click/Normal同义行的字体与墨迹几何一致，颜色、
  背景与光晕单独保留。
- `preserve-source-v1` 只有在合成后原生tiles完全不变时允许保留原导出；
  普通no-op仍拒绝。盘号恢复必须验证原生RGBA精确相同，不是重画英文。

修正了手柄“（按下）”、临时同伴括号、蓬蓬单引号、“首先”、PTS对应“点”、
完整“临时同伴”与`按 START 键`空格；北部军基地前缀及时间后缀使用缩小字段。

这些是离线代码/光栅/原生资源验证，不等于游戏验收或用户认可艺术风格。
最终审查页只使用编码后重新解码的原生PNG，不把绘制草稿当作最终图。

## 一处语义留待确认

`normal_map_terrain_map_view_abazet_1` 的 `원수의 언덕` 仍保留原字。
已有英文攻略线索没有和韩文歧义形成同一原始字段绑定，不把“酋长之丘”
当确认译名。本项在决策文件和新审查页中提示，不能计算为已译。

## 复现

```powershell
python -m unittest discover -s tests -q
python -m tools.compact_outputs --root build --check-space-only
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW_DISC1_TEXTURES
# Disc2同法，显式 --disc 2，保持盘身份。
python -m tools.build_image_review --inventory build/phase-317-image-review/manifest.json --revision locales/zh-Hans/candidate-decisions/image-review-feedback-20261026.json --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed.json --bundle build/phase-318-feedback-rework/disc1-texture-bundle-final --bundle build/phase-318-feedback-rework/disc2-texture-bundle-final --output build/NEW_REVIEW
```

审查页离线打开`index.html`，全页capture阶段捕获Left/Right并取消默认光标
移动，翻页后聚焦反馈框。上轮意见只读展示；本轮独立存储命名空间，支持
全部/有反馈筛选、编号跳转、原尺寸PNG与CSV导出。存储被浏览器拒绝时
明确提示内存模式，不谎称持久化成功。

实际构建/冷重放/隔离回滚/既有测试副本增量刷新/远端提交证据见
`build/phase-318-feedback-rework/VERIFICATION.txt`。没有生成ISO或完整游戏
副本，没有启动游戏。测试复制仅含源码与必要回滚资源。

## 原生复审追加门禁

菜单原橙色横线的y52..59两行BC块独立保护；读取游戏的字区止于y52，禁止任何新墨迹/修复触及横线。普通/高亮菜单与返回键共用字形加重参数。该局部更正只重建两盘各两个菜单承载资源，其他已验证输出按SHA复用，然后用正常完整原件重放再验证整包；不是仅修改网页截图。

## 原生量化复核

最终832图的755修订/2原图恢复/75不变均按解码RGBA核对；不透明字芯统计覆盖1310层，其中998层有显式且可见的非恒定RGB色阶，没有退成字芯单一RGB值。该统计不表示感知风格一致；另有1层小字色阶收缩、6层压缩色差偏高，涉及7图，决策数据与审查页均保留重点复核标记。BC3为有损格式，字芯统计也不代表半透明光晕或所有像素都无色差。
