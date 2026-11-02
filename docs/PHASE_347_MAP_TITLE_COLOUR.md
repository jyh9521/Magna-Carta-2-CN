# 阶段347：恸哭之门的原图配色修正

本轮仅处理 `Map_View_Oldfox.xxx / Map_View_Oldfox` 中的
`normal_map_terrain_map_view_oldfox_02`。双盘使用同一资源；字号、字体、
位置、字形alpha、轮廓、投影、底图与其他地图文字不变。

## 已验证

阶段346候选的颜色表在826..1000处重新变成灰白，编码前字形已出现
灰白底边，故不是截图缩放或BC3才产生的偏色。原图局部第25行起的
白色地图引线含这些中性色；原字形实际下端仍为橙红/深红。

本轮只在已核查的原字形范围内取色：局部x=7..81、y=7..25；alpha
至少235、R至少90。下半段y>=16额外要求R>=1.4G且R>=2B，排除引线；
各行取R峰值12以内的样本均值，按19个源行归一化至0..1000渐变。
原图、源像素位置及RGB、前后颜色表记在
`locales/zh-Hans/candidate-decisions/map-title-colour-20261102.json`。

完整重建计划 `map-lettering-v19.json` 只更新此层的
`label.appearance.gradient`；其余数据深比较不变。增量计划
`map-colour-v20.json` 以阶段346实际安装资源SHA为输入，限定一份资源、
一个纹理、一个92×32区域。通用渲染器与BC3编码器无需改动。

## 复验

新增回归测试使用自有矩形字形，走生产 `font_ink` 和 `effects` 路径：
旧颜色表使下端红色测试失败；新表通过；颜色改变不影响字形alpha和
独立轮廓/投影图层。实际中文字芯下端83个高覆盖像素由0/83红色变为
83/83红色，整张原生纹理alpha与区域外RGBA逐像素不变；其他export和
区域外原生块字节保持。全部257区域和41组对齐继续检查。

```powershell
$p='locales/zh-Hans/texture-overlays/map-colour-v20.json'
python -B -X utf8 -m tools.rebuild_texture_titles --profile $p `
  --profile-sha256 (Get-FileHash $p -Algorithm SHA256).Hash.ToLower() `
  --project-root . --source-root build/phase-347-map-title-colour/baseline `
  --output build/NEW_COLOUR_REBUILD --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -B -X utf8 -m unittest discover -s tests -p test_map_title_colour.py -v
```

阶段346的安装包和一份资源保存在本轮基线中；只增量刷新既有测试路径，
不启动游戏。安装包仍为 `dist/MC2-CN-v1.0.exe`，不改变版本号。
本轮三列原生对照在 `build/phase-347-map-title-colour/comparison.png`；
`review.html` 复用上轮未变化的图，仅替换此项，不改写历史证据。
安装包、三态检查、独立重建、清理及同提交CI身份以本轮
`VERIFICATION.txt` 为准；游戏内验收与离线检查分别记录。
