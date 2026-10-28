# 动态文字字体对照预览（阶段326，2026-10-28）

## 本轮交付与边界

本轮只生成五款真实字体的离线排印预览，不选择或部署字体。用户指定第一款采用
**霞鹜臻楷 Slab GB**，不是已停止维护的无后缀臻楷。后续若采纳，只面向剧情字幕
和动态文字；既有绘制素材、菜单图、载入影片、地图图集全部保持原样。

不重建字库包，不刷新测试目录或 ISO，不启动 Xenia。新反馈中的“切换目标”字号、
手柄图残留、“已获得”间距、游戏名统一为“真名法典”仍是待处理事项，未混入本轮。

## 已核验的输入

采用 `locales/zh-Hans/gameplay-readability-v7.json` 中的实际译文：

> 所以北部军模仿守护者，制造出了怪物兵器“哨兵”。  
> 如今那些哨兵正在战场上大肆屠杀南部军。

源 ID：`coalesced:41ee13042c4dc5822bd04a9e3a37a1a8f39c7ada856a38363de318d168771fda`；
上下文：`MC2CSMB.int / CSMB00_10 / voc_csmb_0010_10`。
仅显示源译文中的 `\n` 为换行，源文件、文字、标点和断句不变。
该源文件的本地工作副本是CRLF，而Git存储为LF；配置显式使用 `identity_mode=utf8-lf`
校验相同UTF-8内容，并额外在manifest记录实际原始字节摘要。仅身份比较处理CRLF/LF，
不重写源文件，不忽略文本内容变化；字体二进制和字形计划继续使用精确字节摘要。

三档来自当前累计字库计划，不按画面截图反推大小：

| 字体对象 | 字形栅格字号 | 可见格高 | 宽汉字最小 advance | 预览效果 |
|---|---:|---:|---:|---|
| EngineFonts.SmallFont | 15 px | 18 px | 20 px | 白字 |
| General_15 | 22 px | 25 px | 27 px | 白字 |
| EngineMedium_Subtitle | 27 px | 29 px | 32 px | 白字、1 px右下黑影 |

输入为 `cumulative-font-route/glyphs-{1,0,2}.json`；字体别名中的数字不是当前栅格字号。
保留左右2/3 px最小留白与宽字 advance 规则，见 [TEXT_READABILITY](TEXT_READABILITY.md)。
字幕计划的规范 JSON SHA-256 为
`39c67a9e2a8a3646d5f1852269b90f9ff32773789e5c113da989de3daca3fd6e`，
与阶段325字幕阴影构建记录相符。

## 五款字体

字体二进制不进入 Git。版本、下载地址、字体内部 PostScript 名称、完整 SHA-256、
许可证地址及校验值均在 `locales/zh-Hans/font-preview-candidates.json` 中锁定。

| 预览 | 版本 | 实际字体内部名称 | 上游 |
|---|---|---|---|
| 臻楷 Slab GB | v0.827 | LXGWZhenKaiSlabGB-Regular | [lxgw/LxgwZhenKai](https://github.com/lxgw/LxgwZhenKai/releases/tag/v0.827) |
| 文楷 Medium | v1.530 | LXGWWenKai-Medium | [lxgw/LxgwWenKai](https://github.com/lxgw/LxgwWenKai/releases/tag/v1.530) |
| 朱雀仿宋 | v0.212 | ZhuqueFangsong-Regular | [TrionesType/zhuque](https://github.com/TrionesType/zhuque/releases/tag/v0.212) |
| 新致宋＋ | v1.069 | LXGWNeoZhiSongPlus | [lxgw/LxgwNeoZhiSong](https://github.com/lxgw/LxgwNeoZhiSong/releases/tag/v1.069) |
| 新晰黑＋ | v1.307 | LXGWNeoXiHeiPlus | [lxgw/LxgwNeoXiHei](https://github.com/lxgw/LxgwNeoXiHei/releases/tag/v1.307) |

臻楷、文楷、朱雀的许可证随下载保存；新致宋、新晰黑各自的 IPA 派生许可同样保留原文，
不将其误标为同一许可证。表格标签使用既有锁定的 Noto Sans CJK SC Regular，
**对白样本则分别用五个真实字体文件**，无回退、伪粗体或图片内文字替换。

## 渲染和验收含义

`tools/render_font_comparison.py` 复用 `supplement_font.rasterize_plan` 的 cmap检查、
共享基线及字形留白，按字格进行 BC3 编解码；字幕复用 `font_shadow.shadow_pixels`。
每个样本37种字符，共5×3组、555个字形栅格。所有正文在深色背景使用相同条件；
每款另有浅色背景的27 px字幕检查。

- **Verified offline**：五款内部字体名匹配；样本缺字为0；字形前景裁切为0；
  15组像素指纹彼此不同；11张PNG均重新打开并校验尺寸、SHA-256。
- 阴影严格受现有可见字格约束；27 px样本在臻楷/文楷/朱雀/新致宋/新晰黑中分别有
  0/2/10/4/11个外移阴影采样落在格外，被保留边界规则舍弃。它们不是被裁掉的字形前景，
  也没有为了好看而偷偷增加格高或缩小字号。
- 1×图是一个字形像素对应一个图片像素；2×图只是同一结果的双线性放大，未重新绘字。
- **Runtime unverified**：这不是游戏运行截图；引擎缩放、过滤、着色器、最终窗口分辨率、
  全量游戏字符覆盖与实际换字体后的排版仍需单独验收。本轮不宣称黑色RGB已通过最终字幕shader。

## 重建

依赖已有的 Python、Pillow、fontTools。默认复用已校验的本地字体；`--fetch-fonts`
只在缺文件时下载锁定的上游字体和许可证，限制文件大小并先校验哈希，不安装系统字体。
朱雀ZIP只读取目标TTF成员，不解压其他路径。Noto标签字体可由同一命令获取。

```powershell
python -B -X utf8 -m tools.render_font_comparison --profile locales/zh-Hans/font-preview-candidates.json --fetch-fonts --output build/font-comparison-new
python -B -X utf8 -m unittest discover -s tests -p test_render_font_comparison.py -v
```

输出必须是 `build/` 内尚不存在的子目录。已有结果、未知文件哈希、错误字体、缺字、
超宽行、路径越界都明确失败；不会覆盖原资源、替换字体回退或缩字塞入框内。
该工具和模板使用相对工程路径；本地中间记录不构成重建依赖。

当前结果：`build/phase-326-font-preview/previews-final/`，包含：

- `index.html`：总览及五张卡片，带上游来源链接。
- `00-comparison-1x.png`：五款×三档并排纵向总览。
- `01-...` 至 `05-...` 的1×/2×PNG：单款深浅背景对照。
- `manifest.json`：真实字形名、基线、字格、逐字像素摘要、阴影边界计数、图像摘要和工具版本。

本轮只有新工具、回归测试、预览配置与本文进入Git。生成图、下载字体及许可证均留在
忽略的build目录。删除了逐像素相同的重复PNG和用户未选用的无后缀臻楷字体，
保留早期元数据作为研究记录。原有5,901个受保护文件（包含两张测试ISO、运行字库、
Coalesced、素材源、配置及准备记录）在本轮前后逐项大小和SHA-256一致。

后续朱雀仿宋Regular与轻度合成500的独立预览见
[ZHUQUE_MEDIUM_PREVIEW](ZHUQUE_MEDIUM_PREVIEW.md)。加粗是新配置中的显式选项，
不影响本页五款原版预览，也不替换游戏内字库。
