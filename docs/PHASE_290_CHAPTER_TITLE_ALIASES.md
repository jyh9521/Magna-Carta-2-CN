# Phase 290 — 完整47图章节标题族原始双盘别名调查

## Verified 原始资源范围

本轮从原始 `UI_Title.xxx` 的 exports25–71 取得47个 `Engine.Texture2D` 叶对象名，再重新读取两张盘全部4145个 `.xxx` 成员，逐件重新计算SHA256并核对盘清单、旧字体调查的独立path/hash集合；目录项的path/sector/offset/size/attributes也与实盘目录复核。完整ISO未重新计算hash。所有原始游戏成员只读，未生成整盘副本、未启动游戏。

对每包恢复logical header，以ASCII/UTF-16BE/UTF-16LE大小写不敏感完整名称字节预筛，然后解析名称/import/export表，必须以最终叶名精确相等才列入对应项。只有真实 `Engine.Texture2D` 导出才完整恢复包及单mip payload，解LZX bulk、untile并实际解码RGBA；import明确另外列出。相同物理hash及包名的解析缓存不跳过第二张盘逐件原始读取和hash验证。

原始结果：[alias-inventory.json](../build/phase-290-title-aliases/alias-inventory.json)，包括4145条源路径、原资源hash、logical header hash、imports及273个真实导出的export index/path/serial offset/size、payload/tiled/linearBC3/RGBA SHA256、原package GUID、canonical namespace GUID。`input-lock.json` 锁定清单、源工具、LZX DLL和本次扫描脚本并在末尾重新验证。原图及decoded预览仅在忽略的build目录，不提交游戏图片。

## 每盘真实资源，不把import当别名

| 盘 | 原xxx数 | header命中包 | 真实导出 | 有真实导出的资源 |
|---|---:|---:|---:|---:|
| D1 | 1912 | 15 | 132 | 13 |
| D2 | 2233 | 19 | 141 | 16 |

| 资源 | D1 exports | D2 exports | 原资源SHA256 |
|---|---|---|---|
| `MC2Game/CookedXenon/02_Village_Persistent.xxx` | 1464, 1465, 1466 | 无真实导出 | `e690c8fb93f1cf1ec6ec0e833e0fab00ae84c4a68f71a84f28e3c6d42d0bc3c3` |
| `MC2Game/CookedXenon/Abazet_Comp02_01.xxx` | 2003 | 2003 | `4f49e2b9a1b29f8ebbbba3825584b8714bd865bfca43c20e4a7025addf481bfc` |
| `MC2Game/CookedXenon/BG03_abazetfield_Persistent.xxx` | 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299 | 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299 | `e3c64f376a505f5af3c81347cc372a7d648bab28021974bb1ea5f56c91e1d44d` |
| `MC2Game/CookedXenon/BG05_KOTAMAREnFIELD_Persistant.xxx` | 1255, 1256 | 1255, 1256 | `a3bfe76a45895a14f0734405740457a085275ceca36739494e07341d86c2f553` |
| `MC2Game/CookedXenon/BG06_Ucave_P.xxx` | 560, 561, 562 | 560, 561, 562 | `c9fa8ade5ae2766236487e72d40b4da26222cfe6948e2a1c2af2794e84d1c0ec` |
| `MC2Game/CookedXenon/Dunan_Comp04_01.xxx` | 1005, 1006 | 1005, 1006 | `3ac22215d3e7906c69b3ef44614157efde668c4d92c767153562e263f50cb251` |
| `MC2Game/CookedXenon/MC2Game.xxx` | 55740 | 55740 | `13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641` |
| `MC2Game/CookedXenon/Map04_oldfox_Persistent.xxx` | 394, 395, 396, 397, 398, 399 | 394, 395, 396, 397, 398, 399 | `adac8f90315f910e99324395aa0d4195d058d7ffca2fb14725c25400f28a0ee7` |
| `MC2Game/CookedXenon/Map07_Dunan_Persistent.xxx` | 441, 442, 443, 444 | 441, 442, 443, 444 | `1a6c0c95eb69e07924d789a27ff0bb54bda586864519dc34aa0113dacbdf44a7` |
| `MC2Game/CookedXenon/Map07a_DField_P.xxx` | 无真实导出 | 421, 422, 423, 424, 425 | `8488e98ee72eddfe271af055b21cd4865252dbfef731d0c2c7a25b998f9c290e` |
| `MC2Game/CookedXenon/Map10_Velfort_MainMap_P.xxx` | 无真实导出 | 727, 728, 729, 730 | `66ed9201f12d1ad241907f04070e9c74ca216522d96115f37267770250dceb69` |
| `MC2Game/CookedXenon/Oldfox_Comp02_01.xxx` | 1545 | 1545 | `67b8d86977f1aad454942b196e6444441b348eea22d0d9a1247f1f8277d360d3` |
| `MC2Game/CookedXenon/Ruhalt_P.xxx` | 无真实导出 | 817, 818 | `b5db633a07724c70b6039868044c95d4665e51b539065a10e38beb494b943969` |
| `MC2Game/CookedXenon/UI_Title.xxx` | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71 | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71 | `b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4` |
| `MC2Game/CookedXenon/UI_Title_Jpn.xxx` | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71 | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71 | `f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595` |
| `MC2Game/CookedXenon/Ucave_Comp03_01.xxx` | 876 | 876 | `d2a664cd9c817f647fbfa262a90d27ecc309038d80f6c1897a95e96b64d97118` |
| `MC2Game/CookedXenon/Velfort_Inrush_Castle.xxx` | 无真实导出 | 39 | `28087c9895c19569bbf3b854f4b09f9f56b1f5631c65f7d12cec10ff38f376a8` |

