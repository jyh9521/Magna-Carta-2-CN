# Phase 292 — 标题菜单、战斗人名与碟片/客串标识完整别名

## Verified：原盘逐成员复核

本轮重新读取两张原盘全部4145个 `.xxx` 成员（D1 1912、D2 2233），逐件计算SHA256，并与 `build/disc1-hashed.json`、`build/disc2-hashed.json` 及旧独立调查清单核对；盘目录的path/directory/sector/offset/size/attributes也重新核对。没有生成ISO/整盘副本，没有启动游戏，原盘仅读。完整ISO未重新hash。

原始证据：[扫描脚本](../build/phase-292-texture-aliases/scan.py)、[输入锁](../build/phase-292-texture-aliases/input-lock.json)、[运行日志](../build/phase-292-texture-aliases/scan.log)、[完整清单](../build/phase-292-texture-aliases/alias-inventory.json)。这些证据同时保留实际物理源SHA、真实导出完整path、package GUID、canonical namespace GUID、export index、payload/tiled/linear BC3/RGBA SHA与解析属性。

扫描先在恢复的logical header以ASCII/UTF-16BE/UTF-16LE名称字节预筛，再按完整FName叶名精确检查imports和exports；只计入 `Engine.Texture2D` 真实导出。缓存以原物理SHA和包名为键复用解析，但双盘每个成员仍独立读取/hash。

| 盘 | 原xxx | header预筛包 | 真Texture资源 | 真Texture导出 |
|---|---:|---:|---:|---:|
| D1 | 1912 | 9 | 5 | 26 |
| D2 | 2233 | 9 | 5 | 26 |

两盘共用路径1594个，其中全部原xxx的同路径源SHA冲突0个；本轮目标真实导出涉及的5资源，同路径源SHA冲突0个。各盘来源仍独立记载，不把D1结果冒充D2验证。

`MC2Game.xxx`、`UI_Core.xxx`、`UI_Field.xxx`、`UI_Field_2.xxx` 两盘均仅字节预筛命中，精确叶名FName表、imports与exports均未命中；它们不是本轮真实别名。没有import-only命中。

## Verified：真实别名所在资源

| 资源 | D1 exports | D2 exports | 原资源SHA256 |
|---|---|---|---|
| `MC2Game/CookedXenon/TitleMap_MSPT.xxx` | 1662,1663,1664,1670,1671,1672 | 1662,1663,1664,1670,1671,1672 | `e094df8399beac753e07a1ee388d5192b8f0a721fa854d786104de7439e98395` |
| `MC2Game/CookedXenon/UI_Battle_08_Jp.xxx` | 27,28,30,31,33,34,35,36 | 27,28,30,31,33,34,35,36 | `36cacc49ee8b0ec199735ecdd8e1f4c0748971d3c0eaf03015522132b1b18b73` |
| `MC2Game/CookedXenon/UI_GameStart.xxx` | 14,15,16 | 14,15,16 | `2884c9e3f5520d6df7390aabcb754ed0644194eb7341ae6e0f25e9594df938b1` |
| `MC2Game/CookedXenon/UI_Pillar.xxx` | 611,612,613,615,616,617 | 611,612,613,615,616,617 | `441ac75a96bb6746bb6b71fbd78bdc75280100c20c77616ea58d67aab0c625dd` |
| `MC2Game/CookedXenon/UI_Pillar_Title.xxx` | 2,3,4 | 2,3,4 | `0bbc44c9cdeba6c3e8b2e5dbf664480632d968cdb6d74b4c9da6f2da9479033d` |

主回填须同时覆盖 `TitleMap_MSPT` 的6个resident导出和 `UI_Pillar` 的两套各3个导出；不能只更新最初的3个独立UI包。

## Verified：格式与像素等价类

全部52个导出均Format7/BC3、空SourceArt、单mip；原bulk flags为0或0x40，两种均经 `parse_atlas_payload` 成功解析并真实解bulk、untile、解码RGBA。没有多mip、raw尺寸不支持或解析失败项。每个完整叶名内部的tiled、linear BC3与RGBA均各只有一个SHA类；没有同叶异图冲突。普通/Red是不同叶名及不同像素图，不能合并覆盖。

