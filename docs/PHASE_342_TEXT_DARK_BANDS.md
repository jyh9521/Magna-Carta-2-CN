# 阶段342：文字横向暗带，保持大小与位置

## 用户边界

本轮只检查、修复截图“晶柱”所代表的文字黑线/假断笔。不改译文、字体、字号、
字距、字形覆盖、UV、控件坐标、按钮和其他布局；不重建安装器、ISO或完整游戏副本，
不启动游戏。沿用原测试目录。阶段340/341已接受的排版继续保留。

## Verified：复现与分类

截图已原样保存并核对 SHA256：
`cba57703281d826990771d92f92b3ea4b2158b0b6773cc069cae3fdd7c4de6f0`。
截图放大与当前原生 `Pillar.Piller_Menu_Title` 回读有相同横向暗带。
`img_ui_name_jpn_136_5` 的字图仍是 `[36,172,200,36]`，墨迹框仍是
`[3,4,194,26]`。源渐变704、963两处暗点进入笔画；原生局部第22行
完整笔画红通道均值约180.86，邻行明显更亮。alpha没有断裂，不是文字位置或裁剪错误。

三种原因分别检查：原生alpha缺口、背景残留、笔画RGB暗段。
本次证据支持最后一种。渐变取色混入原字描边/抗锯齿是**高可信推断**，
并非已经取得原取色程序的运行轨迹。BC3端点/索引量化造成额外暗段可由自有夹具复现。

盘点当前1,599个文字层，其中1,383个是可重放的生成字形；216个原图保留/独立美术层
单独计数，不拿平滑算法改写它们。渐变初筛131项，另有111项原生量化候选（存在重合）。
逐项查看原生放大图后，最终明确列出213个文字层，涉及170个逻辑图片、471份物理纹理、
190份资源包。首轮129层去掉显式列出的异常取色点，84层只重拟合指定原生行；
正常宽渐变和美术字的设计暗部保留。两盘相同路径的当前资源摘要逐项核对后共享修订，
盘独有路径仍保留盘身份。

筛查是发现候选，不是自动批准修改：

- 孤立渐变谷值使用既有20级红通道阈值；相邻锚点覆盖最多3.25个字芯像素。
- 量化筛查要求至少3个高覆盖笔画采样，行中位亏损至少20、相对相邻行多15。
- 字形笔画本身的空隙、正常由白到灰/金/橙的渐变，不按“看见暗色”直接删除。
- “返回标题”的700/750/800为连续污染段，必须连同邻接污染点修复，不能只拔掉谷底。

## 实现与不变量

`texture-overlays/text-dark-bands-v15.json`锁定阶段341实际输入、各原生tiles、
既有字形计划及字体摘要。它不是对历史v9计划的大范围覆盖。
`texture_dark_bands`仅计算相同字形的RGB修订；已有背景不被透明重绘替换。
写集只包含明确暗带及一行相邻保护范围所触及的BC3块。

端点拟合复用既有确定性拟合器。仅在本次修订中提高字芯采样权重，
并避免给高覆盖字芯选择比目标最大色通道低16级以上的暗插值项。
保留拟合端点，索引在现有四个颜色中选择；不是改全局解码器或所有图的默认编码。
每个块仍需相对当前原生输入改善加权RGB误差，否则保留原块。
BC3是有损格式：不声称共享块中所有RGB像素无损，也不将正常渐变本身当作黑线。

**严格不变：** 每一块原始8字节alpha、整图解码alpha、纹理尺寸/格式、
字形计划中除指定取色点之外的字段，以及所有包内非授权RGB字节。
审计将候选的授权RGB字节换回基线后，要求整个文件逐字节等于基线，
因而坐标、UV、字体指标、动态字库、正文、其他纹理和元数据的变动都会失败。
原生alpha全相同是大小/位置/轮廓不变的证据，而非只比较名义字号。

## 可复现入口

基线来自阶段341已验证的双盘recipe；按配方路径放置源锁定的190份资源。
其前序构建见[阶段341](PHASE_341_BUTTON_VISUAL_CENTER.md)。完整游戏资源只留本地。

```powershell
$p='locales/zh-Hans/texture-overlays/text-dark-bands-v15.json'
$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.repair_texture_dark_bands --profile $p --profile-sha256 $h `
  --source-root build/phase-342-text-black-lines/baseline `
  --output build/phase-342-text-black-lines/rebuild
python -B -X utf8 -m tools.audit_texture_dark_bands --profile $p `
  --baseline build/phase-342-text-black-lines/baseline `
  --candidate build/phase-342-text-black-lines/rebuild/candidate `
  --expected build/phase-342-text-black-lines/rebuild/manifest.json `
  --title-label img_ui_name_jpn_136_5 --report build/phase-342-text-black-lines/rebuild-check.json
```

