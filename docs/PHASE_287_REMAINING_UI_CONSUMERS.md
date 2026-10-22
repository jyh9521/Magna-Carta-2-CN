# Phase 287：剩余 UI 片段的实际消费者与七字段采用组

## 结论

本轮从 phase286 的剩余语言字段清单实际提取出 **26 条 MC2UI 字段**。七条已闭合为一个应当一起采用的原子组；另外 19 条保持原文，不能将字面值零命中解释为未使用。

| 字段 | 建议译文 |
|---|---|
| diction.Objective_0 / Objective_1 | 已 / 已 |
| Battle_Log.GetITEM | 获得 |
| System_Log.GetWeapon / GetItem3 | 获得 / 获得 |
| System_Log.SkillSubject | 的 |
| System_Log.GetSkill | 习得 |

这不是删除韩文助词的空值绕过，而是将韩语宾格结构整体改为中文「名词短语 + 已 + 获得／习得」。角色与技能名之间使用中文「的」。原版脚本嵌入的 ASCII 空格全部保留，不在本轮改脚本以消除空格。离线例句为 `道具名已 获得`、`100席德已 获得`、`图标道具名（3）已 获得`、`人物名的技能名已 习得`；这些例句验证拼接语法，不是游戏截图或数值补全。

逐稳定 ID、源 hash、目标值见 `build/phase-287-ui-research/adoption-candidates.json`；可提交的结构化精简证据为同目录 `adoption-evidence.json`，原子成员／目标 hash／依赖 joins 为 `review-groups.json`。建议证据落点为 `locales/zh-Hans/candidate-decisions/remaining-ui-assembly-evidence.json`，不提交任何完整游戏包。

## 直接源与边界

输入只读、执行前锁定：

