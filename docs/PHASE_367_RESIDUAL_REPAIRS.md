> 后续更正（阶段368）：本文12项pending是阶段367检查点；现已9项翻译、3项按完整原生零注册证明保留。本文关于Subject“任务查找用途”的推断已由完整参数／调用链纠正：检索使用整数QuestID，Subject只作显示标题。见[接续闭合](PHASE_368_PENDING_CLOSURE.md)与[消费者证据](LEGACY_DISPLAY_CONSUMERS.md)。

# 阶段367：碑文修复与逐项残留处置

日期：2026-11-11。接续用户“先修复图2，其余待核项逐项查清并处理”。
本轮实际改动 **41 个 Coalesced 字段、11 个包内 StyleName 字段**。
94 个上一轮未决身份均有逐项结果；**不是94条全部确认漏译，也不是全游戏清零**。

## 图2：已写入修复资源

`MC2Compose.int [Chapter11] Chapter11_27`：

```text
败者啊，将目光投向黑暗。
待兴盛之魂苏醒，南天之星将闪耀光芒……
```

结构化计划为 `locales/zh-Hans/inscription-fix-v37.json`，稳定ID为
`coalesced:53c21149e6042a65db33e839bdfbb97207a5fab20759ecc43cd6b622f03a5cb4`。
保留原有一个字面量 `\n`、嵌入路径、章节和键。

**Verified：**用户图2对应原字段；双盘当前文本资源有相同原值。完整包引用查询还找到
第二盘 `Ucave_Comp03_02.xxx` 的 export45：
`TheWorld.PersistentLevel.Main_Sequence.MC2SeqAct_ShowAlarmWindow_12`，
相对偏移41的完整字符串引用为 `<Strings:MC2Compose.Chapter11.Chapter11_27>`。
包SHA为 `92127236e18cc7ac73b88ba50dfe299bcf8554b20382e9978cde148d0883e3c2`。
截图本身仍不标识安装包版本；本轮没有启动游戏观察修复后的弹窗。

**翻译决定／High-confidence deduction：**既有阶段285因 `성쇄` 待考而保留整句。
这次参考同场景日文的 `隆盛の魂`，采用“兴盛之魂”，不是把它当作角色姓名。
日文字段值SHA为 `9049eca028941da3b3cf6dc4c0c99cc368ad82f33988cecf7203f40271fe6175`。
区域版本句式并非逐字一致；该采用决定**不证明韩文拼写错误或词源已经考定**。
旧阶段285的保留记录继续作为历史，不回写成“当时已确认”。

## 94个身份的逐项结果

完整台账：`locales/zh-Hans/omission-resolutions-v37.json`。
每项包含原ID／源值SHA／盘成员／定位、处理及下一项核查条件。

| 上轮集合 | 数量 | 本轮结果 |
|---|---:|---|
| 用户确认碑文 | 1 | 源锁定翻译，未改断行控制符 |
| UI拼接片段 | 10 | 按既有中文相邻字段／日韩同键语义本地化；动态组合仍需游戏复测 |
| 独立笑声 | 1 | `哈哈哈`；不推断未观察的触发场景 |
| 缺失／未使用台词源注 | 2 | 保留诊断含义，不编造剧情台词 |
| 删除标记 | 24 | `삭제`→`删除`；不是恢复24条正文 |
| 英文默认标签提示 | 3 | `默认值：请输入新标签值`，仍是诊断默认值 |
| 混合编码源字段 | 3 | 保留并继续列pending，详见下节 |
| 包内StyleName | 11 | `대포`→`大炮`，10资源／11盘成员，等长原位修改 |
| 任务进度QuestName参数 | 27 | 当前中文模板不消耗该参数；按精确模板SHA保留 |
| PlayerName | 3 | 兼作身份／查找键，保留；不做全局字符串替换 |
| Startup_int旧物品／测试任务 | 9 | 已解析对象、查到消费者线索，但正常游戏可达性未闭合，保持pending |

总计：**52 localized＋30有条件保留＋12继续待核**。23条既有editor/test等排除项
不属于这94项，v37逐字沿用其分类，未借用它们掩盖本轮未决。

### 其余40个Coalesced字段

计划为 `locales/zh-Hans/residual-text-fixes-v37.json`，必须应用在碑文修复之后。
`Subjective_2/3` 与现有 `Subjective_0/1` 一样使用带引号单空格 `" "`，不是删字段。
GetSP采用“点技能点已获得”，与当前GetEXP的拼接次序保持一致。
源中“未使用”“缺失台词”和删除标记全部保持诊断语义。

41处译文及“大炮”均通过现用七套中文字库覆盖检查，无新增字库或字体修改。
碑文两行General_15 advance为298/475，原值329/577；Subtitle为359/576，原值422/745。
SmallFont原本不覆盖韩文，故不拿它做原文宽度比较。
这是静态字形／宽度证据，不等于最终居中、裁切或动态组合的游戏验收。

