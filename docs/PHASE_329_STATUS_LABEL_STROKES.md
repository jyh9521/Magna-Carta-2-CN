# 阶段329：属性字图断笔修复

## 范围

用户圈出的 `Common_State_Tex` 六层：武器、耐力、两个饰品、抗性、耐力恢复。
对应 `img_ui_name_jpn_157_{2,8,9,10,11,12}`。只改这六个区域；
同图其余七层、其他图片、动态朱雀仿宋500字库、字幕、译文和可执行文件不变。

两处物理别名分别为：

- `MC2Game.xxx / UI_Name_Jpn.Tex.Common_State_Tex`
- `UI_Name_Jpn.xxx / Tex.Common_State_Tex`

## 原因与修复

**Verified（离线）**：旧计划中有7处明显的孤立暗色谷值，直接进入笔画填色。
旧BC3最远颜色对编码也会把细笔画量化到较暗的中间色。
自有双竖线夹黑边夹具中，笔画红通道最低值从预期250以上降到172，
形成错误暗段；显式新编码回读为255。不是alpha缺失或UV越界。

**高可信推断**：旧逐行颜色测量混入了原字的抗锯齿/描边颜色。
没有把这种取色污染当作原作故意断笔，也没有更换字族掩盖问题。

修复计划：`locales/zh-Hans/texture-overlays/status-label-rgb-repair-v1.json`。

1. 引用并锁定已有v7计划，只去掉明确列出的13个内部渐变取样点，
   由其余原有色点插值，去除7处暗谷及相邻受污染的过渡点。
   保留原白色高光、金黄、橙色端点及所有剩余色点；不是整张图统一换色。
2. 字体仍为原有Noto Sans CJK Bold；字形、字号、字距、墨迹框、位置、
   描边/阴影/光晕参数完全不变。图片字不采用动态文字的朱雀仿宋。
3. 六个区域显式采用 `weighted-fit-v1` BC3 RGB端点拟合，
   以旧编码为初始候选，固定迭代次数，只接受alpha平方加权RGB误差更小的结果。
   默认编码路径、原缓存键、BC1行为均不变。
4. 原生块的alpha前8字节逐块保留；两份导出的整图alpha回读逐字节相同。
   256×128尺寸、格式、mip、UV及非选中导出不变。每个别名只改变六区内475块。

原生编码是有损的：保留风格/参数不等于声称每个RGB解码像素无损。
六层相对修正后未压缩绘制的RGB误差均下降，具体数值在构建报告中。

## 复现与验证

输入是阶段328最终规范化资源，不从旧字体底包重画整个包。
新工具只读取源文件，输出到新的目录；未知输入哈希、几何、重叠区域或越界写入会失败。
阶段328的重建步骤见 [PHASE_328_DYNAMIC_FONT_AND_TEXT](PHASE_328_DYNAMIC_FONT_AND_TEXT.md)。
将其两份最终资源按本阶段JSON中的路径放入 `baseline-resources`，先核对：

| 资源 | 输入SHA256 |
|---|---|
| MC2Game.xxx | `caa488fc8fa927cdaff5761c0c9c370f568be4bf5db50ab68b19f65121a18eb5` |
| UI_Name_Jpn.xxx | `64d2de80e4c47824753641c4c904ec73baef848dde79b81a83098be4576f8b33` |

```powershell
$p = 'build/phase-329-status-label-repair'
$recipe = 'locales/zh-Hans/texture-overlays/status-label-rgb-repair-v1.json'
python -m tools.repair_texture_labels --recipe $recipe --lzx-library build/lzx/native-verified/ue3_lzx.dll --output "$p/final-resources"
python -m tools.repair_texture_labels --recipe $recipe --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root "$p/final-resources"
python -m unittest discover -s tests -v
```

本地 `CHECK.py baseline` 返回1并复现7处暗谷/细线172；`CHECK.py modified`
返回0并核对六层、两个别名、暗谷0/细线255、原生alpha与范围外块不变。
`ROLLBACK.sh` 在另一个资源副本上执行逆向原生块替换，两份文件恢复完整输入SHA，
当前修改候选保持不变。它不是对两张完整ISO另做复制回滚。

只提交工具、配方、测试及文档。完整资源、原生预览、输入、回滚副本与执行记录位于
忽略目录 `$p`，四项入口为 `MODIFIED_FILE.json`、`DIFF_FILE.patch`、
`VERIFICATION.txt`、`ROLLBACK.sh`。

## 交付与人工复测

这次用户明确要求覆盖测试ISO，采用 `repair_disc_image prepare-refresh`，
以前驱阶段328 `disc{1,2}-refresh-final/plan.json` 为锁定输入，
仅追加两包和TOC并刷新原文件目录字段，不生成另一份整盘镜像。
新的可逆事务保存在 `$p/disc{1,2}-refresh/plan.json`。
原有文件夹入口也通过 `compose_incremental_comparison` 和 `refresh_oneclick_probe`
同步刷新，保留配置、原文对照、存档、runs以及所依赖的历史资源。

未启动游戏。玩家需检查装备/属性界面六处字图在实际缩放和选中状态下的连续性，
并确认其余字图与原有白金橙渐变、描边和阴影观感一致。

## 本轮交付记录

全套2,450项测试通过，其中1项按原条件跳过；两份包独立重建字节相同，
真实资源隔离回滚恢复输入哈希。输出包SHA256：

- MC2Game.xxx：`a87c10ef28441d6abf9529ca4464f750c73ce8a3a44ba6b71ce2e4af13abab11`
- UI_Name_Jpn.xxx：`873e2c72c991b24194eb0a326ba3c12df8c25c1f1dde7cc69a19f04c31bc15c1`

原路径 `dist/MC2-test-iso-v6/` 下两张ISO均已原位刷新，完整SHA256：

| 文件 | SHA256 |
|---|---|
| MC2-Disc-1-zh-Hans-test-v6.iso | `1506b99fcaf7c8047d21c1bee6caf4658e3a0729508f7cd82161f910fdf06d5f` |
| MC2-Disc-2-zh-Hans-test-v6.iso | `61bfe8bb48b22c1b689224c7939078d1bf80284586acb2dd2e09635553f18bfc` |

两盘2016/2340个活动文件、TOC及逆向原前缀摘要全部通过。
文件夹入口同步两包，419项候选及原文对照资源在清理后复核通过。
删除98个确认可再生成的中间文件，合计2,244,409,368字节（约2.24GB），
包括阶段328此前未删除的89项；完整清单和逐文件哈希留在本地清理报告中。
原盘、配置、存档、runs、活动包依赖、基线和必要回滚证据保留。
