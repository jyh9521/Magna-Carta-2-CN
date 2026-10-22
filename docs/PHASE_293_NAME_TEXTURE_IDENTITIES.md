# Phase 293 — Monster族316源行与11个有证UI图精筛

## Verified：本轮实际范围

本报告只读精筛已冻结的phase293全盘原件别名证据，没有翻译、改图或启动游戏。目标327源行：UI_Name_Jpn `Monster_Name.*` 117行 + UI_Monster_Name_Jpn全部199行；另包含UI_Name_Jpn exports8/9/10（Battle_Npc）、137（Pillar）、155/168/171/180（Tex）以及173/174/175三个人名atlas，共11行。

输入为 `build/phase-293-name-aliases/selected-row-inventory.json` 与 `alias-inventory.json`。精筛脚本 [filter.py](filter.py)、[输入锁](input-lock.json)、[运行日志](run.log)、[完整327行目标清单](target-aliases.json) 均在本目录。父清单已逐件重新hash4145个原xxx；本子任务再从两张原盘读取目标355个disc/path资源成员并逐件hash，与原盘清单和父清单SHA三者相等。没有完整ISO重hash或整盘拷贝。

## Verified：逐源映射与碰撞排除

每个源图以完整canonical path和namespace GUID选择别名，然后断言atlas支持及RGBA SHA与该源图完全相等；不以leaf或像素相同自动合并namespace。清单每行保留source_identity(resource/export/path/leaf)、source原件完整记录、canonical path/GUID、各disc/path/export原payload/tiled/linear/RGBA SHA、尺寸/mip/format及物理源hash。扁平targets数组的每项亦保留source_identity，不同源namespace明确独立。

两族即便同RGBA，仍按UI_Name_Jpn与UI_Monster_Name_Jpn两个源identity分别列出。目标(disc,path,export)键1400项全唯一，没有一个导出被两种源映射争用。相同叶名但其他namespace的对象逐源列于same_leaf_excluded（这是排除于该源映射，不代表排除于别的合法源映射）。

FX_Pattern.tx.Name 的Format05/9mip异namespace碰撞、KJ_Public_Event.North_crowd.North_01 的2048²/12mip碰撞均未进入targets。全部1400目标均单mip/Format7且源RGBA相等。

| 盘 | 精确目标Texture2D导出 | 真实资源数 | 本子任务重新hash原盘成员 |
|---|---:|---:|---:|
| D1 | 697 | 148 | 148 |
| D2 | 703 | 207 | 207 |

两盘目标资源union为243路径；同路径源SHA冲突0，完整路径列表和逐盘来源列于target-aliases.json的resource_union、per_disc、original_resource_rechecks。双盘清单独立，不能复制D1作为D2来源。

## Verified：与当前Font底包的兼容性

与phase285已验证font component候选资源交集仅 `MC2Game/CookedXenon/MC2Game.xxx`。候选物理SHA为 `5595562dab1233cbbf7979fff1b9c9ca031707b40f10adf75eb97ec1e999d425`；先核对font manifest记录，再实际解析其logical tables。以下6个不同目标导出的完整原payload SHA与tiled SHA均与原图证据完全相等；双盘对应12别名没有新增不同源或原字节期望冲突。

| MC2Game export | 完整path | canonical path |
|---|---|---|
| 55688 | `UI_Name_Jpn.Tex.Field_MainMenu_Quest` | `ui_name_jpn.tex.field_mainmenu_quest` |
| 55691 | `UI_Name_Jpn.Tex.KamondBoard_NoKamond` | `ui_name_jpn.tex.kamondboard_nokamond` |
| 55693 | `UI_Name_Jpn.Tex.Nama1` | `ui_name_jpn.tex.nama1` |
| 55694 | `UI_Name_Jpn.Tex.Name` | `ui_name_jpn.tex.name` |
| 55695 | `UI_Name_Jpn.Tex.Name0` | `ui_name_jpn.tex.name0` |
| 55683 | `UI_Monster_Name_Jpn.Boss_Name.Boss_029` | `ui_monster_name_jpn.boss_name.boss_029` |

其余目标资源不在font component候选交集中，因此其正确底包是各盘已hash原资源；这不等于允许覆盖此前纹理变更，实际累计texture计划仍须保留旧编辑并由主构建验证非目标导出/字体不变。本报告没有写入实际overlay。