### 27个任务参数：有界原生格式化路径

所有对象完整解析后，CompleteSentence都绑定当前中文模板，原参数分布为
`덫깔기`3项、`응급붕대`5项、`북부군처치`19项。
消费者链经过 `MC2HUDUI.NotifyShowQuestLog` 和 `MC2UIScene_Log.SetQuestLogText`。
韩版解码映像SHA：`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`。

Verified静态地址链：

```text
native wrapper 0x82320ed8
constructor 0x823584f8 → vtable 0x821328a8, method +0x290
implementation 0x82d2f358 → 0x82d2f1e0
format wrapper 0x82357a80 → 0x8238dfc8
0x82870b78 → 0x82870a48 → formatter 0x82872f18
```

formatter以r17读取格式、r24保存可变参数指针；0x82001c88是状态转换表。
27个实际解析后的中文模板逐字符重放都只进入state0，走0x82873224普通字符输出，
再到0x82873928继续；没有格式参数消费。模板已直接包含数量，未包含`%`。
因此**只对这些当前模板**，QuestName不是最终显示内容。模板哈希改变时必须重开核查。
台账保存模板ID、值SHA、转换表和原生映像锁；测试验证全27项state0合同。
这不是全程序运行／任意未来模板的不可达证明。

### PlayerName及9个测试数据字段

PlayerName出现于角色查找比较、`voc_bt_`语音键拼接和
`<Strings:MC2CharacterName.Default.`名称键拼接；StyleName则有CharacterStatus复制消费者。
保留三个PlayerName字段，避免改变身份查找。

9项具体为：CureSeed和HealLeaf各自ItemName/Description，Ice_Hat.Description，
throw_stone.Description，以及testquest的Subject/Description/SpecialReward。
整对象tagged stream都已消费到末尾，不是仅按附近字节猜字段。
完整引用查询发现 `MC2PlayerController.AddItem`（export25667，flags `0x20202`）
含 `data_item.etc.CureSeed`／`data_item.etc.HealLeaf` 的精确加载路径。
正式资源另外存在 `data_item.Recover.CureSeed_New`，不能用子串CureSeed命中代替旧对象引用。
Ice_Hat另有自身ItemName命中；throw_stone/testquest在本次查询中只有名字表命中。
**未命中不证明无动态引用**。ItemName另有事件比较用途，Subject另有任务查找用途；
这些源字段不通过随意改名、填空格凑等长、或仅凭Test路径排除。
后续仍需完成对象引用／动态加载入口到物品及任务UI的闭合，台账明确保留9 pending。

<a id="malformed-source"></a>
### 3个混合编码字段：定位了损坏，未伪造修复

当前物理解析只有无节名的ItemName／Accept／Cancel。原盘INT、JPN和当前版本的
MC2Game文档重编码UTF16LE载荷完全一致：390字节，SHA
`e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7`。
发现11处字节级CRLF；诊断性替换CRLF→LF后剩379字节，**奇数长度**。
若额外补一个零字节，可以看出AnswerChoice／Quest／UITest等原始形态。

Verified是损坏字节及原／现身份一致；“文本模式CR插入UTF16”属高置信推断。
需要补零的诊断不是可逆结构修复，更不是原生INI解析行为证明。
本轮保留完整源字节和三个pending，不调整通用解析器来消灭报错。
下一步是核实原生INI读取这份混合流时的节／键归属，再定义源锁恢复规则。

## 全量查询与审计门禁

从两份原盘和阶段365有效recipe执行4,145成员／2,551独立包的精确引用查询。
两盘原映像及有效资源前后哈希稳定，结构unknown包0，扫描独立输入7,709,065,216字节。
查询涵盖本轮44个Coalesced完整键、相关UI前缀、9个旧数据字段的对象名等，
UTF8／UTF16LE／UTF16BE，ASCII大小写不敏感；最终要求完整键后的`>`或NUL边界。
没有把`233_0`误计为`233`，也没有把CureSeed_New当成CureSeed旧对象。
唯一完整未决字段键命中就是图2的弹窗引用。

第一次结果写盘后，JSON重读比较因tuple/list类型差异退出1；完整扫描文件已存在。
后续逐包重新打开JSON并规范化计数完成，未重复冒充扫描；失败日志也保留。

新文本策略 `omission-screen-v37.json` 实际结果为：

```text
PRIMARY_FIELDS=18176 SUBTITLE_CUES=315 SCRIPT_RESIDUALS=25 CLASSIFIED_RESIDUALS=25 PREFIX_GAPS=0 UNCLASSIFIED=0 PENDING=3 EXCLUDED=23 CONFIRMED_PLAYER_GAPS=0 UNRESOLVED=3 OPAQUE_PRIMARY_DOCUMENTS=1 RESULT=UNRESOLVED
```

