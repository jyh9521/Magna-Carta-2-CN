# 阶段370：31个英文动态占位字段

## 结论与处理

这31项不是31条遗漏的固定英文提示。实际消费者把它们作为技能名、物品名、
任务标题、教程标题和新连击说明的动态标签；清空路径也真实存在。
本轮按原生空态把31个序列化英文默认值改为**规范空FString**，
不伪造“初始文本”“物品名称”“任务标题”“暂无数据”等玩家提示。
真实中文数据、控件标识、资源引用、脚本及显示逻辑均保留。

| 逐项编号 | 原默认值 | 控件／数量 | 实际写入与空态 |
| --- | --- | --- | --- |
| UI-01 | initial text | ButtonB.TextB，1 | 固有技名称；缺数据写空 |
| UI-02～05 | initial text | TextB_Shadow_0～3，4 | 与正文共用一次FString，逐层写入 |
| UI-06～11 | Item Name | QuickMenu.List_0～5.ItemName，6 | 清空后按物品数据写入名称 |
| UI-12～20 | Quest Title | QuestJournal.Content_0～8.List.QuestTitle，9 | 清空后按任务数据写入标题 |
| UI-21～22 | Level UP / Level Up | Point_Text_0～1，2 | 新连击描述；未用行清空并隐藏 |
| UI-23～31 | NO DATA | RemindTutorial.Content_0～8.List，9 | 清空后按教程数据写入标题，不是真实“无数据”提示 |

完整31个对象路径、字段路径、旧／新payload摘要在
`locales/zh-Hans/ui-defaults-v40.json`；逐项消费者结论在
`locales/zh-Hans/ui-defaults-audit-v40.json`。
历史阶段369的“未验证原生覆盖”记录不回写成当时已完成。

## 消费者证据

### Verified：序列化对象、函数体、数据源与原生指令

- ButtonB：注册表绑定的`SetInherentSkillName`实际函数是`0x82d66798`，
  不是Function中的空native存根。它从空FString开始，正常数据链填入技能名，
  缺数据也进入共同写入段；同一次结果写正文及四层阴影。
- QuickMenu：数据更新`0x82d4ed88`先执行`0x82d55e68`清空，
  然后按`ItemName`标识写入物品对象的名称FString。标签标识本轮不翻译。
- QuestJournal：数据更新`0x82d5c530`先清空全部列表标签，再由
  `0x82d5c028`写入任务记录标题。不是只按“QuestTitle”名字猜用途。
- RemindTutorial：`InitTutorialList`／`SetTutorialList`绑定到
  `0x82d59bb8`／`0x82d591d0`，数据更新`0x82d59080`同样先清空再填行。
  按钮字幕和子UILabel分别有实际setter链。
- LevelUp：`FindWidgets`精确绑定两行；`SetInformation`依据本级新连击数量
  分0／1／2行处理，`SetLevelUpDescription`组合流派名与`Combo_n`中文，
  `ClearLevelUpDescription`写空并隐藏。**OpenScene／FadeIn早于SetInformation**，
  因而不作“旧英文绝不可能在初始化窗口出现”的推断。

名称表、constructor／vtable关联、完整函数边界、指令窗口摘要及脚本摘要由
`references/ui-defaults-research.lock.json`锁定。原生静态链不是游戏执行日志。
源AST受控模型覆盖升级0／1／2行与真实中文组合，属于离线正控，不是VM／游戏实测。

### 现行动态文本与保留项

动态内容仍来自现行中文Coalesced／Startup数据，而非上述英文默认值。
本轮保持Coalesced摘要`8671b08e5bd4732aad15729d44d8832778a06684980efd8b5776dd071b8fa79a`、
Startup摘要`27f179a768b8c18dc884e2d9f6499d0fc1b5b07b41c1b7e181e0398facb39228`。
字体与纹理也不修改；清空默认不需要新增字形或以缩小字号遮掩问题。

Quick物品数据复核还遇到两个原盘就存在的失效Strings标识：
`Anesthetic`、`PaticleOfFire1`。原／现名称字段相同，原／现文本库均无对应完整键；
它们不是这31项中的英文默认值，也不是确认的韩语文句。
不把失效标识猜译成新物品名，不宣称已经观察到它们进入实际背包。
此发现与31处占位处理分开保存。

现行任务／教程目录的152个非空Name值均含中文，2,075个目录值无审计范围内韩文。
有界包选择中的201个明确序列化标题为200个中文目录引用和1个既有“测试任务”literal。
这份补充检查不覆盖152个未显式序列化字段的继承值、153个超出其简化prefix解析的实例；
也不改写既存存档缓存，不冒充全部实例或原生datastore查找已经实测。
完整来源与分母见`references/ui-defaults-dynamic-titles.lock.json`。

两段教程记录脚本的0x55 ArrayAddItem只在只读研究decoder扩展：
446版本使用array表达式与item表达式，不套后来版本的skip／end参数标记。
格式依据Eliot van Uytfanghe的Unreal-Library（MIT，提交
`8236c39b79e30887a487ecf9b018204e430a5ebc`）；三份上游文件URL／SHA在本轮研究锁中，
生产VM parser没有因此放宽。native `+0xb4`／`+0x78c`的布局命名仍为High-confidence deduction，
而不是运行时反射取得的成员布局。