没有依据当前32资源默认上限删减这些别名；完整族写入将新增地图resident资源，主任务须调整通用数量边界并保留所有完整性验证，不能仅更新UI_Title/UI_Title_Jpn而宣称47图全部消费者同步。

## 逐图一致性与完整映射

全部273个真实导出都是512×64、单mip。每个叶名内部tiled DXT5 bytes、untile后的linear BC3和解码RGBA分别全相等；47/47个组均是1个hash类。不同组不据此合并。payload hash受不同本地表/偏移/压缩影响，保留在JSON，不用payload不同推断图像不同。

各组完整export映射位于JSON的 `groups[].aliases`；下表列出逐盘别名数以及实际原图RGBA（不是PNG编码hash）：

| 原叶名 | UI_Title/Jpn export | D1别名数 | D2别名数 | RGBA SHA256 |
|---|---:|---:|---:|---|
| `ch01_01_vill` | 25 | 3 | 3 | `bcc99f39678edcfa2b50fdb86202b3f785bf7c887cdeb37f0f7685730dd508d3` |
| `ch01_02_beach` | 26 | 3 | 2 | `9a5bc6b2457e65b8c560f93f5d949cebad2f3fec1c259430e095f5ac66d53f33` |
| `ch01_03_cave` | 27 | 3 | 2 | `9f7e31ed103363612e957dcb04bc90b61bd2150e174825869a3268d8d6d42967` |
| `ch01_04_wood` | 28 | 3 | 2 | `cbb1ba7332d007f0056e5758a71d107a87f5ebec76744bf3f855534014f51f76` |
| `ch02_01_abazet` | 29 | 3 | 3 | `29dd7da7c531112ad3f5c96acbb85b71816a2f161080e6f15297acae93b21a56` |
| `ch02_02_abazet_port` | 30 | 4 | 4 | `65985105fcc457dbb46437721e88803cc2699114987c8d5d9fa70d402bd332b2` |
| `ch02_03_abazet_field` | 31 | 5 | 5 | `112d234ce570e56a40bafb215bca2d65538e14b5ae27dbcbe8d449aa25e1d405` |
| `ch02_04_forest_of_wild` | 32 | 4 | 4 | `535901ca982d1dda196a72f2c058270245151bb80b6219f893aa69bb10f4e6e9` |
| `ch02_05_hill_of_a_chief` | 33 | 2 | 2 | `9da2fe88e49a67b9d5c752e32caaa3200c643fa4ab61912e65f2f1bb5cd996b4` |
| `ch02_06_cave_of_lati_tribe` | 34 | 4 | 4 | `c075f8cd27789eab9d819759f060419f3bdfb4f73d13ff3f707d66da805595dc` |
| `ch02_07_base_of_werewolves` | 35 | 4 | 4 | `9adb1b4e87e2b716d7a37631f90ad56cceffd77d480d199dde84e296d288f4eb` |
| `ch02_08_headquarters` | 36 | 2 | 2 | `675088a37215e4ff567cb984f769dc4e7fd16212448c348f5aa6b949c0f60228` |
| `ch02_09_old_fox_canyon` | 37 | 5 | 5 | `62f90ecfabe705a498fb6347e9a3437d20f489e36cdf29d68414bf8748670f75` |
| `ch02_10_temporary_base` | 38 | 2 | 2 | `eb83a91202efb143a3eaf4275cdb3b9822e9189ce57534d42161b50e75c4c7c5` |
| `ch02_11_desert_of_silence` | 39 | 3 | 3 | `276bb2bf265ae8756754a026055622fd3e82829c6ccd72f55ec042da5c7e6076` |
| `ch02_12_wail_wall` | 40 | 2 | 2 | `fab09dfa62ae6ac179804e728da8a182d6ee67b9f192b9984b7c505b592405ba` |
| `ch02_heathofsilence` | 41 | 4 | 4 | `dd757a5ef2d5e35835994b0dada6816666645505eed4aec6e408b430252090d3` |
| `ch02_navyblue` | 42 | 3 | 3 | `15e0e8574a1ae56239897d53bca5c2aef7506b9e38aa2c940fa2d1f1e959419e` |
| `ch02_northerncampsite` | 43 | 2 | 2 | `1a3050f92f5f26b7e0dd4808e35f426c55ad3eaa216a427867cac87f08510507` |
| `ch02_northerngarrison` | 44 | 4 | 4 | `023a656adadd5de9e08d33b49f6b1042f38b27ad7627189d3eb9c9665489ecbc` |
| `ch02_northernoutpost` | 45 | 4 | 4 | `7197f14021f73ee78ea451e91c518a7a364fdc2288d429d8f02d9cd156a63300` |
| `ch02_refugeofdarkness` | 46 | 2 | 2 | `1c6e8dbf00b8ab7a1d8194b262d904a4697ad07a5579e9d627184bcbb60b0adf` |
| `ch02_southgate` | 47 | 2 | 2 | `87f9695d8643ad340f8115b83b45d27295f58414e9d7759fa48679cb60f64d5e` |
| `ch03_altar_mare` | 48 | 3 | 3 | `df3d76ad45ae3b987a15f8eb212689dff6792cdd712f981d9c0c9bef1aeca6ee` |
| `ch03_cotamare` | 49 | 3 | 3 | `078b62e9031ebd312e9f42098ffa27d2b95ae564f641c40108e8473a2f50769a` |
| `ch03_library` | 50 | 2 | 2 | `0e4f233b127e19d4398095bc4b3bfe2cbd1594df10c648eb5a8b07c983a412cf` |
| `ch03_maresquare` | 51 | 2 | 2 | `3b117f6a6233953e0ec45ae0024c9c1033b26e6485e3541bc0f1ae8b29933a93` |
| `ch03_tomb` | 52 | 3 | 3 | `02f24ff0c267390373f2ec425f7500e66cad6c42f5f4ebc46bf14cd63b79f03f` |
| `ch03_undersea` | 53 | 4 | 4 | `60548eb99237135de3d795bab87d4f426e3a9effddf36c74474adf1e29b04aa3` |
| `ch04_1stcheckpoint` | 54 | 3 | 3 | `536d81c229005f0fddfdb2fb7a3fb12e251194c4cfc92ea0f6420a36c5495b23` |
| `ch04_2stcheckpoint` | 55 | 3 | 3 | `88a0edd00e4cf062ef8956ed0300b094f93f7c7377dad010e09b5573d81dd898` |
| `ch04_darkblade` | 56 | 4 | 4 | `559843436684e5fe36a75461bbba984c90aa30a3e0077ba2983c3ae152c73392` |
| `ch04_dunanhill` | 57 | 4 | 4 | `0c1c502c39e087629628af689cc59084cd8e97cc0ea9a41bdaf51114a00f7914` |
| `ch04_dunanhillcheck` | 58 | 2 | 2 | `a713bb4ea1fb7fcff05619c9cb09e38fbcd158805738f726c0dc4569e6b09f01` |
| `ch06_ancient` | 59 | 2 | 3 | `5d0fc5fecbf404e3f4aa21f42b84193f364b3389927b81eccc5495607dc1ef82` |
| `ch06_dunanfield` | 60 | 2 | 3 | `a2cdbe9bb9bc040663adf7750dee008e035f7834dcfa0f2b8cafa85e59cfd2df` |
| `ch06_lanoara` | 61 | 2 | 3 | `fe3dd664260908d8002ea8b52b0eba198f98db3bffef6f50e5c0250b0e7f5c38` |
| `ch06_outlaws` | 62 | 2 | 3 | `c1b6579d534c13b86fe5251586e1c06a33ee3543c6cfad56cd19c80417cf03cd` |
| `ch06_reinpolt` | 63 | 2 | 3 | `8887e9b821d6975222213fb365ef65622e1596f8e3881f1c5d5bf0b0cd27cff1` |
| `ch06_ruhalt` | 64 | 2 | 3 | `3be37e8b8ad6d6889cbdeb2192259b2b0b2e7ba1dce41cc19bd559f95470ca1c` |
| `ch07_belfort` | 65 | 2 | 3 | `cc911714cd8672da81126b2696ffa5eec930d9eae276b979aec38e641501bcc5` |
| `ch07_belfortcastle` | 66 | 2 | 4 | `d1afd0d1e9884a900114e58d721ddb170c5e5eb5fd5045d12496e8494a346312` |
| `ch07_belfortruin` | 67 | 2 | 2 | `b8ff6c3f24d08b975770e4aa1bea438cb3ee047beea353f04243aef48c1d3816` |
| `ch07_belfortsouthern` | 68 | 2 | 3 | `a28d9ab7f74b7cdc0b635d48f4a9806933db96e6fdcf1547b0ec3e9f0c2b2db6` |
| `ch07_starlightfield` | 69 | 2 | 3 | `238fd89ee9fa6ae1364a9f094a72477b8e282dc012ed2a4724193e531b0e07f1` |
| `map_lastrada` | 70 | 2 | 2 | `154f28aba77c8840e1dc9a366a9d73fad12ecb9b18771d5fb1836018573700f0` |
| `map_ruhaltp` | 71 | 2 | 3 | `ea74684f719bd68030e937df236663044d8bc41dac9abe3d2a9a77fad4252dc3` |

