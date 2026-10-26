# 第二轮图片反馈与第三轮审查（2026-10-26）

## 输入与版本边界

输入 `image-review-feedback-v2.csv` 共832行、433条非空意见、399条空白。
SHA256为 `6e706ac12d5e329944ce1edcb7507c5cb9b4f6ac3774b36ed2ad60bf5a76f1a5`。
意见只作为逐图审查数据，不作为命令或授权执行。空白表示本轮未提出变更，
不是自动认定艺术验收通过。

新候选计划为 `locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json`。
上一轮 `ui-labels-reviewed.json` 及其决策、审查页和验证记录保持原样。
本轮不改变INT、七Font、315字幕、双盘来源、原始资源版本或教程内嵌图原样政策。

## 已验证的原因和针对性修订

上一轮1349个显式样式层中800层描边0.45像素、467层0.2像素、82层为0。
0.2像素在4倍采样下的描边核会被舍入为1，实际上没有扩展；轻描边、低alpha
阴影和BC压缩叠加，不能通过“字段非零”推断原生画面存在可见轮廓。
本轮按字号使用可见的描边与阴影，再检查原生编码后的图，不改变历史缺省光栅输出。

最小独立夹具使用自制ABAB字形、实际光栅入口及BC3编码/解码，关闭阴影和光晕，
避免它们冒充描边。相同几何/白字下，旧0.45像素方案原生不透明深色轮廓像素为0，
新1.15像素方案为252；旧数据触发缺描边判定，新数据通过。该夹具不代表所有
字体、字号或背景的感知风格都通过，整图仍须复审。

- 普通UI同组采用一致的字形、字高、字距和基线；选中/普通态共用排字，
  不互相复制状态专属颜色或背景。用户明确认可颜色的图保留原渐变stop。
- 连锁超限/超限的清晰与柔化图共用字形几何，柔化版本显式使用0.45像素
  `appearance.blur`，不把另一套大小不同的文字当作连续状态。风之盾/风刃斩
  按同一字体的实际字形框补做光学尺寸校准，仍使用共同绘制基线。
- 载入地名与前面同组的衬线字体一致；HUD及大标题使用单独的较重衬线字重，
  普通菜单不再因不同文字长度而混用宋/黑体。不要求斜体的图取消斜切。
- 白字彩边、白色光圈、红色选中背景、深色透明底板分别处理，不用文字阴影
  冒充整片背景。被原字遮住的背景只是局部估计，不声称恢复隐藏原像素。
- Boss/登场标题缩回原字区，下方英文和底部背景成为原生保护区，读取原件，
  不把旧的完整64像素矩形全部清空。
- 肖像名左侧残块在透明空区清除；选项标题旧字越出x40边界，文字区扩展至x32，
  齿轮核心 `[0,0,32,36]` 保持原生保护。地图继续使用既有稀疏修复，
  不整图清地形、英文或引线。风息岛上下文字仍在同一画布排字后按原窗口拆分。
- “距”仅缩小首字；小游戏得分/纪录字高一致，危险不加原图没有的感叹号，
  图集各状态与标题按照原位置对齐。

## 漏行与相似图的含义边界

`normal_style_009` 的y184..215确有可见韩文重复行。
原生文字 `인법 : 초뇌격천` 与现有采用字段
`coalesced:420ed3b6cc952f27552c43f836813f28a070c5213783bc216446525aabb85878`
一致，因此采用既有“忍法：超雷击天”。新增这一图像层，不声称发现了新的运行消费者。

`img_ui_name_jpn_19/20` 分别是“腿”和“核心”，只统一处理风格，不把不同源ID的
文字盲目复制成同一个词。`Skill_Name_00/Effect` 的最后一项也不同，按各自真实
字段保留文字，匹配项共享字高/字体及右对齐。

阿巴泽特与无反馈邻片相连的两段保留上一轮完整共享排字；不能只换半个词。
`원수의 언덕` 的语义待证状态不因字体返工而自动解除。

## 可复现构建与字体来源

新增Noto Sans CJK SC Bold及Noto Serif CJK SC Black开发输入，上游提交、URL、
字节数与SHA在 `locales/zh-Hans/texture-overlays/review-v3-font-sources.json`。
沿用SIL OFL 1.1；字体二进制不进入Git。原有Regular/SemiBold仍须按各自描述符准备。

```powershell
python -m unittest discover -s tests -q
python -m tools.compact_outputs --root build --check-space-only
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW_V3_DISC1
# Disc2同法，保持 --disc 2 和独立目录。
python -m tools.build_image_review --inventory build/phase-318-feedback-rework/review/manifest.json --revision locales/zh-Hans/candidate-decisions/image-review-feedback-v2-20261026.json --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json --bundle build/phase-319-review-v3/disc1-texture-bundle-final --bundle build/phase-319-review-v3/disc2-texture-bundle-final --output build/NEW_V3_REVIEW
```

## 审查页和收尾证据

通用审查器通过显式 `review_round=3` 区分存储命名空间、页面标题和CSV文件名，
仍支持旧描述符缺省第2轮。左右键全局捕获、取消光标移动、翻页后聚焦反馈框的
交互不变。源JSON继续按文本显示并转义script结束符。

本轮实际命令、退出状态、原生验证、隔离回滚、既有测试副本增量刷新和远端身份，
以 `build/phase-319-review-v3/VERIFICATION.txt` 为完成证据；草图不是最终审查图，
离线验证不等于用户艺术验收或游戏内验收。
