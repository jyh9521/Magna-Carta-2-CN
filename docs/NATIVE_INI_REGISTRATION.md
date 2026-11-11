# 原生 INI 节／键准入验证

阶段368，2026-11-11。接续阶段367的三个混合编码待核项。

## 结论与逐项处置

**Verified（静态代码＋有界原生指令重放）：**当前 Coalesced 中
`..\MC2Game\Localization\INT\MC2Game.int` 的整个195个 UTF-16 code unit
经过原生行扫描后，没有一个节名通过准入，当前节指针始终为零。
所有六行均走 `0x824783f8 → 0x82478730` 的无节跳过分支，最后到
`0x82478738`；最终光标为196（含终止NUL之后），不是只检查前几行。

| 物理提取键 | 原生行 | 当前Coalesced行起始偏移 | 结果 |
|---|---:|---:|---|
| ItemName | 2 | 783805 | 无当前节，跳过；保留原字节 |
| Accept | 4 | 783911 | 无当前节，跳过；保留原字节 |
| Cancel | 5 | 783981 | 无当前节，跳过；保留原字节 |

这三个条目是通用工具的**物理行提取结果**，不是三个已注册的原生INI键。
据此从 `pending-malformed-source` 转为“已验证未注册的损坏源文档／保留”。
该结论绑定文档、原生代码和入口；不是“任意韩文都是测试数据”，也不是靠
`UITest` 名称或全包未命中推断不可达。修复图2的正常碑文字段不受此结论影响。

源身份：

- 当前Coalesced SHA256：`8671b08e5bd4732aad15729d44d8832778a06684980efd8b5776dd071b8fa79a`。
- 文档length-word偏移783739，值 `-196`；载荷偏移783743。
- 不含NUL的UTF16LE载荷390字节，SHA256：
  `e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7`。
- 原盘INT／JPN以及当前INT／JPN的该文档载荷相同（阶段367逐份哈希证据）。
- 物理值SHA分别为 ItemName
  `0207167a7cb295f04902173e6e8d1b460d741121f10dd1611c9de14121234c44`、Accept
  `333e7d4da2405c0e83a2990e7b89c1fb7719546ebc94aced44ebba082a68df4a`、Cancel
  `03b3e654c6f617dd251cf72ccdc71a6c74cce38bfd3a7c24c8df6a8cd6208ead`。

## 真实入口与分支

原生映像基址 `0x82000000`，SHA256：
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`。
`references/ini-registration-profile.json` 保留完整映像哈希、七个原生窗口的
地址／长度／SHA、重放断点以及常量身份，不包含完整函数或原游戏文档。

| 路径 | 地址／调用证据 |
|---|---|
| Coalesced loader | `0x82479468..0x82479860`；`%sLocalization%sCoalesced.%s` 位于 `0x8217aa34` |
| FString数组反序列化 | loader在 `0x824796b0` 调用 `0x822de1a8` |
| 单个FString | 数组在 `0x822de27c`／`0x822de2c4` 调用 `0x8238e0e8` |
| 负length的宽字符串 | `0x8238e21c` 读取 `count*2`；`0x8238e23c..0x8238e280` 逐16位交换字节 |
| path/content配对 | loader按24字节（两个FString）前进，`0x82479820` 调用 `0x82478278` |
| 宏处理 | parser在 `0x824782a0` 调用 `0x8238d958`，宏常量 `%GAME%` 在 `0x8217a9ec` |
| 当前节初始化 | `0x824782c0..0x824782cc` 将r28／r27／r19置零 |
| 行分隔 | `0x824782e0..0x82478340` 只按U+000D／U+000A／U+0000分行 |
| 节准入 | 首字符必须 `[`；`0x8286e0e0` 求长度；`0x82478360..68` 要求末字符 `]` |
| 无节跳过 | `0x824783f4` 比较r27；零时 `0x824783f8 → 0x82478730` |
| 键准入 | 有节／非空后，`0x8286e920` 找 `=`；`0x8247841c` 才开始分离键值 |
| 写入调用 | 后续 `0x824786f4`／`0x8247872c` 调用 `0x82397260`；此文档均未到达 |

两条以 `[` 开头的原生行分别长30／59 code units，末字符为U+0D00／U+20B7，
均不是 `]`。中间看起来像 `[Quest]` 的字节没有形成合格的原生行开头。
**U+0A0D不等于U+000A**，不能用字节级CRLF或Python `splitlines()` 代替原生分行。
载荷本身仍可严格解码为UTF16LE；这里验证的是损坏后的INI语义，不是Unicode解码报错。

当前执行文件也重新核验：`build/phase-368-pending-closure/current-executable-proof.json`
记录当前recipe下的XEX重新解码及七窗口一致性。该本地证据应与发布recipe一起核对，
不能只因原盘代码符合就假定将来的字体补丁或其他XEX版本仍相同。

## 可复用验证工具与边界

`tools/replay_ini_registration.py` 使用 `tools/ppc_fragment.py` 执行真实指令窗口：

1. 验证完整映像、全部窗口、常量及源Coalesced／嵌入载荷的SHA。
2. 重放原生UTF16字节交换，核对实际码元。
3. 从原生当前节初始化开始，遍历全部行；需要长度时重放实际 `wcslen`。
4. 每段最多256条指令，总数有硬上限；只在下段会重新设置条件位的边界切片。
5. 原件完成4421条指令、995片段，最终无节／无键准入，**没有任何注入的map假设**。
6. 输出JSON重新打开比对，并验证只读输入未改变。

这是离线指令重放，不是启动游戏，不执行allocator、TMap插入、UI或整套FString API。
原件无 `%GAME%`；静态宏路径确认无命中时复制源文本。工具对含宏输入明确失败，
不会用自写replace冒充原生宏执行。正向合成输入默认停在节准入；仅带有显式
`assume_section_map_success` 的合成对照注入非零节指针，再执行原生找等号／键准入。
其报告保存每个注入及跳过写入的边界，永远不声称完成了map注册。

```powershell
python tools/replay_ini_registration.py `
  --image build/phase-368-pending-closure/current-native.bin `
  --profile references/ini-registration-profile.json `
  --coalesced build/phase-367-residual-repairs/MODIFIED_FILE.int `
  --coalesced-sha256 8671b08e5bd4732aad15729d44d8832778a06684980efd8b5776dd071b8fa79a `
  --embedded-path '..\MC2Game\Localization\INT\MC2Game.int' `
  --embedded-sha256 e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7 `
  --output build/phase-368-pending-closure/mixed/native-replay.json `
  --controls --expect-inactive