## 可重建的嵌套字符串改写

`tools.rebuild_tagged_strings`增加显式v2 profile，v1宽字符单层规则不变。

1. 核对整个输入包SHA／长度、对象class、原对象payload与逐字段原字节。
2. 字段采用完整indexed path；旧编码显式为ASCII或UTF-16LE。
3. 新非空文本使用UTF-16LE FString；本轮空态用四字节零count，不加空格、不写假译名。
4. 递归重建所有祖先StructProperty长度。对象其余属性、顺序、NetIndex、
   FName、object reference及终止标记不变。
5. 数组必须在源锁计划中逐路径声明为object-reference array；核count、字节长度、
   每个索引范围，拒绝未知数组和未用声明。这里的`InactiveStates`与`Children`
   由Engine的UIScreenObject属性定义5684／5687及其inner类型独立确认，
   31个对象的类链都确实继承UIScreenObject。
6. 不移动未知native数据，不接收未知对象尾部；完整新对象附加到文件尾，
   原前缀只改31个export记录的size／offset，其他export逐字节校验。
7. 独立回滚通过原始摘要和规范forward replay验证，不只比较个别文本。

同包现有QuickMenu.Description等控件已使用相同零count表示空FString。
为可靠回滚而保留的旧payload不再被这31个active export引用；
原始字节扫描仍可能找到英文，因此验收必须按active export与字段路径读取。

### 实际资源身份

- 输入MC2Game.xxx：`9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7`，68,943,872 bytes。
- 输出MC2Game.xxx：`076d165efe18b64d36b5106dc3913aada71ff80f790ee56a7c77a87d7477408b`，68,976,640 bytes。
- v2计划：`132f65ca482479c33c61d242156f50145778b4fe6aa8ab7a0ea1b441ee601719`。
- 两盘共享同一修复内容；471／573资源集合不变，只有两盘MC2Game与TOC共4条记录改变，2个DLC不变。

### 重建与回滚命令

先按前轮流程获得上述hash匹配的输入包。`SOURCE`、`OUTPUT`与`JOURNAL`是显式本地路径；
输出必须新建，工具不覆盖输入。

```powershell
python -B -X utf8 -m tools.rebuild_tagged_strings apply SOURCE `
  --source-sha256 9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7 `
  --plan locales/zh-Hans/ui-defaults-v40.json `
  --plan-sha256 132f65ca482479c33c61d242156f50145778b4fe6aa8ab7a0ea1b441ee601719 `
  --output OUTPUT --report JOURNAL
```

回滚用同一工具的`rollback`模式，输入输出包摘要、同一计划与journal实际摘要，
写入另一新文件；完成后必须恢复到上述输入SHA。可执行的本轮`ROLLBACK.sh`
及准确命令／输入／字面输出／退出状态保存在`build/phase-370-ui-defaults/VERIFICATION.txt`。

## 验证边界

- 旧包：31个英文默认值，目标检查退出1；新包：31个规范空默认，英文active默认为0，退出0。
- 独立副本回滚：整包恢复旧SHA及31个旧默认，旧目标检查恢复退出1；新包仍保持修改。
- 合成测试同时验证非空中文写入、嵌套父长度、数组拒绝、保留真实文本、源锁及回滚篡改拒绝。
- 主文本回归沿用源锁v39策略，不因处理UI占位修改原有排除判定。
- 游戏显示、首次打开瞬间、不同存档、动态切换仍由[测试清单](PHASE_370_TEST_CHECKLIST.md)实测。
  不把静态PASS扩展成全游戏任何语言残留为零。章节卡按用户决定不再排查。

## 实际交付回读

- 原`dist/MC2-display-repair-disc1/开始中文测试.cmd`已增量更新：2个candidate资源、
  3个入口元数据文件及测试清单；原文对照、配置、存档与运行记录保留。
- 同名`dist/MC2-CN-v1.0.exe`已替换为本轮构建，SHA256
  `24884164568a37d391d3b8f70dbc919ed4bddf764c97ae8c53d224ab56234186`，1,743,443,819 bytes。
- 实际EXE内756项payload、1044条资源记录、2个DLC、版本与最新说明均回读通过；
  bundle manifest为`35f4dd30635a9a65bd3e116b8ee66c4c6907c9c1ddf6ed39d3f00e00c064ab54`。
- 旧安装器相对新recipe有5个预期差异（两盘资源／TOC四条加说明）；新包为0。
  独立安装器副本回滚到旧SHA`8651b9a9becf519b72d1d56697168da125a5cc566a0e5adfb5bc1328228da733`，
  恢复同样5个差异；旧包自身verify-only仍通过，新包保持修改。
- 原始ISO、旧安装器、bundle、当前packet依赖及必要回滚证据保留。
  仅移除已hash核验的可再生打包副本与暂存文件，共15,738,240,371 bytes；未新建整盘副本。
