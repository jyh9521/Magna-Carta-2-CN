# Phase 291 — BOSS与战败提示17图双盘真实别名审计

## Verified：逐盘原件与完整导出

本轮从原始 `UI_Title.xxx` exports10–24选择15个BOSS图，再从 `UI_GameOver.xxx` exports3、6选择战败标题与按钮提示，共17图。扫描重新读取两张原盘全部4145个 `.xxx` 成员（D1 1912、D2 2233），逐件计算SHA256并与盘清单及旧独立字体调查清单核对；目录path/directory/sector/offset/size/attributes也与实盘复核。完整ISO没有重新hash。所有源成员只读，未启动游戏、未生成整盘副本。

主要证据为 [alias-inventory.json](../build/phase-291-texture-aliases/alias-inventory.json)、[输入锁](../build/phase-291-texture-aliases/input-lock.json)、[脚本](../build/phase-291-texture-aliases/scan.py) 与 [日志](../build/phase-291-texture-aliases/scan.log)。脚本以实际恢复的logical header作ASCII/UTF-16BE/UTF-16LE名称字节预筛，再以完整FName叶名精确匹配imports和exports；只对真正 `Engine.Texture2D` 导出解完整logical package、解析单mip、解bulk LZX、untile并解码RGBA。缓存按原物理SHA及包名复用解析，但第二张盘仍逐件读取/hash，未跳过来源验证。

| 盘 | 原xxx数 | header预筛命中包 | 有真实导出的资源 | 真实Texture2D导出 |
|---|---:|---:|---:|---:|
| D1 | 1912 | 9 | 9 | 40 |
| D2 | 2233 | 5 | 4 | 35 |

D2 `Map13_Lastrada_MainMap_P.xxx`只是字节预筛误命中，精确FName表、imports、exports均没有所选名称，不能列作别名。本轮没有同名import-only包。

## Verified：逐资源来源及export index

| 资源 | D1 exports | D2 exports | 原资源SHA256 |
|---|---|---|---|
| `MC2Game/CookedXenon/ChinookIsland_Zebasa_Spawn.xxx` | 150 | 无真实导出 | `fbb9dd3fc494d39763b47961f21d3b1681ccec8892622d2a8488681db463e4b5` |
| `MC2Game/CookedXenon/Dunan_Vekas_Spawn.xxx` | 268 | 无真实导出 | `4f11fbee71c81eff813ca1009d35dee7b9b8b50454e3534b2ffb5b1acb52586f` |
| `MC2Game/CookedXenon/MC2Game.xxx` | 55656, 55659, 55739 | 55656, 55659, 55739 | `13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641` |
| `MC2Game/CookedXenon/Oldfox_Situation01_BDoor.xxx` | 431 | 无真实导出 | `d855d0cc4f4464999d3bb7f22cccfd7468c2f3b745e22da513ba28a69088caa7` |
| `MC2Game/CookedXenon/Oldfox_Situation02_Sionlegral.xxx` | 288 | 无真实导出 | `b1a87566afaa4833e379f923d1a8b91bdf43d8345498d5cc3f89edb8558edc14` |
| `MC2Game/CookedXenon/Oldfox_Situation03_Clare.xxx` | 1798 | 无真实导出 | `cac7d503d86b82afd7756b79a0451d0c9c8a48b3767b5a71c8530323fdbf705b` |
| `MC2Game/CookedXenon/UI_GameOver.xxx` | 3, 6 | 3, 6 | `292da40a53ee2f9e3ebab0d4fe56d01d97a2bcefdae7d391c8bbe63bf0ac35af` |
| `MC2Game/CookedXenon/UI_Title.xxx` | 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 | 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 | `b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4` |
| `MC2Game/CookedXenon/UI_Title_Jpn.xxx` | 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 | 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 | `f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595` |

两盘共同路径的原资源SHA均相等，没有source hash冲突。D1额外五个地图/事件resident包都是真实forced Texture2D导出，不是import；主回填须包含它们，不能仅更新UI_Title/Jpn与MC2Game后宣称消费者全部同步。D2没有这五包的匹配真实导出，不能将D1列表复制为D2来源。

## Verified：17图像素等价类

全部75个导出可解码；每个完整叶名内部的tiled DXT5、linear BC3和RGBA各自只有一个SHA256类，17/17组通过。15个BOSS与GameOver_Tex均512×64；Notice_tex为256×64。payload hash可能因局部名称表、重定位和bulk编码不同而不同，不能据此断言图像不同。

