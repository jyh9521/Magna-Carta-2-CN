# 阶段368：12项待核字段逐项闭合

2026-11-11，接续用户指定的3个混合编码字段和9个旧测试数据字段。
**9项已翻译；3项经完整原生解析路径验证未注册，保留原始字节。**
这12个身份没有继续pending，不表示全游戏／所有视觉资源已经清零。

## 逐项结果

| 对象／嵌入文档 | 字段 | 处理 |
|---|---|---|
| MC2Game.int（损坏文档） | Accept | 原生第4行无当前节，跳过；原字节保留 |
| 同上 | Cancel | 原生第5行无当前节，跳过；原字节保留 |
| 同上 | ItemName | 原生第2行无当前节，跳过；原字节保留 |
| data_item.etc.CureSeed | ItemName | 疗愈种子 |
| 同上 | Description | 单体恢复30% |
| data_item.etc.HealLeaf | ItemName | 治愈叶 |
| 同上 | Description | 全体恢复30% |
| data_item.Test.Ice_Hat | Description | 炎热概率降低10% |
| data_item.Test.throw_stone | Description | 投掷后造成伤害 |
| data_quest.Test.testquest | Subject | 测试任务 |
| 同上 | Description | 来测试吧 |
| 同上 | SpecialReward | 无 |

结构化源为 `locales/zh-Hans/legacy-display-fixes-v38.json`；完整94身份台账为
`omission-resolutions-v38.json`：**61 localized、27当前模板不消耗的参数、3身份字段、
3已验证未注册的损坏文档字段**。除上述12项外，82项处置逐字保持v37；旧文件保留历史。
旧物品的单体／全体30%不替换成正式物品的200HP；10%、任务Id、KeyNumber、对象路径、
Type、数量、价格、Stats及Comment全部保持。独立非剧情短文本无内部标点，不补句末句号。

## 3项：不是猜测“测试内容”，而是原生零注册证明

[完整原生INI证据](NATIVE_INI_REGISTRATION.md)记录loader→宽FString字节交换→INI解析器链。
当前两盘XEX重新解码的映像相同，七个相关窗口与源profile一致；当前已启用图形补丁
不覆盖这些窗口。文档390字节／195个码元完整重放到 `0x82478738`，六行、零节、零键，
没有注入TMap成功假设。Accept／Cancel／ItemName分别经过 `r27=0` 的跳过分支。

源文档SHA `e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7`。
当前整个Coalesced保持
`8671b08e5bd4732aad15729d44d8832778a06684980efd8b5776dd071b8fa79a`，
包含阶段367已经修好的图2碑文。研究副本只把一个U+0A0D改为U+000A就激活首节，
正向反例说明“修乱码”会改变注册状态；该反例不进入生产资源。

**Verified**是当前字节在指定入口的有界指令执行结论；历史损坏方式仍属推断，
完整TMap、UI及游戏运行未执行。文档、代码profile或实际入口改变时必须重开这3项。

## 9项：区分显示字段和身份，变长回填

[消费者核查](LEGACY_DISPLAY_CONSUMERS.md)保存25个完整脚本、物品事件比较、加载／库存／
选择缓存与任务UI链。更正阶段367的过度保守表述：**Subject不是任务检索键，QuestID才是**。
ItemName事件比较来自两个对象的属性，精确旧名命中18项中只有2项是ItemName，
其余16项是Comment；库存按KeyNumber、加载按资源路径。两旧物品Type3不进入Type5选择缓存。
物品说明的原生UI读取链字节已验证；`+0x1c8` 对应Description的布局归属标为高置信推断。
不依赖“Test路径所以不可达”的排除，也不宣称完整动态图或现存存档缓存已遍历。

通用工具 `tools/rebuild_tagged_strings.py` 使用独立locale计划，
profile为 `ue3-relocated-wide-tagged-strings-v1`：

- 源包SHA／大小、唯一对象路径／类、完整tagged stream、旧新payload SHA全部锁定。
- FString仍为负大端长度＋UTF16LE载荷；重算property size、export size和offset。
- 五对象整段4字节对齐追加；全包32768字节对齐。原始前缀仅改五个export各8字节。
- 原header／name／import／dependency表、其余export及全部原payload不动。
- 拒绝数组、未知native tail、未知native struct、stack／CDO及选中导出的重叠别名。
- 三处数值百分比显式声明为literal；真实占位符仍检查，不把30%误当printf片段。
- Journal记录40字节元数据差异与追加段；回滚恢复元数据并截断，再正向重放比对整个候选。

旧韩文payload保留在**非活动导出范围**，不能凭全文件grep再计作九条活动漏译。
必须依当前export的offset／size回读，且先验证旧范围没有被其他导出同时拥有。
现用七Font覆盖所有新字，不改字体；静态覆盖不等于游戏内排版验收。

## 可复现源锁回填

先依阶段367构建得到该检查点的Startup，再执行（`$P`为计划文件）：

