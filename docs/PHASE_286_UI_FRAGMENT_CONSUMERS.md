# Phase 286：UI片段的实际拼接消费者

## 已验证（离线静态）

来源为仓库保留的原版disc1逻辑映像 `build/phase-282-verification/MC2Game-logical.bin`，SHA256 `e2a49cdd67c2b49f9b91fb517a49de33262ada4f3ec5a65c776a7d3126d1ecf4`；配置源 `build/disc1-selected/MC2Game/Localization/Coalesced.int` SHA256 `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。本调查只读解析，无游戏启动。下述偏移均是解压后的逻辑包偏移，非压缩包偏移。

### 可以采用：Level_Up/Combo_1至9

`MC2UIScene_LevelUp.SetLevelUpDescription` export11567，函数脚本绝对偏移7782208，脚本SHA256 `5405bb771797dede031b379b5055acd805ac192e6c1d4f711260a5a2f141ad7a`。原函数存在四个完整赋值分支；`build/phase-286-ui-research/proof.py` 不是字符串邻接推测，而是用五次二元Concat_StrStr精确重建各整段赋值并逐字节匹配。其语法为：

```
tempString = "<Styles:MC2UITextStyle_0>"
           $ styleLabel
           $ "<Styles:/>"
           $ "<Strings:MC2UI.Level_Up.Combo_"
           $ string(nComboNum)
           $ ">"
