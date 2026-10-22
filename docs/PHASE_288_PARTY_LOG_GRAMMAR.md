# Phase 288：共享主语助词、升级与队伍日志的实际拼接闭环

## 实际采用建议

新增七字段，并将既有 `MC2UI_Shop.[Kamond shop Menu_Description].work_E = 制作完成！` 锁为不变依赖。候选不是空白删助词方案；两种韩文主格后缀共同改为中文完成体「已」，所有后缀保留自然动词短语。

| 字段 | 原文 | 候选 |
|---|---|---|
| diction.Subjective_0 | 가 | 已 |
| diction.Subjective_1 | 이 | 已 |
| Battle_Log.LevelUp | 레벨업을 했습니다. | 升级 |
| System_Log.JoinParty | `\n파티원으로 추가 되었습니다.` | `\n加入队伍` |
| System_Log.LeaveParty | `\n파티에서 제외 되었습니다.` | `\n离开队伍` |
| System_Log.JoinGuest | `\n게스트로 참가 했습니다.` | `\n作为临时同伴加入队伍` |
| System_Log.LeaveGuest | `\n게스트에서 제외 되었습니다.` | `\n不再作为临时同伴同行` |

四个行首 `\n` 是原有两个字符的功能换行标记，全部逐值保留，脚本嵌入 ASCII 空格不变。Guest 沿用既有Tutorial_Scene_11/12的「临时同伴」称谓，不另造「临时队员」或「嘉宾」。离线组装形态为「人物名已 升级」、「人物甲、 人物乙已 \n加入队伍」、「人物名已 \n不再作为临时同伴同行」。不将例句当作实际截图或自动排版验收。

## 原始输入与精简证据

全部来自已有原版输入，无游戏启动、无原生运行、无新游戏副本：