```

字面输出，退出0：

```text
source_gate: terminal=true section_admissions=0 key_admissions=0 lines=6
native_exit: 0x82478738 cursor=196 code_units=195 assumptions=0
controls: PASS 9
inputs: unchanged; report: reopened
```

九个对照覆盖无节、坏尾部、有效节停点、有效键准入、后段才出现有效节、CRLF／空行、
有节但无等号、空输入及宏拒绝。`tests/test_replay_ini_registration.py` 用自写小型PPC
程序检验编排器，不依赖游戏资产；真正游戏指令的正负对照另存在上述本地JSON。
新增LHZ／LHZU／STH／LHZX／SUBF／SRAWI均有独立指令测试，原有语义测试继续通过。

## 源数据上的反例与回滚

`build/phase-368-pending-closure/mixed/red_green_replay.py` 只改研究副本的两字节：
偏移783771的 `0d0a` → `0a00`，即将首个U+0A0D换成真正的U+000A。
这就让首行成为完整 `[AnswerChoice]`，在实际原生代码里触发节准入。
因此“把损坏文本修得可读”不是无副作用的汉化修补，而是激活原来不注册的文档。

- BASELINE：原件 `--expect-inactive` 退出0。
- MODIFIED：两字节反例到 `0x8247836c`，section_admissions=1，退出1，正确拒绝“无注册”断言。
- ROLLBACK：在另一副本执行 `ROLLBACK.sh`，原SHA恢复，退出0。
- ROLLBACK_BEHAVIOR：重新扫描到 `0x82478738`，零节／零键，退出0。

`mixed/VERIFICATION.txt` 保存完整命令／输入／字面输出／退出码和四个绝对路径。
`mixed/MODIFIED_FILE.int` 刻意留下激活反例，并非可安装补丁；`DIFF_FILE.json` 明示
`synthetic-header-activation-control-do-not-deploy`。原始／当前游戏源始终未改变。

## 仍应保留的不确定性

- 历史损坏过程不是实测；“对UTF16做了字节级CR插入”仍是高置信推断。
- 删除11个CR再补零的可读诊断不是源历史证明，不用于生产恢复。
- 不推断激活后的测试字段会在何种游戏流程出现；恰因会改变注册状态，本轮保留它们。
- 若文档SHA、代码profile、loader路径或当前recipe改变，必须重开这三项验证。
- 完整原生TMap插入和游戏呈现未执行；本轮闭合的是这些确切源字节在此入口的零注册路径。
