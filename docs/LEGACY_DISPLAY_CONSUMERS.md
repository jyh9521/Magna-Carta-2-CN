# 旧物品与测试任务：显示字段消费者核查

阶段368，2026-11-11。本文补齐阶段367的9个 `pending-test-data-consumer`，
更正“看见字段参与函数调用，就把它视为身份键”的过度保守结论。
**九字段均按自身显示语义本地化；对象路径、类、KeyNumber、任务Id及玩法数据保持。**
这项决定不依赖证明旧对象在正常流程中不可达，也不以 `Test` 路径作为排除依据。

## 输入和证据等级

- 双盘共享 `Startup_int.xxx` 原输入：28,442,624字节，SHA256
  `089868b8120f382c22e71329530824e97f03d6c8fb37681a39224dd4fc89c91e`。
- 当前 `MC2Game.xxx` 包SHA256：
  `9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7`。
- 原生虚拟映像SHA256：
  `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`，基址 `0x82000000`。
- 本文的 **Verified** 指重新读取源锁字节、完整解码所列函数或完整对象tag，
  不是实际启动游戏。**High-confidence deduction** 另列，不升级为实机观察。

研究产物位于 `build/phase-368-pending-closure/legacy/`：
`EVIDENCE.json`、`proof.py`、`decode_consumers.py`、`typed_aliases.py`、
`item-name-aliases-typed.json`。它们不包含可发布的完整游戏文件。
函数证据保留实际包SHA、export、脚本范围、脚本SHA、完整AST及已消费全部字节的标记。

## 九字段的处置

| export／对象 | 字段 | 原值 | 采用译文 | 消费者与保护项 |
|---|---|---|---|---|
| 443 `data_item.etc.CureSeed` | ItemName | 큐어 시드 | 疗愈种子 | 显示名及对象间事件比较；所有精确显示名别名已查清 |
| 443 同上 | Description | 한넘 30% 회복 | 单体恢复30% | 物品说明显示；保留单体、30% |
| 444 `data_item.etc.HealLeaf` | ItemName | 힐 리프 | 治愈叶 | 显示名及对象间事件比较；所有精确显示名别名已查清 |
| 444 同上 | Description | 전부 30% 회복 | 全体恢复30% | 物品说明显示；保留全体、30% |
| 483 `data_item.Test.Ice_Hat` | Description | 더위 확률 10% 감소 | 炎热概率降低10% | 物品说明显示；保留10%，不改类型和效果 |
| 491 `data_item.Test.throw_stone` | Description | 던져서 데미지 | 投掷后造成伤害 | 物品说明显示；不编造伤害数值 |
| 1306 `data_quest.Test.testquest` | Subject | 테스트퀘스트 | 测试任务 | QuestInstance.Title → UILabel；检索键是Id，不是Subject |
| 1306 同上 | Description | 테스트하자 | 来测试吧 | QuestInstance.Desc → UILabel；保留测试语义 |
| 1306 同上 | SpecialReward | 없음 | 无 | RewardItemName[2] → UILabel；不新增实际奖励 |

旧CureSeed与正式 `data_item.Recover.CureSeed_New` 不是同一玩法对象。
正式INT的全体200点恢复说明不替换这里的单体30%。
`Comment`、ASCII对象名、路径、KeyNumber、任务Id、Type、Target、价格、数量和Stats均不在九字段修改中。

## Verified：Subject不是QuestID

完整解码的真实调用和赋值如下；参数名相似不表示身份用途相同：

1. `MC2Quest.AddNewQuest`（export27007，54字节）与
   `MC2QuestManager.AddThisQuest`（27189，71字节）传入
   `AddNewQuest(Id, Subject, Log_QuestBegin, Quest, bDummyQuest)`。
2. `MC2QuestManager.AddNewQuest`（27197，273字节）的签名首参数是
   **QuestID:IntProperty**，第二参数是 **Quest_name:StrProperty**。
   已有任务判断比较 `QuestInstance.Id == QuestID`；第二参数用于通知文字。
3. `FindQuestInstance`（27265，84字节）的唯一输入为 `QuestID:IntProperty`，
   同样逐个比较任务整数Id。CompleteQuest和FailQuest也按Id定位，名称只进入通知。
4. `MC2QuestInstance.SetQuestInfo`（27127，641字节）在脚本偏移
   `0x6a/0x7e/0xa6` 分别赋值
   `Title=Quest.Subject`、`Desc=Quest.Description`、
   `RewardItemName[2]=Quest.SpecialReward`。
5. `MC2UIScene_QuestJournal.FindQuestRewardLabel`（33826，675字节）
   把上述三个值分别传给 `UILabel.SetValue`；SpecialReward仅按非空字符串检查显示。
   `MC2UIScene_QubeMail.FindQuestLabel`（33740，691字节）也把Subject和Description直接送到UILabel。

因此翻译这三个字段不更换任务身份。整数 `Id=99999` 保留。
已保存QuestInstance内的旧Title/Desc缓存是否在某条读档路径重新刷新，是另一项运行时状态问题；
本文没有修改存档，也不宣称资源翻译追溯改写既存缓存。

