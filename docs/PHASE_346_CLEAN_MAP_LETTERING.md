# 阶段346：地图字形、轮廓、投影与底图分层重建

## 范围与来源

本轮对应用户连续指出的英文上方暗带、旧字阴影、贝尔福特尾部残留、
阿巴泽特过重投影，以及风息岛漏换字体。覆盖原地图清单的49图组、
82份物理纹理、42份资源：269条中文记录中的12条贝尔福特清理尾片并入
主标题，形成257个重建区域；44组英文全部覆盖。地图内部小地名、
房间名也重新生成文字效果，不仅处理用户截图中的几个大标题。

发布基线是阶段344的已发布 v1.0 资源及安装器。阶段345是被反馈否定的
未发布候选，不能当成已经通过的观感验收；其图、代码和失败方法保存在
`build/phase-346-clean-map-lettering/rejected-v18/` 及原阶段345证据目录。
既有测试目录曾刷新到阶段345，最终刷新会验证其实际 PREPARED 身份，
而不是假定它仍等于发布基线。

## 已验证的根因及废弃做法

旧 `isolate_original` 按与英文/韩文亮像素的距离分配原图暗像素。
两种文字的阴影相邻时，距离不等于阴影归属；最小复现会带入52个
与英文无关的黑影像素。把这种提取结果再当成“正确阴影蒙版”审计，
只能证明生成器与自身一致，不能证明画面干净。原始压缩前 RGBA 中
已经有这些像素，不能将问题归咎于截图缩放或BC3本身。

## 新的可复现方法

通用实现是 `tools.lettering_layers`、`tools.rebuild_texture_titles` 和
`tools.audit_texture_titles`；字体、文字、坐标和效果参数在
`locales/zh-Hans/texture-overlays/map-lettering-v19.json`。

1. **中文字形**：在透明画布上重新栅格化。大标题沿用杜南丘陵所用的
   `NotoSerifCJKsc-SemiBold.otf`；风息岛上下片使用同一个204×92画布、
   同一32像素字高、字体、渐变、锚点和效果，最后切片。小地名保留
   各自既有字体和排字规则。已修正的渐变暗行不从旧计划重新带回。
2. **英文墨迹**：保留原纹理的采样位置、字形、大小和颜色贡献，不换
   英文字体，也不重新排字。只在明确的英文墨迹框内，以每行亮度峰值
   对 `RGB × alpha` 解黑色衬底；纯黑alpha、框外像素和字符空隙中
   不邻接实际墨迹的弱RGB565杂色不作为字形。没有复制原图黑色投影。
3. **轮廓与投影**：只从干净字形alpha生成。轮廓用4倍双线性采样，
   避免滤波振铃；投影从字形而非矩形或扩张轮廓生成。低于3/255的
   投影尾部归零，效果支撑域限制在字形周围3源像素，不裁成直线暗带。
   阿巴泽特使用更轻、紧凑的英文投影；La Strada保留原版较明显的
   英文轮廓。其余标题按原图色调与层次作视觉近似，不声称新阴影与
   原作者的笔刷逐像素相同。
4. **地图底图**：大标题区域从全透明底重建，绝不复用旧覆字修补图。
   小地名的旧去字层也单独关闭文字检查：阿巴泽特港口、草原、荒野森林
   和青灵森林的旧修复层确实保留了韩文字尾，不能把旧底图全部当作
   审计白名单。当前计划逐项声明保留的地图/引线区域，其余旧底图像素
   清零；房间标记的真实光晕独立保留。五种与地形相交的布局（含风息岛
   海岸，两种地图副本共七处）使用 `tools.map_underlay`，只采样已核查的
   上下干净行，按地图边界插值估计被原字遮挡的局部地形，已露出的右侧
   地形按显式区域保留。该估计不声称恢复原作者隐藏的地形细节，不复制
   区间内的原字或旧阴影；测试替换整个区间的黑/白字仍须得到相同底图。
   写集外原生块和其他export保持原字节。
5. **原生回读**：重新编码Xbox BC3后再审查，不只看编码前PNG。
   透明像素必须仍为零alpha；alpha误差上限24/255，标题预乘颜色
   上限48/255，地形混合区域上限64/255。超过预算的RGB块使用显式
   minimax细化，alpha块不变；没有全局改变旧编码器的默认行为。

## 对齐与独立验收

`texture-alignment-audit-v19.json` 继承逐项左/右/居中合同，以及菜单
图标/其他行的保护合同。英文效果按本轮要求变化，因此旧版“整个
英文矩形逐字节不变”的合同由原始英文墨迹的预乘颜色、位置/大小检查
替代，而不是继续要求被用户要求修改的投影不变。

阴影清洁审计不以生成后的阴影图作许可蒙版：它只使用字形墨迹、固定
距离上限及独立地图底图检查负空间；跨纹理字形的支撑域先拼接再切分。
回归测试故意添加孤立黑点并同步伪造生成器自己的结果摘要，独立审计
仍须失败。另有纯黑污染、字符间RGB杂色、源/字体/纹理SHA、不相交
输出、重复资源、BC3读回与双盘manifest测试。

最终底图复查在关闭全部新文字时单独进行。仅按亮度数黑像素会把地形
轮廓和房间标记算作残影，因此先查看完整原地图确定真实美术元素，
再核对81种独立小地名底图；没有将所有暗像素粗暴删除。首次文字层
通过后的中间提交和安装包仍保存在本轮 `underlay/`，最终交付身份
以 `VERIFICATION.txt` 为准。最终资源、packet、recipe 与 bundle 位于
本轮 `final/`，不再指向首次文字层检查的中间候选。

全部比较图在 `build/phase-346-clean-map-lettering/review/index.html`，
风息岛两片合并显示。原尺寸、整数倍放大、浅色/深色/棋盘底图及
单独字形/轮廓/投影图用于离线检查。实际游戏内缩放仍由原测试入口
复测，`game_rendering_verified=false`。

## 重建与收尾

```powershell
$e='build/phase-346-clean-map-lettering'
$p='locales/zh-Hans/texture-overlays/map-lettering-v19.json'
$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.rebuild_texture_titles --profile $p --profile-sha256 $h `
  --project-root . --source-root "$e/baseline" --output "$e/rebuild" `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -B -X utf8 -m tools.audit_texture_titles --profile $p --project-root . `
  --baseline "$e/baseline" --actual-root "$e/rebuild/candidate" `
  --reference "$e/final/modified/manifest.json" --lzx-library build/lzx/native-verified/ue3_lzx.dll `
  --report "$e/rebuild-audit.json"
```

`input-resources.json` 将阶段344 recipe逐项核验后物化为42项稀疏基线，
不是整套游戏副本。字体及原盘输入继续由现有来源锁提供；新计划包含
完整文字/效果数据，不依赖被废弃候选的旧生成代码。

同版本安装包仍使用 `dist/MC2-CN-v1.0.exe`；测试目录只做哈希守卫的
增量刷新，保留配置、存档、runs、原盘与回滚依赖，不启动游戏。
完整的基线/修改/隔离回滚命令、字面输出、退出码、成品SHA、独立重建、
清理、提交推送及同提交四组Actions状态以本轮 `VERIFICATION.txt` 为准。
