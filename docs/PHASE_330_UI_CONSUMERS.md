# 阶段330：任务底部提示与全技能数字消费者

## 本轮结果与证据等级

**Verified offline**：以阶段329/330已核对的 `MC2Game.xxx` 为底包，修改15个真实UI导出中的21个同长度标量字段。
修订计划为 `locales/zh-Hans/gameplay-ui-fields-v9.json`；通用补丁工具不包含中文或特定控件名称。
配套测量契约为 `locales/zh-Hans/gameplay-ui-spacing-v9.json`，通用审计工具按真实FontCharacter.USize、Coalesced字段和序列化控件位置测量。

用户第二次反馈要求数字缩小后，本项最终输入使用 `build/phase-330-gameplay-qa/numerals-reproducible/candidate` 的平衡数字包；不沿用已否决的大数字预览。
本项没有启动游戏、改ISO或部署测试副本；游戏内动画、排版重算和像素合成效果仍由本轮后续实机验收确认。

## 已验证根因：两种问题不是同一个数字字体问题

### 任务接受窗口

真实对象前缀：`UI_Core.Scenes.QuestInfoDecision.Base.Quest_Info_window`。
`Bt_Y`/`Bt_A`/`Bt_Deny`包含原有Y/A/B字形标记及 `MC2UI.Common.Image/QAccept/Deny` 绑定。
`GeneralFont`样式ID `9fe5e7d1-481e0c9d-c03b5f9f-40f3726d` 的六个状态引用 `Startup_int.Font.General_15`。
按钮图标在 `font_ui.MC2StyleFont_0` 的USize为27；当前汉字USize为27。
因此“Y查看图片”占135，“A接受”和“B拒绝”各81，而原槽只有98/63/76。

新位置全部保持相同y；正常footer与仅接受footer分别保留完整译文，不通过删字解决遮挡：

| 对象 | x 原→新 | 横向槽原→新 |
|---|---:|---:|
| Bt_Y | 409→307 | 98→141 |
| Bt_A | 517→460 | 63→90 |
| Bt_Deny | 576→562 | 76→90 |
| Bt_Y_OnlyYes | 465→409 | 98→141 |
| Bt_A_OnlyYes | 580→562 | 绝对右边956→相对宽90 |

`Bt_A_OnlyYes.Position.ScaleType[2]` 从 `EVALPOS_PixelViewport=1` 改为 `EVALPOS_None=0`，与其他槽采用相同的右面相对模式；不能把旧956直接当作宽956。
四个原本启用横向AutoSize的A/Y renderer，`AutoSizeParameters[0].bAutoSizeEnabled`改为0。
保留所有按钮字形、MarkupString、StringStyle、垂直坐标、隐藏状态、事件和原生绑定。
两个footer最右边界均保持652，文字/图标实际advance之间至少21，不再跨入下一按钮组。

### 动态技能名称与KAN数值

真实共享消费者是 `UI_Battle.Scenes.Scene_ButtonX.Bundle.Base.ButtonX_Bundle` 下的
`Selected`、`X_0`、`X_1`、`X_2`、`X_3`，不是教程中已经烘焙的四张示意图。

五个 `KanNum*` 标签的36px槽均在x205，原renderer横向对齐为2（右对齐）。
名字右端在普通状态202、Selected状态208。单数字使用原始美术字体 `font_ui.normalnumber`，
USize为12–15，导致普通状态单数字间距24–27px；其 `WhiteNumber` 样式ID为
`2901905f-47135361-dd09e5a1-e2f272ac`，六个状态均指向这个原始数字字体。
该路径不使用本轮平衡后的仿宋0–9字形。

五个数值renderer的 `TextStyleCustomization.TextAlignment[0]` 从2改为0（左对齐），
`Selected.Skill.Position.Value[0]` 从206改为200，统一五组名称右端202→数值左端205，即3px advance间距。
所有20个名字阴影的右端保持主文字±1px；两位数不会因“把名字整体向右挪”而撞字。
36px数值槽、名称、数值、字体、控件可见性和四方向选择逻辑保持。

## 全量测量分母

- `MC2Skill.int` 的12个角色风格分区及连携分区，共119个非说明名称。
- `Data_Skill.xxx` 全620个 `MC2Game.MC2SkillData` 导出，全部无显式archetype；显式 `NeededKan` 加真实CDO默认1，域为0–10。
- 三个10值资源包括 `Crocell.SkillData_519`、`DoubleAttack.SkillData_038`、`Rue.SkillData_416`；没有把全部技能误当单数字。
- 119个名字 × 11个实际数值 × 5个控件 = 6545组合，另外119 × 99边界 × 5 =595组合，总7140。
- 这里使用保守笛卡尔积覆盖所有可能名称/数值，不声称119个名称与620个战斗资源已经全部一一配对。
- 修改前7152项不满足契约（7140组合间距和12项footer问题）；修改后0。