## Verified：ItemName比较的是两个对象自身的字段

`MC2ItemManager.TriggerUseItemEvent`（13075，263字节）完整脚本执行的比较为：

```text
DynamicCast<MC2Item>(evt.Item).ItemName == Item.ItemName
```

事件来自 `Sequence.FindSeqObjectsByClass(MC2SeqEvent_UseItem, ...)`；
匹配后调用该事件的 `CheckActivate`。完整函数没有硬编码韩文字符串，
也不是把名称与保存的旧韩文键相比较。

`MC2ItemManager.CheckExistingItem`（13032，111字节）则按
`ItemList[I].KeyNumber == ItemNew.KeyNumber` 判断物品是否已有。
KeyNumber不随译文更换。

### 精确别名与正式物品的区别

重用源锁定的双盘4145个包成员／2551个不同包的FString及脚本字面量census，
再逐个重新解包、完整解析相关对象tag，并核对其包SHA仍匹配阶段367：

- 两旧名称共有18个存储命中。
- **只有本轮的2个字段是ItemName**。
- 其余16个全部是 **Comment**，包括CureSeed_New和CureSeed_Del。
- 正式CureSeed的实际ItemName为 `<Strings:MC2Item.Recover.CureSeed>`，
  不是其Comment中的 `큐어 시드`。它不构成旧显示名等值比较的别名。
- 原生映像中两旧名称按UTF-16BE、UTF-16LE、UTF-8、CP949搜索均无字面量命中。

这里的负向搜索只说明指定编码和已筛选序列化字符串的边界，
不证明动态生成值或整个程序不可达。正向依据是实际属性到属性的比较，
不是“没有搜索结果所以可以删除”。

## Verified：对象加载使用路径，Type3不进入Type5选择缓存

- `MC2PlayerController.AddItem`（25667，254字节）实际传给SpawnArchetypeActor的是
  `data_item.etc.CureSeed`／`data_item.etc.HealLeaf`，然后AddNewItem。
  两路径保持不变。
- `MC2CheatManager.AddItem/RemoveItem` 虽把形参叫ItemName，
  实际把该形参交给DynamicLoadObject加载对象；它不是读取MC2Item.ItemName显示属性。
- `MC2Party.LoadNAddPartyItem`（15991，102字节）实际把ItemPathName交给
  AsyncDynamicLoadObject。`MC2SaveData.PPItemInfo`也声明ItemPathName、Count、PlayerName等，
  不能把形参名相近误读成显示名称存档身份。
- 存档确有LastSelectedItemName。原生包装函数
  `0x822de3b0–0x822de43c`调用GetLastSelectedItemName，
  `0x8245e880`和`0x82e18a30`两个调用点把返回的FString存入状态字段。
- 完整解码的 `MC2UIScene_ButtonX.GetLastSelectedItemName` 返回SkillNameList当前项；
  `GetItemList`（11049，476字节）只有在 **MC2Item.Type == 5** 时把ItemName加入该列表。
  本轮旧CureSeed/HealLeaf对象的实际序列化 **Type == 3**，所以不进入这条名称选择缓存。

上述正向链足以区分资源身份、库存KeyNumber与UI缓存。
没有声称已经证明全部原生存读档实现或所有动态消费者。

## 物品说明的原生显示链

**Verified字节与类绑定：**

- `0x82d23cb0` 的类工厂以 `UMC2UIScene_Item` 和ctor `0x82359010` 注册类；
  ctor写入vtable `0x82134d40`，槽 `+0x2d8` 指向 `0x82d20748`。
- 完整函数 `0x82d20748–0x82d207dc` 在列表非空时读取当前选中物品，
  以对象 `+0x1c8` 为FString源，在 `0x82d20798` 调用已验证的赋值helper
  `0x822d0548`，然后把局部字符串传给UI字段的虚方法。
- 商店说明函数 `0x82d42810–0x82d42b24` 同样读取选中物品的 `+0x1c8` 并送UI字段。

**High-confidence deduction：**将该偏移命名为MC2Item.Description，
依据已知ItemName在 `+0x1bc`、FString宽12字节、连续成员声明顺序
Comment→ItemName→Description→ShortDescription及物品界面Description字段。
本文保留这一级别，不把静态布局对应伪称为运行时反射或截图验收。
四个Description字段按实际文字语义翻译，不改变使用物品的数值逻辑。

## 独立重放

仓库根目录：

```text
python build/phase-368-pending-closure/legacy/typed_aliases.py
python build/phase-368-pending-closure/legacy/proof.py
```

第二条实际输出，退出状态0：

```text
PASS full_scripts=25 event_equality_cases=9 keynumber_cases=3 quest_id_cases=2 aliases=18 itemname=2 comment=16 ui_sinks=3 native_description_reader=verified_bytes game_execution=false
```

受控测试直接使用重新解码的字符串等值、KeyNumber等值、QuestID等值表达式：
翻译前后9个事件物品配对、3个库存查重输入、2个任务ID输入的逻辑结果相同。
它不是整个虚拟机执行，也不代替游戏内排版和旧存档复测。
三态资源验证、双盘集成和增量刷新由阶段368主记录另行给出。
