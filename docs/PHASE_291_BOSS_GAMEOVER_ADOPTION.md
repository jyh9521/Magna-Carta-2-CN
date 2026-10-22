# 第291阶段：BOSS与战败图片实际汉化

## 采用范围

本轮实际增加15张BOSS标题及2张战败图片，共17图/双盘75个真实Texture2D别名；与已完成47章图合为 **64图、65个文字层、双盘348别名**。文字层比图片多1，因为“按”和“键”分居原A按钮两侧。D1当前纹理源19包、D2为17包，并集23；完整资源比较包两盘均45成员。INT仍batch121/14159；七Font和315字幕不改。

新图译名、JPN/INT一手字段和已采用批次见[名称裁决](PHASE_291_BOSS_GAMEOVER_LABELS.md)，结构化采用为 `locales/zh-Hans/candidate-decisions/boss-gameover-image-labels.json`。完整别名调查见[4145包调查](PHASE_291_BOSS_GAMEOVER_ALIASES.md)：除UI_Title/Jpn和MC2Game/UI_GameOver，D1另有五个Boss地图resident，不把import/header预筛当导出。D2的Map13只是字节预筛误命中。新增角色全名仅为有证图片草稿，不冒称官方中文。

新累计计划为 `locales/zh-Hans/texture-overlays/ui-labels.json`；旧 `chapter-entry.json` 仅保留47章图历史profile用于独立重建/回读；后续译文回填以新累计计划为准，不再向旧profile追加。15个中文Boss标题替换原日/韩标题与重复拉丁小注，包含“守护者”“攻略目标”等语义，不只填短名；贝里艾尔沿用已采用正字。普通Boss采用珊瑚红文字/暗红描边，攻略目标暖金，三张有翼饰的韩文标题保留翼饰；游戏结束采用白红字体，不复刻原字形书法。新17张实际BC3编码后逐图目检，62张Title文字图（章47+Boss15）及战败两图均纳入候选。

## 不重画控制器符号的通用实现

`tools.texture_overlay` 为同一Texture2D新增明确的`regions`文字层列表与`image_id`，保留旧`label`单区域计划/报告字节兼容。多层最多16，严格拒绝重复ID、缺层、区域重叠、未知保护键、不对齐/越界/错误源hash。只有一个最终payload追加/导出表重定位，不用重复同导出对象的补丁绕过保护。

`protected_regions` 记录独立原像素crop SHA。工具先验证保护区与修改区/其他保护区没有共同BC3块，再分别证明原块相同及解码RGBA crop逐字节相同，未知或不匹配输入即失败。新`image_groups`与`labels`分别计图片和文字层，不把两个按钮侧字算两张图。

Notice_tex明确只改`[40,12,68,40]`和`[144,12,80,40]`，分别绘制“按”“键”。原绿色A/边缘/阴影整列`[108,0,36,64]`保留，保护范围比实际绿像素bbox更大；不以新字母A或AI图像替换控制器图形。三张翼饰分别在计划中锁定两侧保护区。所有保护均在每个resident/standalone别名验证，不只看一份PNG。

PNG的透明背景可能带有非零RGB：原Notice像素`(192,79,54,0)`不是要画到游戏里的不透明橙色底。预览使用实际RGBA在深色底合成，不能只看RGB就盲涂背景。BC3文字仍为确定性有损量化；修改区域外原块、对齐padding与未选导出保持，运行blend/采样/加载优先级仍留游戏验收。

## 构建与输入恢复

既有Noto字体来源/OFL和Font底包流程不变。每张图片的源资源/payload/tiled/尺寸/保护crop hash都在计划中；中文文字来自locale数据，通用工具不认识Boss名或A按钮含义。

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-291-verification/disc1-texture-bundle
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-291-verification/disc2-texture-bundle
```

首次构建用新目录与`--output-dir`；manifest/hash分别绑定到对应locale-compositions，仍独立验证每盘原资源。原始输入可按[上一轮精确提取代码](PHASE_290_COMPLETE_CHAPTER_TEXTURES.md#原始小资源的精确恢复)恢复：只将计划路径换成`texture-overlays/ui-labels.json`，资源数为23（不是17），其余hash/路径/已有文件不覆盖规则相同。只提取23个选中小资源，不复制整游戏；Font候选仍按固定字体流程生成。原包/字体/PNG不入Git。

## 收尾与后续

旧测试目录D1显式增加6资源（五Boss地图+UI_GameOver）；D2仅离线包，新增UI_GameOver1资源。默认同集合保护保持，旧原文对照、配置、存档、runs和原XEX保留。隔离迭代回滚恢复旧47图/39资源检查点，新加源回到原件；当前canonical/live保留64图。回滚/基线/修改/清洁源码、旧计划独立回读、348别名实际预览一致与推送证据见 `build/phase-291-verification/VERIFICATION.txt` 和四项交付。

接续：其余UI/角色名/怪物名/游戏开始/教程图，111不支持纹理导出、不同名/动态别名与原生硬编码可见文本；未知UI/성쇄仍只凭新证据推进。完成本组不是全部汉化或游戏内验收完成，仍不启动游戏。
