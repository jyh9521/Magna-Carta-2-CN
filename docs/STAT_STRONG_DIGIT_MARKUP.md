# 数值参数的逐字数字标签链（阶段283）

## 本轮新增而非重复核对的证据

阶段282的8条StatStrong模板已确定前缀、数值字符串、后缀、LF、附加说明的排列。本轮追到数值字符串的来源，发现它不是直接插入十进制数字：

1. 原生辅助0x82356fa8通过全局FName 0x83265dac查找函数，并以整数参数块和字符串返回槽做虚调用。冷初始化器0x82e33620窗口把UTF16BE名称`GetStringFromNumber`（0x820e8650）的构造结果两字存入该全局。对应名称、整数输入/字符串输出与包内`MC2HUDUI.GetStringFromNumber`一致。原生调用的活动receiver类尚未执行观察，因此实际对象归属保留为高置信关联，不冒充游戏内调用跟踪。
2. MC2Game.xxx对象12425为151字节脚本；读取7项类型/引用绑定，并完整匹配有限字节码形状：输入整数经PrimitiveCast:0x53赋给numStr，取长度，索引从0开始，在索引小于长度时取单个字符，拼出`<Strings:MC2UI.Number.Num_字符>`，拼到结果并递增，最后返回结果。
3. 不是凭native编号猜功能：Core.xxx的5个实际声明分别绑定112 Concat_StrStr、125 Len、127 Mid、150 Less_IntInt、165 AddAdd_Int，逐一检查参数/返回类型。分支目标41和138（十进制）、回边41均由完整脚本匹配验证。PrimCast:0x53的原始类型转换操作保留；没有编写或执行游戏VM。
4. Coalesced原始Number分区正好包含Num_0–Num_9，值分别为ASCII 0–9。第二盘从原ISO重新校验目录条目及两指定包哈希，只提取MC2Game.xxx/Core.xxx两个文件，独立运行探针；两盘报告字节一致。原盘未改，没有整盘/整游戏复制。
5. 原生格式化链进一步定位为0x82324c50→0x8238dfc8→0x82870b78→0x82870a48→0x82872f18；检查到变参寄存器保存和宽字符缓冲处理。完整CRT格式化语义及Strings标签展开仍未证明，不能把以上静态链声称为画面验收。

## 80个离线中文组合情景

对HP/攻击/防御/精神/抗性/速度/耐力/耐力恢复，分别用0、1、9、10、20、100、140、999、1000、2147483647共10个输入建模。每个数字先生成逐字标签，再通过源Num_0–9值展开，验证数字序列、百分号及唯一LF不变。

候选组合采用“角色的属性提高 ”作为前缀；HP的PercentUP候选为`%  `，普通normalUP候选为单空格。即将韩文后缀中的增加动词原子地迁到8个中文前缀，以适应中文语序，而保留前缀末空格、百分号及两/一空格。示例展开为“角色的HP提高 20%  ”或“角色的攻击力提高 140 ”，再接模板自己的LF和附加说明。80例仅是明确正整数域的离线模型，不是运行输出。

**本轮未把这10个候选写进翻译计划**。共享后缀的采用必须与8个前缀成套，下一步清点其他消费者并处理原值保留记录的显式迁移；不可单独把normalUP改成空格，也不可删除模板中的数字标签。负数/符号不属于本轮模型验证域，不据此断言游戏支持或不支持负数显示。

## 两个异常格式与两个未定术语

- 两条Zephi文本在INT/JPN中的单独反斜杠和未完句一致，仍要追踪转义/字幕展开，不把未完句补成完整承诺。
- 本轮新增读取CSMB12_131完整双语场景及information/lastrada全组。JPN的王の霊廟与UI键lastrada_sch、四证通路及ラ・ストラダ中心同指；INT的同UI键为라 스트라다 최심부（拉·斯特拉达最深处），剧情也称中心。这里有实际命名差异，不是简单韩日同词。
- CSMB12_131的韩日键相差1：INT07的通往中心对应JPN08，INT08已有证明对应JPN09。该关联为未知왕의 영병提供目的地候选证据，但仍不证明韩文这个拼写本义就是灵庙。下一步查具体目的地对象/地图关联，避免再凭同键直接替换。
- 성쇄仍只在主源章节句中命中；没有把相似字성쇠或日文隆盛当已证原文修正。本轮不重复术语原封轮询，而把新目的地范围存入后续研究检查点。

## 复现

```powershell
python tools/inspect_digit_tag_formatter.py build/poc-game/disc1/MC2Game/CookedXenon/MC2Game.xxx --sha256 13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641 --core build/poc-game/disc1/MC2Game/CookedXenon/Core.xxx --core-sha256 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815 --plan references/probes/stat-strong-digit-formatter.json --plan-sha256 6ae0c85f893417e2a4ec60494a5692169ab300a321e0b9ce61de4f40adb76611 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-digit-formatter.json
```

标准输出：`PASS digit-tag script shape;7 typed bindings;5 Core declarations;executed=false`，exit0。输入hash在解压/解释前检查，输出必须全新且与输入不同，来源/输出均复读。工具locale-neutral；只有计划中的对象名、角色绑定及标签前缀属于本作。报告不包含完整包或脚本。

9项自制/公共身份测试新增，基线/隔离旧源1779、修改/干净源1788测试各1跳过。源hash、双盘27/29回填/重放、14082旧译/4094原值/315字幕、独立研究记录/旧源/注册表回滚及11954旧依赖按收尾流程检查。命令与实际输出见build/phase-283-verification/VERIFICATION.txt。资源未变，复用276测试目录，不刷字库/TOC，不启动游戏；游戏验收由用户负责。