全量只读筛查使用 `tools.screen_texture_dark_bands --profile ... --recipe ...
--recipe-sha256 ... --report ...`；已应用本轮修订的recipe需加`--apply-revision`。
输出仅为待查看候选，不能拿阈值结果自动批量改图。
针对性测试：`python -B -X utf8 -m unittest discover -s tests -p test_texture_dark_bands.py -q`。

本地三态、源测试、完整包摘要、双盘归属和增量刷新证据放在
`build/phase-342-text-black-lines/VERIFICATION.txt`。
`ROLLBACK.sh`只在新建隔离副本逆向还原本轮RGB差异；原输入及当前修改候选保持。
离线原生回读、放大预览和游戏内验收分列；最终实际缩放/着色器观感由用户复测。

## 用户追加的三处修正：v16

用户在首轮原生预览中指出“世界地图”“商店”仍有黑线，“购买”左侧描边不完整。
因此首轮筛查不作为视觉验收；本次追加只改这三个已有文字层，其他修订保持。

Verified：前两项的源渐变含**连续两个等暗取色点**，不是单点谷底。
“世界地图”为815/852，“商店”为556/593；首轮只重拟合原生行而未删除这些取色点，
所以暗段仍被源计划要求保留。窄暗段筛查现包含等暗平台，仍保留原20级/3.25px阈值，
不把宽渐变自动批准为修订。

| 项目 | 原生局部采样 | 追加前 | 追加后 |
|---|---|---|---|
| 世界地图 | 第26/27行高覆盖字芯R均值 | 137.50 / 132.57 | 253.40 / 252.71 |
| 商店 | 第17行高覆盖字芯R均值 | 192.55 | 255.00 |
| 购买 | x=37、y=20..23外缘RGBA，各4点 | (57,60,57,147) | (0,4,8,147) |

“购买”不是缺失alpha或要加宽描边，而是已有描边的BC3最低色级偏亮。
`restore_outline_rgb`只在显式指定的字层中重拟合亮色污染的暗描边块；保留原alpha，
不扩大字形/描边、不改字体、字号、矩形、墨迹框、字距或位置。其余字芯渐变保持。
BC3共享色板仍是有损格式，不承诺一个选中块的所有RGB像素逐像素不变。

`texture-overlays/text-dark-bands-v16.json`锁定首轮成品中的4包5份纹理；
`text-dark-bands-v16-audit.json`检查上述原生行与外缘点，避免连续暗行再次逃过单行判据。
追加修订总共改变**320个RGB字节**；包内其余字节、每块alpha、所有位置/尺寸均逐字节保持。
双盘8项身份核对通过，另外的既有资源须与首轮recipe相同。
三态为9项失败 → 0项失败 → 隔离还原后9项失败，回滚脚本返回0且修改候选仍保持修改。
4包独立重建的manifest和文件均逐字节一致。

```powershell
$p='locales/zh-Hans/texture-overlays/text-dark-bands-v16.json'
$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
$e='build/phase-342-text-black-lines/followup'
python -B -X utf8 -m tools.repair_texture_dark_bands --profile $p --profile-sha256 $h `
  --source-root "$e/baseline" --output "$e/rebuild-new"
python -B -X utf8 -m tools.audit_texture_dark_bands --profile $p `
  --baseline "$e/baseline" --candidate "$e/rebuild-new/candidate" `
  --expected "$e/rebuild-new/manifest.json" --title-label world_map_header_title `
  --rgb-checks locales/zh-Hans/texture-overlays/text-dark-bands-v16-audit.json `
  --report "$e/rebuild-new-check.json"
```

输出目录必须为新目录。追加证据以`followup/VERIFICATION.txt`为准；
`followup/before-after.png`来自最终成品原生回读，不是模拟游戏截图。
首轮及追加的原始包/修改包/隔离回滚副本保留，重复重建包只在摘要复核后清理。

本地最终2790项测试通过（跳过2项）；原始/隔离回滚源码各2778项通过。
追加增量刷新改变4个游戏资源及3个入口/摘要文件；前轮布局20项、存档153项、
7字库77数字字形和DLC检查均通过。127个受保护文件摘要不变，包括原安装器。
最终提交、推送前干净源码检查及同提交四组Actions结果记录于上述VERIFICATION；
本地测试或远端SHA一致不替代四组云端结果。