`--require-resolved`仍正确退出1。25是含目标脚本的字段数，26是含一个非脚本损坏字段的
总处置数；不相互替代。Core.int的opaque项保持。
此外阶段366的198条脚本token候选、443条未类型化字节候选，以及图像／原生尾部覆盖项
都未因本轮文本修复自动关闭；独立章节大卡 `UI-20261107-02` 也未被这个碑文修复代替。

## 可复现修改与回滚

遵循阶段365源构建流程得到锁定基线；不直接对未知游戏文件应用固定偏移。
通用基础设施不含中文字符串，语言内容独立在locale计划中。

```powershell
# 原Coalesced SHA ee45b275cbcd5275d65a48926bc26d7f2270fd7d19757ad3f7719f57edad0f60
python -B -X utf8 -m tools.build_coalesced $baselineInt `
  locales/zh-Hans/inscription-fix-v37.json --output build/replay367/inscription.int
python -B -X utf8 -m tools.build_coalesced build/replay367/inscription.int `
  locales/zh-Hans/residual-text-fixes-v37.json --output build/replay367/Coalesced.int
# final SHA 8671b08e5bd4732aad15729d44d8832778a06684980efd8b5776dd071b8fa79a

# 对tagged-string-fixes-v37/manifest.json的每项使用对应已锁定有效资源：
python -B -X utf8 -m tools.patch_tagged_strings apply $sourcePackage `
  --source-sha256 $entry.source_sha256 --plan $entry.plan --plan-sha256 $entry.plan_sha256 `
  --output $newPackage --report $applyReport
python -B -X utf8 -m tools.patch_tagged_strings rollback $newPackage `
  --source-sha256 $entry.output_sha256 --plan $entry.plan --plan-sha256 $entry.plan_sha256 `
  --output $restoredPackage --report $restoreReport
```

包工具仅接受BE未压缩包、offset4非stack/CDO、完整payload解析、明确对象/类/值SHA、
唯一顶层StrProperty及array_index。BE有符号长度＋UTF16LE含NUL；等长、不改控制符、
不重叠；修改后按新payload SHA重解析并反向逐字节比较。错版本、双应用、尾部、
重复JSON键、尺寸超限均报错；源文件保持、输出只创建新文件并重读。

源计划必须以UTF8/LF落盘后再算文件SHA，匹配仓库`.gitattributes`。
Windows默认文本换行会令本机hash通过、Git源码快照hash失败；本轮在规范化后重新运行
22次真实CLI（两阶段Coalesced＋10包正反向），全部产生相同成品／原始回滚身份。

新包按阶段365的`tools.compose_incremental_comparison`组合，并由
`tools.prepare_installer_sources`验证双盘。当前recipe SHA：
`ae4ae07c0e8d4736aabb1252dd32b36e83b314867207a1089b5441ba075af3ca`。
盘1仍471资源、盘2仍573资源；13个正文/包成员及2个TOC共15处资源身份变化；
两份DLC、未点名资源身份和游戏配置保持。没有新增ISO／完整游戏副本。

现有 `dist/MC2-display-repair-disc1` 已用`refresh_oneclick_probe`增量刷新：
新增资源0，变更15文件（12资源及3入口/状态文件）；原文对照、配置、存档、runs保持。
134个受保护文件前后SHA一致。备份和可审计journal在
`build/phase-367-residual-repairs/refresh-backup/`。

本轮真实三态命令／输入／完整输出／退出码记录在
`build/phase-367-residual-repairs/commands.json`与`VERIFICATION.txt`：
BASELINE52字段原值退出1；MODIFIED0原值退出0；隔离副本恢复11资源退出0，
ROLLBACK重新出现52原值退出1（预期旧状态复现）。修改版继续保留。
四件证据为同目录`MODIFIED_FILE.int`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`。

## 已更新的安装器

`dist/MC2-CN-v1.0.exe` 已替换为本轮双盘包，SHA256：
`f32ffaeeaae8e9c303f42c153eedbe2d21a68bbab556618abdbae39a094b330c`，
大小1,743,439,900字节。patch manifest SHA：
`b326f4b34c8ba81ce76fcc762f40e23e5de44e5c7beeb80600b78bdf1634cdc4`。

实际旧exe独立保存在本轮 `ORIGINAL_INSTALLER.exe`，不是按报告重建的替代基线。
旧安装器对新recipe有15个陈旧资源身份（退出1）；新安装器1044资源核对通过（退出0）。
另在独立exe副本恢复旧安装器，完整SHA相同、再次出现相同15项差异（预期退出1），
恢复版`--verify-only`通过。发布入口自检通过，756个payload条目、两份DLC及bootstrap
临时目录清理均核实；发布后再次比对recipe通过。修改版和当前测试树仍保留新状态。

没有删除原盘、旧证据或活动依赖；构建与回滚材料保留在本轮build目录。
自动化测试与同一提交远端四组Actions的最终观察值记录在同目录关闭记录；
静态资源／打包自检不会被记作用户游戏验收。
