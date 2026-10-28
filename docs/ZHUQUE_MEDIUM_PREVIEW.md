# 朱雀仿宋轻度加粗预览（阶段327，2026-10-28）

用户选择朱雀仿宋，并要求先看接近Medium 500的轻度加粗效果。本轮仍是离线预览，
未采纳到游戏；字幕/动态文字以外的绘制素材、字库包、ISO与运行配置均不改。

## 字体和加粗含义

沿用阶段326的 `ZhuqueFangsong-Regular.ttf` v0.212，SHA-256：
`558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4`。
直接读取该文件确认 `OS/2.usWeightClass=400`、UPM=1000、无fvar轴；
不把修改字重标签或CSS500当作已有的真正Medium字形。

本轮的500明确标为**合成预览目标**，不是上游原生Medium字体。
用Pillow 12.2.0的浮点 `stroke_width` 重新栅格化FreeType轮廓，
半径为 `font_size × 0.006`。源字体文件、字体内部名称和字重字段完全不变。
这是可复现的轻度轮廓扩张，不是抗锯齿位图模糊、白色外发光或新的黑色描边。

API及实现依据：[Pillow ImageFont文档](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getmask2)、
[Pillow 12.2.0 FreeType调用](https://github.com/python-pillow/Pillow/blob/12.2.0/src/_imagingft.c)。
后者通过 `FT_Stroker_Set` 设置以1/64像素量化的半径，并在栅格化前处理字形轮廓。
选择0.006em是本次视觉预览参数，不宣称存在从400到500的通用数学换算。

## 同条件对比

继续使用阶段326的同一段游戏对白、原换行和三档字号。对比仅改变白色字形的粗细；
不改变字距、advance、共同基线、可见格高、正文颜色、行距或27px字幕的1px右下黑影。

| 字号 | 请求的轮廓扩张半径 | 栅格alpha总量比原版增加 | 边界丢弃增长采样 |
|---|---:|---:|---:|
| 15 px | 0.090 px | 约25.2% | 0 |
| 22 px | 0.132 px | 约24.0% | 0 |
| 27 px | 0.162 px | 约24.0% | 0 |

**Verified offline**：同一37字样本的六组栅格无缺字、原前景裁切为0；
三组加粗样本的增长也没有越出可见字格。加粗前后glyph plan、baseline记录和advance完全相同。
新工具的Regular分支与保存的上一版工具逐字RGBA摘要一致；Medium三档均发生真实像素变化。
先保留原alpha，再加入轮廓增长，最后执行与上一轮相同的BC3与字幕阴影流程。

完整字库覆盖、全量排版和游戏内着色器效果不由本次37字样本证明。未创建新字体文件，
未改原有图片或视频；页面与PNG标题明确写出“合成预览”。

## 重建与验证

```powershell
python -B -X utf8 -m tools.render_font_comparison --profile locales/zh-Hans/font-preview-zhuque-medium.json --output build/zhuque-medium-preview-new
python -B -X utf8 -m unittest discover -s tests -p test_render_font_comparison.py -v
```

依赖沿用前一轮，不下载另一份字体。新配置的两个样本引用同一源文件和相同SHA；
只有第二个样本启用 `embolden={target_weight:500,stroke_em:0.006}`。
未指定该字段的所有旧配置保留原像素；非法、非有限、过大或只改标签的参数明确失败。

当前结果在 `build/phase-327-zhuque-medium-preview/previews-final/`：

- `00-comparison-1x.png`：Regular 400与合成500的三档总览。
- `01-Zhuque-Regular-400-{1x,2x}.png`：原版深浅背景对照。
- `02-Zhuque-Medium-500-preview-{1x,2x}.png`：轻度加粗深浅背景对照。
- `index.html`、`manifest.json`：预览入口、字形指标、真实字重/合成目标和像素摘要。

保存原工具哈希，以修改后的工具副本验证像素变化，再在另一个源码副本上回滚并重放，
确认Regular像素恢复，同时保留修改版。证据、差异和可执行回滚入口分别为
同级目录下的 `MODIFIED_FILE.py`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`。
回滚只针对隔离源码副本，不触及当前工程工具、字体、游戏或最终预览。
