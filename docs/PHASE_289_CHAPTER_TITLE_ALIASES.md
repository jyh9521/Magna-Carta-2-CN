# Phase 289 — 章节标题纹理别名与既有地名复查

## 范围与证据等级

**Verified（原始资源离线）**：针对 `ch01_01_vill` 这个精确叶对象名，重新读取两张原始盘清单的全部 `.xxx` 成员，逐件 SHA256 通过后恢复 logical header，在 ASCII / UTF-16BE / UTF-16LE header 中查找完整、不区分 ASCII 大小写的名称 token。命中包才完整解析 import / export 表；真实 Texture2D 导出再完整解压、严格解析其单 mip DXT5 payload。没有把 import 误算为资源副本，没有把过去字体类表调查当作图片覆盖。

输入沿用已锁定盘清单及[字体命名空间调查](FONT_BINDING_AUDIT.md)的 4145 包集合；新一轮仍实际读取资源并核对 hash，而非信任历史 `resource_hash_verified` 标记。新脚本另外核对完整目录与清单以及旧调查每个资源 path / SHA 的一致性。输入文件、工具、LZX DLL hash 在 `build/phase-289-alias-research/input-lock.json`；脚本结束时重新核对这些输入。

- D1：1912 个原 `.xxx`，5 个 header token 命中包，3 个真实 Texture2D 导出。
- D2：2233 个原 `.xxx`，3 个 header token 命中包，3 个真实 Texture2D 导出。
- 全部 4145 个资源 SHA 已重新计算；未重新计算整个 ISO SHA，未生成游戏副本。
- 每盘只有 `MC2Game55740`、`UI_Title25`、`UI_Title_Jpn25` 这三个同名导出。此次精确名称调查未发现可另行加入补丁的同名资源别名。

主要原始结果：`build/phase-289-alias-research/alias-inventory.json`；运行脚本 `scan.py`，原终端结果 `scan.log`。报告含4145资源的物理路径/hash/header hash与所有命中import/export细节；没有导出游戏代码到Git。

## 真实纹理副本与字节比较

以下三行在两张盘上逐资源 hash 均相同，但每张盘的来源独立读取验证。

| 原物理资源 | Texture2D export / path | 原资源 SHA256 | bulk |
|---|---|---|---|
| `MC2Game/CookedXenon/MC2Game.xxx` | 55740 / `UI_title.Chapter01.ch01_01_vill` | `13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641` | raw 0 |
| `MC2Game/CookedXenon/UI_Title.xxx` | 25 / `Chapter01.ch01_01_vill` | `b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4` | LZX 0x40 |
| `MC2Game/CookedXenon/UI_Title_Jpn.xxx` | 25 / `Chapter01.ch01_01_vill` | `f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595` | LZX 0x40 |

6 个导出均为 512×64、单 mip。序列化 payload hash 因本地表索引和压缩表示不同而不同，不能用 payload 不等判断图像不同。实际解析后，以下三层6/6分别相等：

- 完整 aligned tiled DXT5 bytes：`418937d6988ab9f586f7bce4e448e4ddba9cb85c66b9efe01a9857f3fc27c5d6`
- untile 后线性 DXT5 blocks：`f752d3d0119a5b3b9d7ff354d03e5f89129f365d0fabd1e937ce6e00705a0330`
- 实际 DXT5 解码 RGBA：`bcc99f39678edcfa2b50fdb86202b3f785bf7c887cdeb37f0f7685730dd508d3`

`mc2game-55740.png`、`ui_title-25.png`、`ui_title_jpn-25.png` 是本轮原始解码预览，原图人工查看文字为“높새바람 섬 마을”。本轮没有修改这些原像素。

### Namespace 不是全部相同

- MC2Game forced export 与 UI_Title standalone 的 canonical path 同为 `ui_title.chapter01.ch01_01_vill`，namespace GUID 同为 `e90197094ec641951da233972bae7ebd`。MC2Game root 是 export45489 `UI_title`。
- UI_Title_Jpn 则是 `ui_title_jpn.chapter01.ch01_01_vill`，GUID `9b9d6ea1412d1aa58d8918a4d535bc36`。它仅与前两者原像素/blocks相同，**不是同一canonical namespace的证明**。
- 此命名空间结论由现有 `StyleGraph.canonical_identity` 及每包原表计算；计算过程没有选择实际运行时加载实例，也没有证明加载优先级。

## Import-only 与 Startup 检查

D1 两个额外 token 命中是消费者引用，不是待替换纹理副本：

| 包 | import | 原路径 |
|---|---:|---|
| `02_Village_Persistent.xxx` | -157 | `UI_title.Chapter01.ch01_01_vill` |
| `CinookIsland_CompTuto_01.xxx` | -188 | `UI_title.Chapter01.ch01_01_vill` |

两盘 `Startup_int.xxx` 均实际读取 SHA `be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3` 并恢复 header，此精确名称 token 均不在 header。依据UE3表内对象名序列化约束，这排除了这些盘内 Startup 包中**精确同名**的静态导出；没有排除其他名字的相似图片、运行时生成对象或其他格式。

## 标题中文必须复用已采用字段，不从OCR另起名

`field_names.py` 重新读取并解析原 `build/disc1-selected/MC2Game/Localization/Coalesced.int`，先验证容器 SHA `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`，随后用稳定ID回查已采用批次并验证原文hash。详细结果 `field-name-evidence.json`：

1. `MC2FieldName.int [ChinookIsland] Town #1`，原 `높새바람 섬 마을`；稳定ID `coalesced:aaf3de80a0c70992b2c57285f156b61f7ce6bd78897c4bfc3de91ccf1bf3836a`；[batch094](../locales/zh-Hans/batch-094.json) 已采用 **风息岛村庄**。
2. `MC2UI_Pillar.int [Destination] Chinookisland_town #1`，原 `높새바람섬 마을 앞`；稳定ID `coalesced:6c9ba07f4fb8271ea70654b9d06cf144019dedb6c5811df92891331e14c5386b`；[batch099](../locales/zh-Hans/batch-099.json) 已采用 **风息岛村庄前**。

因此该标题补丁采用 **风息岛村庄** 可保持已采用INT地名一致；不是“风息岛村”，也不是新增官方译名裁决。图片与字段同字的核对辅助建立文本对应，实际消费者资源链仍以[上一轮章节入口](PHASE_288_ASSET_TEXT_COVERAGE.md)及原包引用证据为准。

## 未覆盖 / 尚未验证

这是一项精确同名Texture2D别名调查，不是游戏全部图片文字覆盖审计。未遍历所有纹理payload、未人工逐图审查4145包、未搜索不同对象名但相同像素的全部图片，也未证明自定义Texture2D子类、非.xxx格式、更新/DLC、动态构造路径、运行时加载优先级、实际章节入口显示或控制台/模拟器绘制。三处已知别名以外的原始header范围现在有精确名称的负证据，但这个负证据不外推为上述范围全部完成。

没有启动游戏；补丁注入、基线/修改/隔离回滚、增量测试目录刷新由主任务单独完成，本文不借其尚未完成状态宣称本轮纹理已经显示中文。

## 重放

仓库根目录，`PYTHONIOENCODING=utf-8`：

```powershell
python build/phase-289-alias-research/scan.py
# PASS resources=4145;aliases=6;rgba_classes=1;block_classes=1;originals read-only
python build/phase-289-alias-research/field_names.py
# JSON: 2 adopted_field_names; recommended_title=风息岛村庄
```

本轮两条命令实际执行退出状态均为0；报告及预览均已重新打开查看。原始资源只读，未改tools/locales/tests。
