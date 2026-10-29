# 阶段330：动态数字的光学比例

## 用户反馈与最终选择

2026-10-29 的无存档截图显示，朱雀仿宋的数字明显小于汉字。
本轮第一份放大预览又被用户明确指出“2太大”。该预览已撤下，不作为当前候选。
最终仍用已选朱雀仿宋的数字轮廓，降低到略小于汉字的墨迹高度并校正基线；
不换汉字字体，不修改原始 TTF，不混用另一套阿拉伯数字。

字体仍为已锁定的 v0.212 Regular400，合成500采用既有 `.006em` 轮廓扩张，
不是上游原生500字体。输入 SHA256 保持
`558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4`。

## 已验证的根因及改动

旧配置为了容纳拉丁重音字符，将 U+0000..00FF 统一降为 12/18/22px。
数字也落入这个区间，实际字芯只有汉字约一半高度。仅改变数字的光学字号，
即可修复，不需要改游戏的全局缩放或替换整套字库。

`dynamic-font-numerals-v9.json` 只选取三角色全部已映射十进制数字：
`0123456789１`，覆盖四个包、七个 Font 别名，共77个字形。
原 remap、全部非数字度量和字形像素保持；图片数字、图标字体和伤害数字美术字不改。

| 角色 | 汉字栅格字号 | 最终数字光学字号 | 数字基线微调 | 数字可见高度 | 参考汉字中位高度 |
|---|---:|---:|---:|---:|---:|
| SmallFont | 15 | 20 | -1px | 11–12px | 14px |
| General_15 | 22 | 28 | -2px | 17–18px | 20px |
| EngineMedium_Subtitle | 27 | 34 | -2px | 21–22px | 24.5px |

表中可见高度来自实际 Xbox BC3 字形回读，前景 alpha 门限80，排除黑色字幕阴影。
参考为截图中的“真名法典”四字；字号不等于字芯高度。
数字与参考汉字下边缘的差值不超过1px。数字实际 advance 只在原格装不下时增加，
全角１仍保留全角 advance，后续全文行宽检查使用修改后的真实度量。

通用 `reface_font` 新增显式 `baseline_offset`，缺省0的输出保持原样。
该字段只接受有界整数；越出字格或裁切扩张轮廓的值会失败。
字格高度、现有中文映射及其非选中 atlas 不改。

## 验证和复现

```powershell
$p = 'build/phase-330-gameplay-qa'
$profile = 'locales/zh-Hans/dynamic-font-numerals-v9.json'
$hash = (Get-FileHash $profile -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.build_font_reface --profile $profile --profile-sha256 $hash --source-root "$p/baseline-resources" --output build/numerals-v9-rebuild
python -B -X utf8 -m tools.audit_font_optical_size --root build/numerals-v9-rebuild/candidate --profile locales/zh-Hans/font-numerals-audit-v9.json --before-root "$p/baseline-resources" --output build/numerals-v9-audit.json
python -B -X utf8 -m unittest discover -s tests -p test_font_optical_size.py -v
```

基线的77个数字均不满足最终比例条件；候选77个均满足。
检测同时检查数字相对高度和下边缘，而非只比较 font_size。
所有非选中映射的度量逐项相等；修改 atlas 内的非数字逐字原生像素相等，
其他 atlas 的完整导出 payload 相等（不把压缩原字库误当未压缩图像解码）。
两次独立构建的四份包逐字节相同。

本地 `font-balanced.png` 是从实际游戏字格按真实 advance 合成的3倍近邻检查图，
不是游戏截图，也不是另外用 TTF 模拟的预览。最终比例的离线验证不代替玩家对
真实缩放、布局和整体美观的验收。完整批次集成、三态恢复和交付记录见阶段330总记录。