- `build/phase-282-verification/MC2Game-logical.bin`：`e2a49cdd67c2b49f9b91fb517a49de33262ada4f3ec5a65c776a7d3126d1ecf4`。
- 对应 `package-tables.json`：`0ea25716085840912c0d658d4daf8e9283f1a5604e77856a1210a9d22b5c4699`。
- `build/phase-283-verification/Core-logical.bin`：`5ac2c9745bdf6220ddb3dbe898ef88b1c8ac84c882b06816e8257ad5b4c6e2a9`；Core tables：`3cd1cd977e7552b202ae88ee2f10db74d3056d4770a7ddbed7de8ead26434c0b`。
- 原版 `build/disc1-selected/MC2Game/Localization/Coalesced.int`：`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。
- 原生虚拟映像 `build/xex-native-verification/final/disc1-pycryptodome.bin`：`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`。

全部证据来自仓库已保留的原版序列化脚本、类型声明和原生字节；本轮没有启动游戏。所有脚本偏移指解压逻辑包坐标；原生地址以虚拟映像基址 `0x82000000` 为准，不是 PE raw pointer。

`coverage.py` 对整个 MC2Game 逻辑包和整个原生映像执行 ASCII、UTF16BE 的**大小写不敏感**完整 tag 搜索。七候选 tag 总计 **47 处**，全部位于已识别、逐字节锁定的完整 typed 字符串赋值窗口内，分别为 Objective_0 15、Objective_1 14、GetITEM 10、GetWeapon 2、GetItem3 2、SkillSubject 2、GetSkill 2。原生完整 tag 零命中。它证明的是这两个输入中的完整直接引用，不排除其他 package、动态构造 key、间接配置读取或运行时字符串。`adoption-direct-coverage.json` 保留每个实际偏移和归属表达式。

## Typed 拼接来源

`typed_assignments.py` 使用仓库 Function metadata 和 property reader，读取真实局部／参数／字段类型。它将 StringConst、LocalVariable、InstanceVariable、Context、StructMember、动态数组取值、IntToString、二元 Concat 与 ConcatEqual 组成有界表达式，验证整段赋值范围、源字节 hash、目标 StrProperty 和局部所属函数。Core.Object 声明确认 token112 为两个 StrProperty 到 StrProperty 的 Concat_StrStr，扩展 token322 为 ConcatEqual_StrStr；后者同时校验 EatReturnValue 的导入路径为 `Core.Object.ConcatEqual_StrStr.ReturnValue`。

七候选共涉及 **14 个函数**；提取中另含 NotifyLevelUP，只作未采用组研究。完整窗口证据不是整个脚本反编译，不宣称所有分支控制流已经解析。VirtualFunction 的 FName、候选序列化声明和返回类型被保留，但不将名称匹配误称运行时 dispatch 证明。

- `MC2BattleYupa.LearnSkill`（export2716）：两个初始化分支分别从 `ParentPawn.PlayerName` 生成 MC2CharacterName.Default tag，接 SkillSubject，然后接 `GetSkillData(...).SkillNameText`（StrProperty）；后续两个分支选择 Objective_0/1，最终追加 GetSkill。初始化脚本偏移486／1245，助词偏移660／714和1440／1494，最终后缀765／1545。技能名是实际 `MC2SkillData.SkillNameText`，不是凭局部变量名猜测。GetSkillData 的运行时调用 dispatch 不作断言，序列化字段和返回类型足以约束此拼接的字符串槽。
- `MC2UIScene_AlarmWindow.SetAlarmTextsIcon`（11146）：`NewStr = GetIconString(MC2Item(Item[idx])) $ MC2Item(Item[idx]).ItemName`；真实 Number 数组决定 `N`（IntProperty），单件直接加 `tempStr $ GetItem3`，多件先加 BracketL、string(N)、BreaketR，再加相同助词与后缀。两个括号 tag 的原始拼写均保留，不把数值或图标改为翻译文本。最终表达式偏移275／336，初始66，助词175／221。
- `MC2SeqAct_ChangeSubEquipData.InitSubEquipData`（27916）、`MC2SeqAct_ChangeWeaponData.InitWeaponData`（27934）：初始 StrProperty 来自实际物品对象的 `MC2Item.ItemName`，Objective_0/1 后最终追加 GetWeapon（偏移873／882）。
- `MC2SeqAct_GiveItemToPlayer.Activated`（28515）：真实 IntProperty 转 string，后接 Sid 与 Objective_0，最后追加 GetITEM。完整 compound 赋值偏移152，最后赋值242。没有补充、删除或重排金额。
- `MC2DropItemActor.AddItemManager`（7624）、`MC2DropItemPlaceableActor.AddItemManager`（7670）：输入来自 `sItemExt.ItemName`、真实数量与既有括号／逗号／Sid tag，组装成 strItem 后选择 Objective_0/1，再追加 GetITEM；不是单一物品名的盲目假设。
- 两种 IncompletionBomb.AddInvenItem（8846／8982）、GiveCollectPlantItem（9299）、GiveInvestItemToPlayer（12844）、ExtractKamond（18173）、MakeKamond.Activated（28666）均直接绑定 `MC2Item.ItemName` StrProperty，再采用同一 Objective_0/1 + GetITEM 尾部结构。
- TreasureBox.OpenItemBox（31608）输入可包含金额、物品名、数量括号和逗号组成的复合名词短语；最终同样先追加 Objective_0/1，后追加 GetITEM。因此候选中文助词必须兼容整个名词列表，不能硬填单数单位或具体物品名。

## 其余 19 字段与下一步

- GetSP、ReceiveCommunication、AcceptCommunication、AskCommunication、GetItem2、Help.Left_Request_particle、Help.Change、Change_Guidence_Massage.Guidence_Massage、Subjective_2／3：两个锁定输入均没有完整 tag 直接命中。下一步需要定位动态键／原生 UI 消费链或其他 package，不凭 key 名称补中文语序。
- HuarenRecover_1／2：本轮全字节扫描各发现一处，位于 MC2Game 逻辑偏移8648463／8648513。它不属于 phase286 那七个 AddHealthPercent 函数，不能照搬“恢复量”槽；下一步单独定位所属函数并解析 typed 中段，优先于重新进行零结果宽泛术语搜索。
- LevelUp 与 Subjective_0／1：脚本 `MC2Pawn_GameDatas.NotifyLevelUP` 已确认从 `PlayerName` 生成角色名 tag，依次加 Subjective_0／1 和 LevelUp。但 Subjective_0／1 同时还有原生消费者，不能只凭这一支就修改共享助词。
- JoinParty、LeaveParty、JoinGuest、LeaveGuest 和 Subjective_0／1：原生地址候选全函数分别是 `.pdata` 范围 `0x82d87fa0–0x82d88570`、`0x82d97220–0x82d97a5c`。实际字符串存在小写变体 `<Strings:MC2UI.System_Log.Leaveparty>`，所以只作大小写敏感检索会漏掉该消费者。两个函数均有先组装 Subjective 标签、再追加入队／离队标签的分支，但 FString helper 的真实行为和前段所有路径尚未绑定，不纳入本次采用组。
- Subjective_0／1 的另一原生消费者位于 `0x82d43300–0x82d43508`，其中整个模板为 Subjective + MC2UI_Shop.Kamond shop Menu_Description.work_E，后者原义“完成了”。修改共享助词时必须同时兼容此合成结果消息。

`native_consumers.py` 的 lis/addi 80 字节窗口仅产生候选地址加载；中间寄存器可被改写，故此方法**不是完整 xref 覆盖或实际数据流证明**。原生逐函数文本和 `.pdata` extent hash 已保存，后续从实际调用与 helper 语义继续，不重复将候选匹配当结论。

## 独立重放

从仓库根目录、UTF8 输出执行：

```text
python build/phase-287-ui-research/typed_assignments.py
PASS exact typed string assignments;functions=15;assignments=81;no execution
python build/phase-287-ui-research/coverage.py
PASS seven candidate tags;direct hits=47;all exact typed assignments;native hits=0;other packages/dynamic keys not excluded
python build/phase-287-ui-research/adoption.py
PASS adoption=7;typed functions=14;direct refs=47;held=19;all candidate/source/target locks reopened
```

以上三条均实际 exit0；第一条另打印每个完整表达式的定位摘要。`all_coverage.py` 保存全部26字段的正负直接命中表。只有七条候选及证据可交给父流程实际回填，最终正式批次、双盘、字体、控制码、增量测试目录、回滚和推送由主流程独立验证；本报告不替代游戏内验收。