## 可组合补丁与回归

`tools.patch_tagged_fields` 先验证输入SHA、UE3版本/字节序、唯一导出路径/类、完整所选payload SHA，
再解析带array_index的逐层tag路径，验证标量类型与原值，拒绝重叠、重复、no-op、未知状态及超界。
补丁只写浮点/字节/布尔/整数的原位置，不修改长度、符号、数组或字符串。
回读同时验证每个新payload SHA和反向逐字节恢复。

计划记录原始整包SHA `a87c10ef28441d6abf9529ca4464f750c73ce8a3a44ba6b71ce2e4af13abab11`，但组合守护以所选导出payload为准。
调用者必须提供**实际**输入SHA，因此可在本轮数字、纹理等不相交的导出更新之后应用，不用旧整包覆盖其他改动。

```powershell
$Source = 'build/phase-330-gameplay-qa/numerals-reproducible/candidate/MC2Game/CookedXenon/MC2Game.xxx'
$Plan = 'locales/zh-Hans/gameplay-ui-fields-v9.json'
python -B -X utf8 -m tools.patch_tagged_fields apply $Source `
  --source-sha256 (Get-FileHash -Algorithm SHA256 $Source).Hash.ToLower() `
  --profile $Plan --profile-sha256 (Get-FileHash -Algorithm SHA256 $Plan).Hash.ToLower() `
  --output build/phase-330-gameplay-qa/ui-consumers/NEW_CANDIDATE.xxx `
  --report build/phase-330-gameplay-qa/ui-consumers/NEW_DIFF.json
python -B -X utf8 -m unittest discover -s tests -p test_tagged_fields.py -v
```

使用 `audit_ui_spacing --package-override game <新包>` 可在既有候选资源根上测量单个新包，不复制完整游戏；
同时提供 `--package-override startup <平衡数字Startup_int.xxx>` 保持最终字体输入一致。
输出包含每个输入SHA、620个源资源身份、所有名称advance、五组槽位和两个footer。

11项通用回归验证精确修改/恢复、重复应用拒绝、异类/越界/错误字段拒绝、selected payload漂移、
其他导出变化的可组合性、缺字、Coalesced绑定唯一性、CLI路径/哈希及本locale全五组消费者覆盖。

## 本地四件证据（忽略目录）

根目录 `build/phase-330-gameplay-qa/ui-consumers`：

- `MODIFIED_FILE.xxx`：最终数字底包+本21字段；SHA `b185edff2e0ca548ec61e88f5b980025fac22f852ce308004dbb65910ac20bac`。
- `DIFF_FILE.json`：字段路径、偏移、原/新字节和正反向哈希。
- `VERIFICATION.txt`：BASELINE/MODIFIED/ROLLBACK确切命令、完整输出与退出码。
- `ROLLBACK.sh`：可执行、只写新的隔离 `ROLLBACK_COPY.xxx`；不覆盖源或候选。

最终数字原输入SHA为 `beb303e8eaa7b63997a218c1a7421302b8b0d7b9a0e1508737bd1fa56cb39676`；
回滚副本SHA精确相同。回滚后重新测量恢复7152项旧问题（退出1），字段baseline检查退出0；修改副本仍保留新状态。

## 其他真实消费者复核

- `MC2Game.xxx`、当前宽度修复的native image和原disc1-native image中，对 `QUEST:`/`QUEST :`/`Quest:`/`Quest :`
  的ASCII、UTF16LE、UTF16BE字节检索全部0命中。Quest相关类/函数符号保持；图9可见前缀由同轮文本子项处理Coalesced。
  这是有限三输入的literal排除证据，不是所有运行路径的零遗漏证明。机器报告 `quest-prefix-audit.json` 保留散列和命中列表。
- 商店四行纹理消费者补证：`KamondStore...Category_0..3.ImageComponentTemplate` 的UV高度31、宽79、V=0/32/64/96；
  `StoreMenuScene...Category_0..4` 也都是79×31。这支持同轮纹理子项按79px居中，避免把128px图集宽当真实消费者宽。
- 邮件 `Mail_Body` renderer为 `CLIP_Wrap=3`、无显式AutoSize，所用General字体glyph VSize25；
  native正文分页/滚动尚未证明，不把304px viewport或假设32行高自动等同于邮件全文上限。

本报告的已验证范围是序列化消费者、输入身份、字宽契约与可逆资源修改；实际运行布局不由静态绿灯替代。
