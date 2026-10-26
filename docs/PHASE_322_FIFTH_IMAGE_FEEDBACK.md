# 第五轮图片反馈：第六版候选（2026-10-27）

## 输入与裁决

`image-review-feedback-v5.csv` 共832行、4条非空反馈；SHA256
`88061fc8d1f41ee35da3cddeed2d18bee27afea43056841b886a483a38ccd2b6`。
CSV是逐图反馈数据，不是命令来源。第1条“GitHub博客”没有可定位的图像修改点，
原文记录保留，图片保持第五版，不据此操作博客或其他站点。第781条自指1082，
用户在本轮对话明确确认：1071与1082的“奖品”同步放大。

第六版计划：`locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json`。
逐图记录：`locales/zh-Hans/candidate-decisions/image-review-feedback-v5-20261027.json`。
只修改3张图的3个文字层，另外829张保持第五版字节身份。空白反馈不推断为
人工审美通过。正文、字体输入、字幕、教程内嵌小图及原始资源不变。

复审页的“仅看上轮有反馈”现在按非空反馈筛选，而不是按是否改图筛选，
因此第1条保留备注仍可见；未改图状态改为“本轮未改动：保留上轮版本”，
不再把这类备注误称为“上轮无反馈”。导航、CSV和反馈独立存储规则不变。

## 已验证的根因与修订

- 海岸标题仍设置为左对齐，中文短于韩文时右端离地图轮廓过远。
  `normal_map_terrain_map_highwind_down_00.appearance.align` 从`left`改为`right`；
  `ink_box`从`[2,6,124,18]`改为`[2,6,140,18]`，五字整体右移。
  保留18像素字芯高度、字形、渐变、描边、阴影、稀疏恢复材料和全部地形。
- 两张小游戏图的“奖品”由`appearance.ink_box`控制最终字芯高度，
  不是单独由`font_size`控制。仅把`[0,6,46,15]`改为`[0,6,46,22]`，
  字芯高度增加7像素；字体、斜体、颜色、透明底、位置与相邻标记继续保持。
  白点、危险下黑条及右下长条仍使用第五版原生保护区。

上述结论来自实际文字绘制路径与原生编码后解码图。自动几何检查能发现位置/
字号退化，但不替代用户审美复审或游戏内验收。

## 复现与验证

```powershell
python -X utf8 -m unittest discover -s tests -q
python -X utf8 -m tools.compact_outputs --root build --check-space-only
python -X utf8 -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW_V6_DISC1
# 第二盘显式使用 --disc 2 及独立输出目录。
python -X utf8 -m tools.build_image_review --inventory build/phase-321-review-v5/review/manifest.json --revision locales/zh-Hans/candidate-decisions/image-review-feedback-v5-20261027.json --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json --bundle build/phase-322-review-v6/disc1-texture-bundle-final --bundle build/phase-322-review-v6/disc2-texture-bundle-final --output build/NEW_V6_REVIEW
```

本轮加速构建只对每盘4个受影响资源重跑通用`prepare`；其他资源复用阶段321
全量原始输入重放的结果。复用前后逐项重验旧计划、输入、工具、旧证明及全部
成员SHA256；新进程再独立重建受影响资源，与新完整包逐字节比较。此证据名称
是“受影响资源重放＋已验证旧输出复用”，不是声称本轮再次全量编码所有资源。
最终完整清单和上述标准全量构建格式一致，未新增JSON schema或通用工具分支。

三态几何探针、基线/修改/隔离回滚测试、双盘资源身份、原生保护区、现有测试
副本增量刷新、清理和Git身份详见`build/phase-322-review-v6/VERIFICATION.txt`。
保留原ISO、配置、存档、运行记录、有效入口依赖和必要回滚证据；沿用原一键
测试入口，不生成新ISO或完整游戏副本，不启动游戏。