## 327源行摘要（完整别名见JSON）

| 源package/export | 源path | namespace GUID | D1 / D2真实别名数 |
|---|---|---|---:|
| UI_Name_Jpn / 8 | `Battle_Npc.Npc_00` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 9 | `Battle_Npc.Npc_01` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 10 | `Battle_Npc.Npc_02` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 17 | `Monster_Name.Boss_001_01` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 18 | `Monster_Name.Boss_001_02` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 19 | `Monster_Name.Boss_002_01` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 20 | `Monster_Name.Boss_002_02` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 21 | `Monster_Name.Boss_003_01` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 22 | `Monster_Name.Boss_003_02` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 23 | `Monster_Name.Boss_003_03` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 24 | `Monster_Name.Boss_006_01` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 25 | `Monster_Name.Boss_011_01` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 26 | `Monster_Name.Boss_011_02` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 27 | `Monster_Name.Boss_011_03` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 28 | `Monster_Name.BOSS_300` | `cc76280e4d58de4f4d38e0add952a460` | 2/3 |
| UI_Name_Jpn / 29 | `Monster_Name.BOSS_301` | `cc76280e4d58de4f4d38e0add952a460` | 3/3 |
| UI_Name_Jpn / 30 | `Monster_Name.BOSS_302` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 31 | `Monster_Name.BOSS_303` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 32 | `Monster_Name.BOSS_304` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 33 | `Monster_Name.BOSS_305` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 34 | `Monster_Name.BOSS_306` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 35 | `Monster_Name.BOSS_307` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 36 | `Monster_Name.BOSS_308` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 37 | `Monster_Name.BOSS_309` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 38 | `Monster_Name.BOSS_310` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 39 | `Monster_Name.BOSS_311` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 40 | `Monster_Name.Mname_01` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 41 | `Monster_Name.Mname_02` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 42 | `Monster_Name.Mname_03` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 43 | `Monster_Name.Mname_04` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 44 | `Monster_Name.Mname_05` | `cc76280e4d58de4f4d38e0add952a460` | 35/16 |
| UI_Name_Jpn / 45 | `Monster_Name.Mname_06` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 46 | `Monster_Name.Mname_07` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 47 | `Monster_Name.Mname_08` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 48 | `Monster_Name.Mname_09` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 49 | `Monster_Name.Mname_10` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 50 | `Monster_Name.Mname_11` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 51 | `Monster_Name.Mname_12` | `cc76280e4d58de4f4d38e0add952a460` | 35/16 |
| UI_Name_Jpn / 52 | `Monster_Name.Mname_13` | `cc76280e4d58de4f4d38e0add952a460` | 37/17 |
| UI_Name_Jpn / 53 | `Monster_Name.Mname_14` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 54 | `Monster_Name.Mname_15` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 55 | `Monster_Name.Mname_16` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 56 | `Monster_Name.Mname_17` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 57 | `Monster_Name.Mname_18` | `cc76280e4d58de4f4d38e0add952a460` | 4/2 |
| UI_Name_Jpn / 58 | `Monster_Name.Mname_19` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 59 | `Monster_Name.Mname_20` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 60 | `Monster_Name.Mname_21` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 61 | `Monster_Name.Mname_22` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 62 | `Monster_Name.Mname_23` | `cc76280e4d58de4f4d38e0add952a460` | 7/7 |
| UI_Name_Jpn / 63 | `Monster_Name.Mname_24` | `cc76280e4d58de4f4d38e0add952a460` | 3/3 |
| UI_Name_Jpn / 64 | `Monster_Name.Mname_25` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 65 | `Monster_Name.Mname_26` | `cc76280e4d58de4f4d38e0add952a460` | 9/7 |
| UI_Name_Jpn / 66 | `Monster_Name.Mname_27` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 67 | `Monster_Name.Mname_28` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 68 | `Monster_Name.Mname_29` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 69 | `Monster_Name.Mname_30` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 70 | `Monster_Name.Mname_31` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 71 | `Monster_Name.Mname_32` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 72 | `Monster_Name.Mname_33` | `cc76280e4d58de4f4d38e0add952a460` | 5/2 |
| UI_Name_Jpn / 73 | `Monster_Name.Mname_35` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 74 | `Monster_Name.Mname_36` | `cc76280e4d58de4f4d38e0add952a460` | 5/2 |
| UI_Name_Jpn / 75 | `Monster_Name.Mname_37` | `cc76280e4d58de4f4d38e0add952a460` | 13/4 |
| UI_Name_Jpn / 76 | `Monster_Name.Mname_38` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 77 | `Monster_Name.Mname_39` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 78 | `Monster_Name.Mname_40` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 79 | `Monster_Name.Mname_41` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 80 | `Monster_Name.Mname_42` | `cc76280e4d58de4f4d38e0add952a460` | 4/3 |
| UI_Name_Jpn / 81 | `Monster_Name.Mname_43` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 82 | `Monster_Name.Mname_44` | `cc76280e4d58de4f4d38e0add952a460` | 4/3 |
| UI_Name_Jpn / 83 | `Monster_Name.Mname_45` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 84 | `Monster_Name.Mname_46` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 85 | `Monster_Name.Mname_47` | `cc76280e4d58de4f4d38e0add952a460` | 8/3 |
| UI_Name_Jpn / 86 | `Monster_Name.Mname_48` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 87 | `Monster_Name.Mname_49` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 88 | `Monster_Name.Mname_50` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 89 | `Monster_Name.Mname_51` | `cc76280e4d58de4f4d38e0add952a460` | 3/2 |
| UI_Name_Jpn / 90 | `Monster_Name.Mname_52` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 91 | `Monster_Name.Mname_53` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 92 | `Monster_Name.Mname_54` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 93 | `Monster_Name.Mname_55` | `cc76280e4d58de4f4d38e0add952a460` | 1/2 |
| UI_Name_Jpn / 94 | `Monster_Name.Mname_56` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 95 | `Monster_Name.Mname_57` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 96 | `Monster_Name.Mname_58` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 97 | `Monster_Name.Mname_59` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 98 | `Monster_Name.Mname_60` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 99 | `Monster_Name.Mname_61` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 100 | `Monster_Name.Mname_62` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 101 | `Monster_Name.Mname_63` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 102 | `Monster_Name.Mname_64` | `cc76280e4d58de4f4d38e0add952a460` | 1/2 |
| UI_Name_Jpn / 103 | `Monster_Name.Mname_65` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 104 | `Monster_Name.Mname_66` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 105 | `Monster_Name.Mname_67` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 106 | `Monster_Name.Mname_68` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 107 | `Monster_Name.Mname_70_nurence` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 108 | `Monster_Name.North_100` | `cc76280e4d58de4f4d38e0add952a460` | 35/31 |
| UI_Name_Jpn / 109 | `Monster_Name.North_103` | `cc76280e4d58de4f4d38e0add952a460` | 33/32 |
| UI_Name_Jpn / 110 | `Monster_Name.North_105` | `cc76280e4d58de4f4d38e0add952a460` | 4/7 |
| UI_Name_Jpn / 111 | `Monster_Name.North_107` | `cc76280e4d58de4f4d38e0add952a460` | 3/21 |
| UI_Name_Jpn / 112 | `Monster_Name.North_110` | `cc76280e4d58de4f4d38e0add952a460` | 6/3 |
| UI_Name_Jpn / 113 | `Monster_Name.North_111` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 114 | `Monster_Name.North_17` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 115 | `Monster_Name.North_18_Theranii` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 116 | `Monster_Name.North_23` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 117 | `Monster_Name.Object_001` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 118 | `Monster_Name.Object_002` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 119 | `Monster_Name.Object_003` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 120 | `Monster_Name.Object_400` | `cc76280e4d58de4f4d38e0add952a460` | 11/2 |
| UI_Name_Jpn / 121 | `Monster_Name.Object_401` | `cc76280e4d58de4f4d38e0add952a460` | 5/5 |
| UI_Name_Jpn / 122 | `Monster_Name.Object_402` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 123 | `Monster_Name.Object_403` | `cc76280e4d58de4f4d38e0add952a460` | 5/2 |
| UI_Name_Jpn / 124 | `Monster_Name.Senti_200` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 125 | `Monster_Name.Senti_201` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 126 | `Monster_Name.Senti_202` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 127 | `Monster_Name.Senti_203` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 128 | `Monster_Name.Senti_204` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 129 | `Monster_Name.Senti_205` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 130 | `Monster_Name.Senti_206` | `cc76280e4d58de4f4d38e0add952a460` | 2/1 |
| UI_Name_Jpn / 131 | `Monster_Name.Senti_207` | `cc76280e4d58de4f4d38e0add952a460` | 1/8 |
| UI_Name_Jpn / 132 | `Monster_Name.Senti_208` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 133 | `Monster_Name.South_500` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 137 | `Pillar.Piller_Menu_Title2` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Name_Jpn / 155 | `Tex.Abis_Title` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 168 | `Tex.Field_MainMenu_Quest` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 171 | `Tex.KamondBoard_NoKamond` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 173 | `Tex.Nama1` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 174 | `Tex.Name` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 175 | `Tex.Name0` | `cc76280e4d58de4f4d38e0add952a460` | 2/2 |
| UI_Name_Jpn / 180 | `Tex.Piller_Menu_Title2` | `cc76280e4d58de4f4d38e0add952a460` | 1/1 |
| UI_Monster_Name_Jpn / 8 | `Battle_Npc.Npc_00` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 9 | `Battle_Npc.Npc_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 10 | `Battle_Npc.Npc_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 11 | `Battle_Npc.Npc_03` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 12 | `Battle_Npc.Npc_04` | `30ea9b2744c191d7b127fe9beb19db6d` | 18/6 |
| UI_Monster_Name_Jpn / 13 | `Battle_Npc.Npc_05` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 14 | `Battle_Npc.Npc_06` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 15 | `Battle_Npc.Npc_07` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 16 | `Battle_Npc.Npc_08` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 17 | `Boss_Name.Boss_000` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 18 | `Boss_Name.Boss_001` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 19 | `Boss_Name.Boss_001_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 20 | `Boss_Name.Boss_001_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 21 | `Boss_Name.Boss_002` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 22 | `Boss_Name.Boss_002_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 23 | `Boss_Name.Boss_002_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 24 | `Boss_Name.Boss_003` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 25 | `Boss_Name.Boss_003_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 26 | `Boss_Name.Boss_003_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 27 | `Boss_Name.Boss_003_03` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 28 | `Boss_Name.Boss_004` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 29 | `Boss_Name.Boss_005` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 30 | `Boss_Name.Boss_006` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 31 | `Boss_Name.Boss_006_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 32 | `Boss_Name.Boss_007` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 33 | `Boss_Name.Boss_008` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 34 | `Boss_Name.BOSS_009` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 35 | `Boss_Name.BOSS_010` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 36 | `Boss_Name.BOSS_011` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 37 | `Boss_Name.Boss_011_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 38 | `Boss_Name.Boss_011_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 39 | `Boss_Name.Boss_011_03` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 40 | `Boss_Name.BOSS_012` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 41 | `Boss_Name.BOSS_013` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 42 | `Boss_Name.BOSS_014` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 43 | `Boss_Name.BOSS_015` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/4 |
| UI_Monster_Name_Jpn / 44 | `Boss_Name.Boss_016` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 45 | `Boss_Name.Boss_016_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 46 | `Boss_Name.Boss_017` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 47 | `Boss_Name.Boss_017_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 48 | `Boss_Name.Boss_017_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 49 | `Boss_Name.BOSS_018` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 50 | `Boss_Name.BOSS_019` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 51 | `Boss_Name.Boss_020` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 52 | `Boss_Name.Boss_021` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 53 | `Boss_Name.Boss_022` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 54 | `Boss_Name.Boss_023` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 55 | `Boss_Name.Boss_024` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 56 | `Boss_Name.Boss_025` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 57 | `Boss_Name.BOSS_026` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 58 | `Boss_Name.Boss_027` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 59 | `Boss_Name.Boss_028` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 60 | `Boss_Name.Boss_029` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 61 | `Boss_Name.Boss_030` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 62 | `Boss_Name.BOSS_31` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 63 | `Boss_Name.BOSS_32` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 64 | `Boss_Name.BOSS_33` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 65 | `Boss_Name.BOSS_34` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 66 | `Boss_Name_Big.Boos_Ch6_Lecas` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 67 | `Boss_Name_Big.Boss_Ch10_Jopa` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 68 | `Boss_Name_Big.Boss_Ch11_Melissa` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 69 | `Boss_Name_Big.Boss_Ch12_Alex` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 70 | `Boss_Name_Big.Boss_Ch12_Raud` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 71 | `Boss_Name_Big.Boss_Ch6_Asmuodeus` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 72 | `Boss_Name_Big.Boss_Ch6_CrazyJuto` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 73 | `Boss_Name_Big.Boss_Ch9_Beelzebub` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 74 | `Boss_Name_Big.Boss_GiantMoth` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 75 | `Boss_Name_Big.Boss_Inferno` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 76 | `Boss_Name_Big.Boss_MadGolem` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 77 | `Boss_Name_Big.Boss_SwampEel` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 78 | `Monster_Name.Mname_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 79 | `Monster_Name.Mname_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 80 | `Monster_Name.Mname_03` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 81 | `Monster_Name.Mname_04` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 82 | `Monster_Name.Mname_05` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 83 | `Monster_Name.Mname_06` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 84 | `Monster_Name.Mname_07` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 85 | `Monster_Name.Mname_08` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 86 | `Monster_Name.Mname_09` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 87 | `Monster_Name.Mname_10` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 88 | `Monster_Name.Mname_11` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 89 | `Monster_Name.Mname_12` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 90 | `Monster_Name.Mname_13` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 91 | `Monster_Name.Mname_14` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 92 | `Monster_Name.Mname_15` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 93 | `Monster_Name.Mname_16` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 94 | `Monster_Name.Mname_17` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 95 | `Monster_Name.Mname_18` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 96 | `Monster_Name.Mname_19` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 97 | `Monster_Name.Mname_20` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 98 | `Monster_Name.Mname_21` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 99 | `Monster_Name.Mname_22` | `30ea9b2744c191d7b127fe9beb19db6d` | 4/4 |
| UI_Monster_Name_Jpn / 100 | `Monster_Name.Mname_23` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 101 | `Monster_Name.Mname_24` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 102 | `Monster_Name.Mname_25` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 103 | `Monster_Name.Mname_26` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 104 | `Monster_Name.Mname_27` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 105 | `Monster_Name.Mname_28` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 106 | `Monster_Name.Mname_29` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 107 | `Monster_Name.Mname_30` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 108 | `Monster_Name.Mname_31` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 109 | `Monster_Name.Mname_32` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 110 | `Monster_Name.Mname_33` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 111 | `Monster_Name.Mname_35` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 112 | `Monster_Name.Mname_36` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 113 | `Monster_Name.Mname_37` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 114 | `Monster_Name.Mname_38` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 115 | `Monster_Name.Mname_39` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 116 | `Monster_Name.Mname_40` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 117 | `Monster_Name.Mname_41` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 118 | `Monster_Name.Mname_42` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 119 | `Monster_Name.Mname_43` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 120 | `Monster_Name.Mname_44` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 121 | `Monster_Name.Mname_45` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 122 | `Monster_Name.Mname_46` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/4 |
| UI_Monster_Name_Jpn / 123 | `Monster_Name.Mname_47` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 124 | `Monster_Name.Mname_48` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 125 | `Monster_Name.Mname_49` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 126 | `Monster_Name.Mname_50` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 127 | `Monster_Name.Mname_50as` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 128 | `Monster_Name.Mname_51` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 129 | `Monster_Name.Mname_52` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 130 | `Monster_Name.Mname_53` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 131 | `Monster_Name.Mname_53ft` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 132 | `Monster_Name.Mname_54` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 133 | `Monster_Name.Mname_54sdf` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 134 | `Monster_Name.Mname_55` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 135 | `Monster_Name.Mname_56` | `30ea9b2744c191d7b127fe9beb19db6d` | 3/6 |
| UI_Monster_Name_Jpn / 136 | `Monster_Name.Mname_57` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 137 | `Monster_Name.Mname_58` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 138 | `Monster_Name.Mname_59` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 139 | `Monster_Name.Mname_60` | `30ea9b2744c191d7b127fe9beb19db6d` | 3/4 |
| UI_Monster_Name_Jpn / 140 | `Monster_Name.Mname_61` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/9 |
| UI_Monster_Name_Jpn / 141 | `Monster_Name.Mname_62` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 142 | `Monster_Name.Mname_63` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 143 | `Monster_Name.Mname_64` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 144 | `Monster_Name.Mname_65` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 145 | `Monster_Name.Mname_66` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 146 | `Monster_Name.Mname_67` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 147 | `Monster_Name.Mname_68` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/2 |
| UI_Monster_Name_Jpn / 148 | `Monster_Name.Mname_69` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 149 | `Monster_Name.Mname_70` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/3 |
| UI_Monster_Name_Jpn / 150 | `Monster_Name.Mname_71` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 151 | `Monster_Name.Mname_72` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 152 | `Monster_Name.Mname_73` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 153 | `Monster_Name.Mname_74` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 154 | `Monster_Name.Mname_75` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 155 | `North_Name.North_00` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 156 | `North_Name.North_01` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 157 | `North_Name.North_02` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 158 | `North_Name.North_03` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 159 | `North_Name.North_04` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 160 | `North_Name.North_05` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 161 | `North_Name.North_06` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/18 |
| UI_Monster_Name_Jpn / 162 | `North_Name.North_07` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 163 | `North_Name.North_08` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 164 | `North_Name.North_09` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 165 | `North_Name.North_10` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 166 | `North_Name.North_11` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 167 | `North_Name.North_12` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 168 | `North_Name.North_13` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 169 | `North_Name.North_14` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 170 | `North_Name.North_15` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 171 | `North_Name.North_16` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 172 | `North_Name.North_17` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 173 | `North_Name.North_18` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 174 | `North_Name.North_19` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/1 |
| UI_Monster_Name_Jpn / 175 | `North_Name.North_19_1` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 176 | `North_Name.North_20` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 177 | `North_Name.North_21` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 178 | `North_Name.North_22` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 179 | `North_Name.North_22_1` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 180 | `North_Name.North_23` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 181 | `North_Name.North_24` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 182 | `North_Name.North_26` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 183 | `North_Name.North_27` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/3 |
| UI_Monster_Name_Jpn / 184 | `North_Name.North_28` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/4 |
| UI_Monster_Name_Jpn / 185 | `North_Name.North_29` | `30ea9b2744c191d7b127fe9beb19db6d` | 3/7 |
| UI_Monster_Name_Jpn / 186 | `North_Name.North_30` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/5 |
| UI_Monster_Name_Jpn / 187 | `North_Name.North_31` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 188 | `North_Name.North_32` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 189 | `North_Name.North_33` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 190 | `North_Name.North_34` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 191 | `North_Name.North_35` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 192 | `Object_Name.Object_001` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 193 | `Object_Name.Object_002` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 194 | `Object_Name.Object_003` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 195 | `Object_Name.Object_004` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 196 | `Object_Name.Object_005` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/6 |
| UI_Monster_Name_Jpn / 197 | `Object_Name.Object_006` | `30ea9b2744c191d7b127fe9beb19db6d` | 2/6 |
| UI_Monster_Name_Jpn / 198 | `Senti_Name.Senti_200` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 199 | `Senti_Name.Senti_201` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 200 | `Senti_Name.Senti_202` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 201 | `Senti_Name.Senti_203` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 202 | `Senti_Name.Senti_204` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 203 | `Senti_Name.Senti_205` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/2 |
| UI_Monster_Name_Jpn / 204 | `Senti_Name.Senti_206` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 205 | `Senti_Name.Senti_207` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/1 |
| UI_Monster_Name_Jpn / 206 | `Senti_Name.Senti_208` | `30ea9b2744c191d7b127fe9beb19db6d` | 1/8 |

## 复跑与冻结状态

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python build/phase-293-monster-aliases/filter.py *> build/phase-293-monster-aliases/run.log
```

字面末行：`PASS source_rows=327 aliases=1400 resource_union=243 per_disc=[(697, 148), (703, 207)] conflicts=0;original-target-resources-rehashed;game_execution=false`，退出0。所有输入锁末次重开hash一致。

未证明事项：具体中文译文、文字区域/样式、改图构建、所有运行时加载路径及游戏内验收均由实际回填阶段另行验证。本精筛不宣称整族已汉化。

Implementation and independent glyph errata: see PHASE_293_MONSTER_PARTY_ADOPTION.md and the committed candidate-decisions data. Earlier frozen readouts are historical evidence, not a reason to retain corrected errors.