## 命名空间与来源

真实导出有 `ui_title` namespace（GUID `e90197094ec641951da233972bae7ebd`）和独立 `ui_title_jpn` namespace（GUID `9b9d6ea1412d1aa58d8918a4d535bc36`）。地图副本是forced exports，不能误称为import-only。Abazet_Comp02_01、Dunan_Comp04_01、Map07_Dunan_Persistent的命中导出属于ui_title_jpn；BG03_abazetfield_Persistent、Map04_oldfox_Persistent同时含两个namespace，必须按每条实际path/identity处理，不从物理包名推断。相同图像不等于相同namespace。独立source package GUID也逐导出记录于JSON，不能与namespace GUID混淆。

MC2Game仅有村庄那一个已知章节纹理，不含全部47个章节入口图；其余forced exports分布在地图包。D1有独有的02_Village_Persistent三个导出，D2另有Map07a_DField_P/Map10_Velfort_MainMap_P/Ruhalt_P/Velfort_Inrush_Castle，共两盘资源并集17包；不能用D1列表代替D2来源。两盘共同资源各自读取/hash后得到相同source SHA。

## 结论边界

**Verified**：这47个精确叶名在盘清单全部4145个原xxx中的静态import/export范围及实际Texture2D像素同一性。**未验证**：不同叶名但同像素副本、其他纹理族/非.xxx资源、未列入原盘的补丁或DLC、动态对象创建、运行时加载优先级、章节实际入口绘制。没有把本轮47图调查称为整个游戏图片覆盖或实际游戏验收。

本报告只建立实际别名全集与原像素一致性；译文、授权绘制区域、各图实际回填、BC3新输出、统一TOC、原资源/Font/字幕保留、隔离回滚及增量测试目录刷新由主任务验证，不依据研究记录声称已完成汉化。

## 重放及本轮观察

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONDONTWRITEBYTECODE="1"
python build/phase-290-title-aliases/scan.py
```

实际退出0，`scan.log` 最后一行：

```text
PASS resources=4145;titles=47;aliases=273;rgba_single_classes=47;originals read-only
```

扫描输入锁、完整结果、47叶名选择表、日志及本报告已重新打开。此前phase289调查文件未改。