```

第一个分支的styleLabel为`<Strings:MC2UI.Level_Up.Juto_Village_Yupa>`；其余三分支为VirtualFunction `GetStyleName(a_PawnData.PlayerName,nYupa)`。FName索引8833确为GetStyleName，不能把0x1b后的FName误当export引用。`nComboNum`是IntProperty11563，`tempString`为StrProperty11562。

`MC2UIScene_LevelUp.GetStyleName` export11571有6角色12个返回分支，返回值均为`<Strings:MC2UI.Battle_Style.<角色>_Style_0/1>`；参数类型为PlayerName:StrProperty、nYupaNum:IntProperty，返回StrProperty。完整源与hash保存在本地`style-name-getter.json`。所以前段来自实际战斗流派名，而非凭key猜成角色名。

Core原声明`Object.Concat_StrStr` export745位于142806，native_token112即脚本0x70，两个StrProperty参数与StrProperty返回；来源Core逻辑包SHA256 `5ac2c9745bdf6220ddb3dbe898ef88b1c8ac84c882b06816e8257ad5b4c6e2a9`，完整类型记录在`core-concat-declaration.json`。

建议9条原子组译文：`的普通攻击<Styles:MC2UITextStyle_0>第N击<Styles:/>已可使用`，N为1至9。保持原样式标签与第N击对应关系，无新增句号。逐稳定ID、原值hash及建议译文见`adoption-candidates.json`。本结论允许实际回填，但不宣称游戏渲染或布局验收。

### 另一个已验证拼接：经验值后缀

`MC2PawnInterfaceBattle.GetFullExp`与`GetExp`的完整赋值均逐字节重建为`tempStr = ExpNum $ "<Strings:MC2UI.Battle_Log.GetEXP>"`。ExpNum和tempStr的StrProperty声明已绑定。两个表达式的精确偏移、完整函数hash和表达式hash保存在`exp-concat-proof.json`；候选后缀为`点经验值已获得`，将实际组成`100点经验值已获得`，不是`获得了100点经验值`。该句式可接受但本报告不强行把它变成前置动词，也不推广到未找消费者的GetSP。

### 另一个已验证拼接：六名恢复者、七函数

Astarot、Bariel、Beelzebub_Duel、Beelzebub_Solo、Leviathan、MelisaSentinel、SchauenzeitSentinel的AddHealthPercent共七函数，完整赋值一致为`tempStr = Recover_1 $ strHP $ Recover_2`，另一个完整赋值是`strHP = string(nAddHP)`；nAddHP是IntProperty，strHP为StrProperty。因此中段是恢复的HP数值，不是目标角色名！六组、12源条目可以按`<恢复者名>恢复了`和`点HP`整体采用。准确拼写是AstarotRecover、BelielRecover、beeljebubRecover、LeviathanRecover、PursonRecover、StrasRecover；不得把HuarenRecover猜入。各完整赋值hex/hash、源函数hash与逻辑偏移见`recovery-concat-proof.json`。现有terms中利维坦、贝里艾尔、别西卜、斯特拉斯已有候选；本次未新增阿斯塔罗斯/普尔森术语裁决，故优先采用Combo组，恢复组需沿现有译名核对后采用。

## 仍未解决与有界搜索边界

本轮检索63个Battle_Log/System_Log/Level_Up/Help/diction原条目，在本地逻辑包可解析函数中46个函数命中了候选key，32函数具有精确相关Strings字面值；完整提取在`source-entries.json`、`script-key-references.json`、`focused-script-literals.json`。名字/子串命中本身不是拼接证据。只对上述完整表达式作采用结论。

GetITEM和Objective_0/1消费者多达多个掉落/宝箱/装备/技能脚本；这些韩文宾格助词还被其他独立消费者共用。当前不局部删助词、不用中文空值污染未知消费链。

GetSP、GetItem2、Help/Change、Help/Left_Request_particle未在本轮函数内精确字符串消费者检索中闭合；动态构造键或原生消费者未排除。仍保留，不将缺少直接字面值说成未使用。

原生映像`build/xex-native-verification/final/disc1-pycryptodome.bin` SHA256 `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`中发现System_Log.JoinParty/JoinGuest/LeaveGuest的UTF16BE标签地址分别0x82110cb8/0x82110c68/0x82110d88，以及diction.Subjective的别处模板；仅定位尚不足证明中文语序。本轮未闭合Core.Object.Localize到该原生配置读取函数的调用链；父调查独立的反斜杠替换函数不能替代Strings标签全链证据。

## 重放

本地`python build/phase-286-ui-research/proof.py`实际输出`PASS combo assignment branches=4;recovery functions=7;typed numeric strings;no execution`，exit0；`python build/phase-286-ui-research/exp_proof.py`实际输出`PASS EXP exact concat assignments=2`，exit0。这些脚本及完整提取只保留在build目录，不提交游戏脚本原文。两个重放脚本已内嵌锁定5项原输入hash（含逻辑映像、表、Core与INT），先验证再解析；完整锁值见input-lock.json。源映像hash还需在正式采用器中独立验证；游戏内接受门槛仍由用户负责。

精简采用证据为`build/phase-286-ui-research/combo-adoption-proof.json`；`python build/phase-286-ui-research/compact.py`重新读hash锁定原逻辑包、表和Core，校验两Function metadata、四窗口以及六角色12返回分支的条件与跳转目标。Core声明还验证122=EqualEqual_StrStr与154=EqualEqual_IntInt的参数和BoolProperty返回。实际输出`PASS compact proof;4 assignment AST windows;6 typed getter branches/12 literal returns;reopened`，exit0；不依赖单一脚本hash推断语义。

后续闭合直接引用范围：`recovery_coverage.py`扫描整个MC2Game逻辑包与整个原生映像的ASCII和UTF16BE。12个恢复tag在逻辑包恰有14处，全部属于7个已验证完整赋值；原生映像中12完整tag及6个Recover词干均零命中。完整正向引用表为`recovery-reference-coverage.json`。此证据不覆盖其他package或动态构造key，不能宣称全游戏全部消费者。可在明确这个静态边界下采用6组12片段的前置动词，与已证所有直接消费者一致。阿斯塔罗斯、普尔森按韩文音译作新候选，不断言神话官方译名。合并9Combo+1EXP+12恢复的逐ID/hash建议为`adoption-candidates-22.json`，22项，不含Huaren。