```powershell
$P = 'locales/zh-Hans/legacy-display-fixes-v38.json'
python -B -X utf8 -m tools.rebuild_tagged_strings apply `
  build/phase-367-residual-repairs/packet/candidate/MC2Game/CookedXenon/Startup_int.xxx `
  --source-sha256 089868b8120f382c22e71329530824e97f03d6c8fb37681a39224dd4fc89c91e `
  --plan $P --plan-sha256 76632f4526f0eea2631a55c137711a18d205dc4c95acb5f138bbda6d84235638 `
  --output build/phase-368-reproduction/Startup_int.xxx `
  --report build/phase-368-reproduction/journal.json
```

输出28,475,392字节，SHA
`27f179a768b8c18dc884e2d9f6499d0fc1b5b07b41c1b7e181e0398facb39228`。
旧件28,442,624字节，SHA
`089868b8120f382c22e71329530824e97f03d6c8fb37681a39224dd4fc89c91e`。
新候选通过raw runtime envelope检查。

通过现有 `compose_incremental_comparison` 和 `prepare_installer_sources` 增量合成：
只有Startup与TOC各两盘成员改变，共4记录；双盘471／573资源及2DLC数量不变。
当前recipe SHA为 `7fc7aca33b52a1f2cbf0c9d70e90181de26aafecd4b2362a49f52f8a9224a0fc`。
双盘原始Startup身份相同，当前输出也是同一SHA，不合并盘结构。

## 三态与严格审计

工作目录 `build/phase-368-pending-closure`：

| 阶段 | 实际命令 | 字面输出 | exit |
|---|---|---|---:|
| BASELINE | `python -B -X utf8 verify_legacy.py BASELINE` | `LEGACY_FIELDS=9 NOT_LOCALIZED=9 ACTIVE_HANGUL_FIELDS=9 RESULT=FAIL` | 1（预期） |
| MODIFIED | `python -B -X utf8 verify_legacy.py MODIFIED` | `LEGACY_FIELDS=9 NOT_LOCALIZED=0 ACTIVE_HANGUL_FIELDS=0 RESULT=PASS` | 0 |
| ROLLBACK_APPLY | `"C:/Program Files/Git/bin/bash.exe" ROLLBACK.sh` | `RESTORED_RESOURCE=YES BYTE_IDENTICAL=YES MODIFIED_KEPT=YES RESULT=PASS` | 0 |
| ROLLBACK | `python -B -X utf8 verify_legacy.py ROLLBACK` | `LEGACY_FIELDS=9 NOT_LOCALIZED=9 ACTIVE_HANGUL_FIELDS=9 RESULT=FAIL` | 1（预期） |

输入依次为 `original/MC2Game/CookedXenon/Startup_int.xxx`、`MODIFIED_FILE.xxx`、
独立 `ROLLBACK_CHECK.xxx`；回滚恢复完整原SHA和原字段，修改件仍保持新SHA。
`final-commands.json`／`VERIFICATION.txt`保存完整绝对路径和命令。
四个交付证据为 `MODIFIED_FILE.xxx`、`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行`ROLLBACK.sh`。

v38文本筛查仍遍历18176主字段和315字幕cue；25韩文字段已分类、26排除，
pending／unresolved均0，但**1个opaque主文档仍令 `--require-resolved` 返回1**。
只关闭有证据的3项，不削弱通用门禁。既有VM／未解码视觉候选、独立大章节卡调查仍单列，
本轮没有观察游戏画面、旧存档文本刷新或完整安装后的实机表现。

## 现有入口与实际安装器

`dist/MC2-display-repair-disc1`已增量刷新5文件：Startup、TOC、两条启动命令和PREPARED。
没有新增资源登记，没有新ISO或完整游戏副本；134个原盘／配置／存档／运行记录受保护文件
重新计算散列后保持不变。回滚备份保留在本轮build目录，不回滚当前已修复入口。

同名 `dist/MC2-CN-v1.0.exe` 已实际更新，文件／产品显示版本仍为v1.0：

- 大小：1,743,441,107字节。
- SHA256：`ee03ed8bdb6802ca0ab21d5365a02c24bb6e1651406f96438415c92f3f057b42`。
- 内置manifest：`49bca88fb382adbd15e58eafc07b1af8adc52658f1d56625f6b3676c486afd2f`。
- 756个内置文件、双盘1044资源、2DLC审计通过；只有4条Startup／TOC记录改变。
- 实际EXE `--verify-only`通过且临时展开目录清理完毕。
- 另一EXE副本回滚到旧件SHA `f32ffaeeaae8e9c303f42c153eedbe2d21a68bbab556618abdbae39a094b330c`，
  自检仍通过，按新recipe审计恢复4项旧资源差异，预期退出1。

本地未启动游戏，也没有重写用户现有安装输出、ZAR、存档或配置。
原测试入口已刷新；其他既有安装输出需使用新安装器重新生成，不会因EXE同名自动更新。

## 工程检查与证据保留

本地统一验证8项全部通过，普通路径与路径别名各执行3215项测试，零failure／error，
各有3项既有平台／可选原生适配器skip。新增工具和数据测试不依赖完整游戏资产。
原生profile及locale计划均按Git LF字节锁定；换行归一化后重新执行真实源文档重放。
安装器自检临时展开目录已验证清理；原件、旧安装器、活动packet依赖、必要的逆向／回滚证据保留。
完整本地命令与随后同提交远端／四组Actions结果见 `build/phase-368-pending-closure/VERIFICATION.txt`。
