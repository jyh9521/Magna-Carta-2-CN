# StatStrong：原生本地化拼接模板（阶段282）

## 已验证：新的静态调用证据

此前仅看到10条韩文前/后缀，因缺少调用证据保留原值。本轮直接在原生虚拟映像找到8条宽字符串模板，并逐条验证16字节PPC参数地址装载及相对带链接分支：

`<Strings:MC2Skill.StatStrong.属性键>%s<Strings:MC2Skill.StatStrong.后缀键>`，随后是实际LF字符和第二个`%s`。

| 属性键 | 后缀键 | 模板虚拟地址 | lis/addi/call窗口起点 |
| --- | --- | --- | --- |
| HP | PercentUP | 0x8212f890 | 0x82d39084 |
| STR | normalUP | 0x8212f930 | 0x82d390ec |
| DEF | normalUP | 0x8212f9d0 | 0x82d39154 |
| ESP | normalUP | 0x8212fa70 | 0x82d391bc |
| ESR | normalUP | 0x8212fb10 | 0x82d39224 |
| DEX | normalUP | 0x8212fbb0 | 0x82d3928c |
| STA | normalUP | 0x8212fc50 | 0x82d392f4 |
| SRV | normalUP | 0x8212fcf0 | 0x82d3935c |

全部装载目标为r4，结果对象地址装入r3，分支目标共同为0x82324c50。每个窗口与整个映像均锁定SHA256；两盘各自派生的映像分别检查并得到字节相同报告。整映像中的16处StatStrong宽字符命中均落在这8条模板的两处lookup中。该计数不排除动态构造键的其他消费者。

**已验证**：这8条模板的字符顺序是属性前缀→第一字符串参数→后缀→LF→第二字符串参数，HP用百分比后缀、其余7项用普通后缀。LF来自模板，不应补进任意一个本地化片段。原10条片段的首尾空格、PercentUP的百分号/双空格仍保持。

**高置信推断**：前一参数是属性增长值，后一参数是附加说明；周边代码读取数据成员并调用0x82356fa8生成参数。该辅助函数和0x82324c50的完整实现尚未命名/证明，不把寄存器调用等同于已执行或真实画面。

**尚未验证**：格式化函数及Strings标签展开实现、所有动态消费者、实际运行调用和中文显示。本轮解决的是静态拼接顺序，不把10条词片标为已翻译，不把未知机制全部交给玩家。

## 可复现命令

```powershell
python tools/inspect_localized_templates.py build/xex-native-verification/final/disc1-pycryptodome.bin --sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9 --plan references/probes/stat-strong-localized-templates.json --plan-sha256 3eb094a694f920c60b0b3d42e815d7f07e35c4fb2c1d2a70497b9c98d2063b48 --output build/NEW-disc1-native-templates.json
```

用disc2-pycryptodome.bin与全新输出路径独立复核。输出必须不存在且与两输入不同，输入哈希在解释前检查；不装载/执行映像。脚本仅标准库，不依赖反汇编器。9项新增测试包含8项自制二进制/模板回归及1项公开计划身份验证；覆盖模板、指令地址、调用目标、参数寄存器、重复记录、原文件身份及覆盖写入防护。

REA对该PowerPCBE PE返回unsupported PE architecture，本轮未改注册/安装环境，改用仓库既有VirtualImage只读字节读取和显式PPC字解码。该诊断与Capstone探索输出保存在忽略目录，不伪称REA成功反编译。第一次实验错误预期CRLF，被原始UTF16BE字符证明应为LF；探针已修正，负例保留在研究记录。

## 其他未定项的实查与接续

- 两条Zephi异常文本已核对INT/JPN：两语种相同ID语境均保留单独反斜杠和未完句。日文没有“完整正确版”可直接替换；下一步追踪实际转义/字幕展开代码，不把两处当同一类占位。
- 성쇄与왕의 영병相关章节的INT/JPN已再按相邻句对照；此前已证明的语言版本差异仍存在。精确网络检索未取得能直接锁定这两个韩文词的原厂证据；不凭英文攻略或日文词猜改。下一步检查包内地图/对象名与其他原版区域文本，区分源文字误写和专名。
- 下一轮先检查0x82324c50及0x82356fa8的静态范围/调用关系，再做10片段中文组合情景与全消费者清点，最后决定是否进入新翻译批次。不要退回只查HEAD/runs或等待用户给未知拼接答案。

基线/隔离旧源码1770测试、修改/干净源码1779测试（各1跳过），源身份、双盘27/29重放、旧译/保留原值、字幕及独立回滚按既有流程验证，命令/结果见build/phase-282-verification/VERIFICATION.txt。没有改译文、字库、TOC或测试资源；复用276包。游戏验收由用户负责，研究继续离线执行。