- 原生虚拟映像：`build/xex-native-verification/final/disc1-pycryptodome.bin`，SHA256 `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`，映像基址 `0x82000000`。地址不是 PE raw offset。
- MC2Game逻辑包：`build/phase-282-verification/MC2Game-logical.bin`，SHA256 `e2a49cdd67c2b49f9b91fb517a49de33262ada4f3ec5a65c776a7d3126d1ecf4`；tables `0ea25716085840912c0d658d4daf8e9283f1a5604e77856a1210a9d22b5c4699`。
- 原版INT：`build/disc1-selected/MC2Game/Localization/Coalesced.int`，SHA256 `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。
- Core逻辑包及tables沿用phase287锁，重放时重新核对，见研究目录 `input-lock.json`。

研究目录 `build/phase-288-party-research`：`adoption-candidates.json` 提供七个稳定ID、原文／译文及其UTF8 SHA；`adoption-evidence.json` 提供完整16函数的.pdata边界与字节hash、精确调用指令窗口、两个无.pdata叶函数的终止窗口、四个重新解析的typed升级赋值及literal字节定位；`review-groups.json` 提供七个新成员与10个joins；既有work_E通过evidence.dependent_existing_targets额外锁定id/source_sha256/translation_sha256/原批次，既有项不重入新批次。提交精简证据时建议落点 `locales/zh-Hans/candidate-decisions/recovery-party-assembly-evidence.json`，该目标路径已经写入组证据锁。

## Verified：实际 FString helper 语义

这里没有把「调用同一个函数」或「附近lis/addi」当作拼接证明。完整helper字节显示：

- `0x822d04b0` 从TCHAR指针构造FString：读取16位首字，非空调用 `0x8286e0e0` 取UTF16长度＋终止字；保存count/capacity，复制 `count*2` 字节。
- `0x822d0548` 是**赋值**而不是追加：对比左右地址，复制右侧count，分配后复制完整UTF16数据。因此主函数中的「拼接临时结果 → 调它」表示回写，不是再次重复拼接。
- `0x822d0438` 是FString复制构造。
- `0x822d0690` 追加右TCHAR：非空左侧的插入偏移是 `(old_count-1)*2`；右侧长度扩容后从旧终止字处复制。右空直接返回，左空采用首字复制路径。
- `0x822d0730` 三参数是out、左FString、右TCHAR：将左侧拷贝至局部，以上述helper追加右侧，再复制结果至out并返回out。
- `0x822d07f8` 的右参数是FString：根据右count取其data或空常量，然后转入 `0x822d0730`。
- 叶函数 `0x8286e0e0` 逐16位字扫到零，返回长度；`0x8286e6a0` 从右指针逐16位字复制至左指针且包含零终止。两个叶函数没有.pdata记录，使用实际第一条blr闭合的独立窗口，不编造函数元数据。

证据以指令窗口和完整helper hash双重锁定，主流程可独立重放。动态内存分配成功与实际字符串运行结果仍属于未执行状态。

## Verified：两个完整队伍日志前段

`0x82d87fa0–0x82d88570` 完整函数读取：

1. 栈`+0x58` 初始化为 `NONE` sentinel；`0x82110b30`固定格式是 `<Strings:MC2CharacterName.Default.%s>`，`0x82110b80` 是 `<Strings:MC2UI.Punctuation.Comma> `。
2. 外层逐输入字符串匹配已有列表；一支取对象`+0x3a8` FString，另一支取`+0x44` FString。空名跳过。非空时将同一名称保留到局部，并将名称data指针传入格式化函数；首项直接赋值，后续先追加Comma，再追加格式化名称。
3. `0x82d88428` 以实际累计列表调用韩文末字检测helper `0x82ded2c8`，然后分支分别追加Subjective_1或Subjective_0。两条中文均为「已」，所以中文末字不依赖韩文받침算法的分支结果。
4. 原有显示flag以及累计列表非NONE的判断通过后，r16选择LeaveGuest或小写变体 **Leaveparty**；两分支都实际追加至相同累计列表，再传给显示函数。不能漏掉小写变体而断言没有LeaveParty消费者。

`0x82d97220–0x82d97a5c` 完整函数读取：

1. `this+0x100` 初始化为同一NONE sentinel。前段包含查找／移除已有对象、按输入字符串查找或加载对象、必要时生成对象；这些控制及资源操作保持原样。
2. 完成上述分支后，实际字符串构造点统一读取对象`+0x3a8`；空名跳过。固定格式仍是角色名tag，首项赋值，后续Comma＋格式化名。完整指令链区间 `0x82d977b0–0x82d978ac`。
3. 结束循环后，`0x82d97930` 检测累计列表并追加Subjective_1或_0；原有flag及非NONE判断通过后，flag位选择JoinGuest或JoinParty，追加后显示。

名称格式化wrapper `0x82324c50` 转入 `0x8238dfc8`。后者保存变参r5–r10，将format指针和参数区交给UTF16格式化例程 `0x82870b78 → 0x82870a48 → 0x82872f18`，扩容重试后构造结果FString。**Verified（仅本次plain `%s` 路径）**：实际字符分类／状态表 `0x82001c88` 令 `%` 将state0变为1、`s`将state1变为7；实际jump table `0x82001ac8` 的s项指向 `0x82873380`。percent分支清零flag，未修饰的s读取首个8字节对齐变参中的指针，flag0x20为零时进入UTF16支路 `0x82873408`；`0x82873420`逐16位字扫描，长度以地址差除2计算，然后 `0x828738b4`以实际指针和字数调用 `0x82872e78` 的lhzu输出循环。因此固定格式确实插入名称TCHAR而非猜测formatter。完整机器与表／跳转值已锁入证据；其它格式码及错误运行路径未作全量证明。

## Verified：升级脚本与商店共享后缀

- `MC2Pawn_GameDatas.NotifyLevelUP`，export16276，script SHA `09acf4a86dddfe2ff522403924dcd2b66af8656e6bf309eaa0fd886c647498a7`，460字节。重放脚本通过已有有限表达式解析器**重新解析原字节**四个完整赋值，offset65、165、220、272；真实StrProperty tempStr先从 `MC2Pawn.PlayerName` 构造Default角色名tag，然后加Subjective_1或_0，最终加LevelUp。不是只读取前轮JSON。
- `0x82d43300–0x82d43508` 商店完整函数中，实际物品名从解引用对象`+0x1bc` FString赋值至`this+0x320`并送往一个UI字段。随后新建局部空FString，按韩文末字检测结果通过 `0x822df3f8` **赋值整个模板** `Subjective_1/0 + ASCII空格 + work_E`，送往另一个UI字段。它不是单一物品名＋助词＋完成后缀的同一FString，不应在文档中拼成虚假的单字段。
- work_E既有译文为「制作完成！」，原文「완성되었습니다!」。本轮保持不变，结果独立后缀字段为「已 制作完成！」，与新的共享助词兼容。证据的dependent_existing_targets锁定它及既有批次，避免以后悄然改变依赖语法；新批次原子组成员仍只有七个新字段。

## 边界与独立重放

精确全tag存储搜索覆盖整个MC2Game逻辑包、整个原生映像的ASCII和UTF16BE，大小写不敏感；它记录的是**literal存储**，不是literal所有代码xref，不将零命中当未使用。三个实际消费者函数及helper的逐指令数据流是本次采用的正证据。其他package、动态拼接key、未识别间接消费者仍未排除。没有游戏内排版、显示、语音或触发流程验收声明。

仓库根目录执行：

```text
python build/phase-288-party-research/proof.py
PASS candidates=7;native complete functions=3;native/helpers=16;typed levelup assignments=4;existing work_E locked;4 literal breaks retained;no execution
```

实际退出状态0；三个交接JSON均重新打开解析。建议主流程将七候选直接纳入实际批次，重新检查字体、控制码、双盘重建、增量测试目录与隔离回滚，而非只保存研究记录。