| 叶名 | 图尺寸 | D1/D2别名 | RGBA SHA256 |
|---|---|---:|---|
| `character_name_argo` | 128×32 | 1/1 | `78c2b14229b883970e02964ab153746eff9281c0f1c51d6f8d2858e07eb3aa4b` |
| `character_name_argo_red` | 128×32 | 1/1 | `f14004af309526d850f68617d83acff57ffd33a52789267338f661a48f466ab0` |
| `character_name_celestin` | 128×32 | 1/1 | `3c8e052e304bc18f4453a01c7856b4d7420b981b8f80457862c7a494658fee68` |
| `character_name_celestin_red` | 128×32 | 1/1 | `53ced0eaab3c4fbfc2aa8b4d5e0e91d40c890862ffe90d0413cb9a8ced72fd0d` |
| `character_name_juto` | 128×32 | 1/1 | `73fa3b5e167d7e75d67b65e73dbcb6aeeec2548ef42a1b937eafea7e0f0b8112` |
| `character_name_juto_red` | 128×32 | 1/1 | `8b05279fe9eb5e89d5d37f1fd701ef025a54f12984f89aab77f706f43a8a17fc` |
| `character_name_zephi` | 128×32 | 1/1 | `d0ca26d8dbe8a0d1fe80b4a085d3a551aa94d6ec982e5cd16bf0dcc2d49f3ab9` |
| `character_name_zephi_red` | 128×32 | 1/1 | `ec68b58c73dfdf5f15e8970c3a27e0741734a720fe6d71c77106021f36543226` |
| `disc_01` | 64×64 | 4/4 | `5b8fafe721802190c433af265f7c5fa4623a21df9b85439874c028dae9e3466d` |
| `disc_02` | 64×64 | 4/4 | `df46fd28a008c1c457b5d5f407a16034954566bab7a7c329c4cdcc9f8bc6e503` |
| `guest_icon` | 64×32 | 4/4 | `603b654961b9515655864d0c2631bba03f7b6bd5cfc3bafdf6a689ce0858262a` |
| `menu_tex` | 256×256 | 2/2 | `40bd431d2b7000a97cc6a89fd7c4a64d387bd6582bb4dcf14db49ea6f6d09161` |
| `menu_tex_back` | 256×32 | 2/2 | `648bbbef50a3940b838de988919c9c7a5a386b78919291925c433ddb65e3bdbf` |
| `press_start_1` | 256×32 | 2/2 | `b5054b2ce4895b560076403fd33985d456d3bdaecbe193441aa75388e452a2bd` |

## Verified：namespace不能由物理文件名猜测

- `TitleMap_MSPT` 1662–1664的forced根为 `UI_GameStart`，canonical namespace为 `ui_gamestart`，GUID `e4bd88ab4c3d22d9091402ba2ed7054d`；与独立UI_GameStart三图同namespace。
- `TitleMap_MSPT` 1670–1672与 `UI_Pillar` 615–617的forced根为 `UI_Pillar_Title`，namespace GUID `60482c3a49aa0da206bf15804c38718e`；与独立UI_Pillar_Title三图同namespace。
- `UI_Pillar` 611–613则是本包 `Tex.Disc_01/Disc_02/Guest_Icon`，namespace为 `ui_pillar`，GUID `fe0b3d074cda68a96ded118c4c2a061b`。它们与ui_pillar_title对应图像素一致，但不是同namespace，回填应显式列出两套导出。
- 八个人名仅在独立 `UI_Battle_08_Jp` 27/28/30/31/33/34/35/36发现，namespace GUID `27bc6ef04d931f48368f6ea6c58523eb`。

## 未证明事项与使用边界

本次证明所选14个精确叶名在全部原xxx中的真实导出清单和像素类，并未排除不同叶名的视觉重复图、动态资源加载、运行时实例选择、UI缩放/裁切或其他未选UI文字。Disc_01/Disc_02虽已完整盘点，具体是否改图及译文须由本轮方案裁定；此文不把别名审计当作已汉化或游戏内验收。

复跑命令（项目根目录，安装项目依赖并保留原盘）：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python build/phase-292-texture-aliases/scan.py *> build/phase-292-texture-aliases/scan.log
```

本次字面末行：`PASS resources=4145;titles=14;aliases=52;rgba_single_classes=14;originals read-only`；进程退出0。输入锁在扫描结束后全部重开hash一致。