| 所选叶名 | D1 aliases | D2 aliases | RGBA SHA256 |
|---|---:|---:|---|
| `01elga` | 3 | 3 | `398250598e5c79cda50ef05264c35b493727fd2104e8597b7f9ca3f2c23f985a` |
| `02amon` | 2 | 2 | `f0db8ca539b62578a82cf61eeb263b45ceb3e1df2460735b7d5a5b70dff1a4a6` |
| `boss_astaroth` | 2 | 2 | `d01e9ca6420355bc85f9c95cf0e482045ac4c3286606cd0073f230e44abe99aa` |
| `boss_ch4_leviathan` | 2 | 2 | `8eed0fa283632afbabc212d980af7d2a01ee4d490488825efbcdc3dd254d3bcd` |
| `boss_ch4_melissa` | 2 | 2 | `d861ab75b1d492dbb8beb7dd66450d85c829ae6d6659d9d8747823eb49928564` |
| `boss_ch4_schauenzeit` | 2 | 2 | `552574721ecb443abb762325424ee0c07a8ee021fc36ae058c44e3d69fa87f6e` |
| `boss_ch4_vekas` | 3 | 2 | `37dc13a02cad4c13eb2b53ff9039b9c943af5b525ad6dc648cd4d3c34a6d526f` |
| `boss_ch5_beriel` | 2 | 2 | `9e4d85e575bd0c8cdbf30c45c8b3f1bdcf2e3a519a4af0b0c4646553ec6ce3a3` |
| `boss_ch5_zebasa` | 3 | 2 | `b87542b1ef84f5b81101bd0b0694373d4b8f929db77f86a63d9126ac68bf0ab5` |
| `boss_clare` | 3 | 2 | `76ad3c70f98eff9e5fbcee59cbe2839bb2ae2ecd799d8a185959b2646ade2027` |
| `boss_gigantic` | 2 | 2 | `6a0be71bbaf24441403bffbb5d29f017668c935f4904c4954fea27fc8860a2bc` |
| `boss_huaren` | 2 | 2 | `5674c6c72820a17be70580f7daf1737377509d2b46e0385d021587414838c235` |
| `boss_rootan` | 2 | 2 | `a84d3cada5503714ae00d953074d46febb99e67c8bf78239e16106e3269b26fd` |
| `boss_sion` | 3 | 2 | `b76bf6c6d8737921962fdc3f7df411fc56a06e0f1dc634ed775410ea02094702` |
| `boss_wailinggate` | 3 | 2 | `d221207935e51a9d44fda5f55559a7521eefe2ab32573d5d2eb75decf5899d2f` |
| `gameover_tex` | 2 | 2 | `6ea0f408bf375739a6c0cdba96bb53fea20121b5ec159f829c95fa534be32b08` |
| `notice_tex` | 2 | 2 | `5dc3e3f6ecaae2d4c9d39aea0ef966aefa693d2a00487fde5aa38ea63e856258` |

`Notice_tex`的完整路径为 `UI_GameOver.Notice_tex`（MC2Game resident）或 `Notice_tex`（独立UI_GameOver）；规范identity均为 `ui_gameover.notice_tex`，namespace GUID `871c4a284b35b1a52302688507781870`。本次全盘同叶精确扫描没有发现另一个不同图或不同namespace的Notice_tex，四个跨盘导出均同图；此结论来自真实payload解码，不是名称推断。

## Verified：canonical path与GUID边界

BOSS图有两个独立namespace：`ui_title` GUID `e90197094ec641951da233972bae7ebd`，以及 `ui_title_jpn` GUID `9b9d6ea1412d1aa58d8918a4d535bc36`。两个namespace的同叶图像相同，但不是同一个UE对象identity。GameOver两图只有 `ui_gameover` namespace，GUID如上。JSON对每个导出分别保存实际path、class、serial offset/size、source package GUID、canonical path、namespace GUID、forced_export以及各层bytes hash；不要将source package GUID与uncooked namespace GUID混淆。

D1额外resident分布：ChinookIsland_Zebasa_Spawn、Oldfox_Situation01_BDoor、Oldfox_Situation03_Clare属于ui_title；Dunan_Vekas_Spawn、Oldfox_Situation02_Sionlegral属于ui_title_jpn。MC2Game的三个匹配导出分别是两个ui_gameover图及ui_title.BOSS.01elga。

## 复现、范围与完成门槛

执行命令（仓库根目录）：

```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONDONTWRITEBYTECODE='1'
python build/phase-291-texture-aliases/scan.py > build/phase-291-texture-aliases/scan.log 2>&1
```

本次退出状态0，日志末行原文：

```text
PASS resources=4145;titles=17;aliases=75;rgba_single_classes=17;originals read-only
```

输入锁包含原UI_Title/UI_GameOver快照、两盘清单、旧独立字体调查、实际parser/decompressor/decoder相关工具、LZX DLL及扫描脚本；脚本末尾重新hash核对全部锁项。原图预览只留在忽略的build目录，不提交游戏图片。

本调查证明所选精确叶名的原/forced图像别名覆盖，不证明任意不同名称但同图的纹理不存在，也不证明运行时动态加载优先级或玩家可见位置。它没有新增译文或自行回填，主任务应按本清单累积47章图之后的实际纹理包，运行字段/字库/非目标export完整性、三态及双盘资源包验证，并由用户最终验收游戏内显示。
