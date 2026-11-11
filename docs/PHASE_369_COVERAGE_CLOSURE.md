# 阶段369：剩余文本、脚本和图片的结构化复核

## 本轮决定与结果

接续阶段368的实际 recipe（SHA-256
`7fc7aca33b52a1f2cbf0c9d70e90181de26aafecd4b2362a49f52f8a9224a0fc`），
重新读取当前资源，不把阶段364/366的旧偏移当作当前证据。
本轮没有新增确认的玩家韩语漏译，因此不制造游戏资源改动；
此前图2碑文及后续61处显示字段修复继续包含在现行双盘资源中。

| 已核查集合 | 结果与处理 |
| --- | --- |
| 1个 opaque Core.int 文档 | 原生指令回放确认窄字节逐个零扩展，新增105个实际字段进入严格文本筛查；不修改文档字节 |
| 198个VM候选（193个物理位置） | 54个元数据匹配、144个操作数匹配；5处有两种端序猜测记录，保留每行、不重复宣称物理位置 |
| 15个函数元数据缺口 | 全部按原生存储结构解析；96个关联函数完整消费39,668字节、9,776 token；182条真实窄字符串均ASCII |
| 443个普通包＋2个DLC非类型化候选 | 全部逐ID归入纹理bulk、数值数组或旧重定位区域；不是可翻译FString |
| 39个native正文缺口 | 38个StaticMesh完整类型profile；1个ShaderCache核验95个编译GPU容器及字节边界，参数尾部语义仍单列研究；MaterialShaderMap数量为0，无该分支FriendlyName槽 |
| 13个驻留＋10个历史未解码图片 | 23对象、双盘46导出、72 mip全部实际解码和人工审看；韩语0项 |
| 31个英文UI默认字段 | 按完整owner和嵌套MarkupString重新绑定，全部ASCII；50个关联函数完整解析。不是韩语漏译；原生运行时是否总覆盖仍不作保证 |

版本化逐项清单：`locales/zh-Hans/coverage-closure-v39.json`。
旧v38结案表和v38筛查策略保留，新策略仅添加一个源锁定的Core读取视图，
没有把旧pending改成excluded以制造绿灯。

独立“大章节名称”仍没有匹配到具体资源。2026-11-11用户明确表示
“这块没有就没有吧，别的不残留就行”，因此撤销本轮继续追查，
保留历史负证据，不登记为“已翻译”或“已修复”。

## Core.int

嵌入路径为 `..\Engine\Localization\INT\Core.int`，负载6559字节，SHA-256
`a2c02ace02b6e5e3ed1d84ea76b541b194033b52e025d4691d76612f1c0bec02`。
唯一非ASCII字节在偏移5872，为版权行中的`A9`。

**Verified：** 两盘XEX解码得到相同native image，FString函数窗口摘要一致，
启用的运行时补丁不覆盖该窗口。正长度读取后的真实循环从`0x8238e1dc`开始，
在`0x8238e1f0`执行LBZX、`0x8238e1fc`执行STHX，直到`0x8238e210`。
源锁回放执行6560次写入（包括NUL），`A9`成为`U+00A9`，不是猜测CP949或UTF-8。

通用工具：`tools/replay_narrow_fstring.py`；独立数据：
`references/narrow-fstring-profile.json`。
回放仅覆盖已完成archive读取后的逐字节变宽循环，不声称执行了allocator、
archive、完整INI注册器或游戏UI。PPC指令语义参考
[IBM LBZX](https://www.ibm.com/docs/en/aix/7.3.0?topic=set-lbzx-load-byte-zero-indexed-instruction)
及[IBM STHX](https://www.ibm.com/docs/ssw_aix_71/assembler/idalangref_sthx_instrs.html)。

`audit_text_residuals`的可选`document_decoders`需精确绑定resource、embedded_path、
双盘membership和完整原始／当前payload摘要。仅在提取视图逐字节变宽，
Coalesced默认解析、重建字节和其他opaque文档的失败状态都不变。
漂移、缺失、半数盘、重复规则、未知decoder都被测试为拒绝。

严格文本门禁：

- BASELINE：18,176字段、315字幕cue、1个opaque文档，退出1。
- MODIFIED：18,281字段、315字幕cue、0 unresolved、0 opaque，退出0。
- 旧策略的独立回滚仍得到18,176字段和1个opaque文档，退出1。

这只代表选择的主文本视图完成筛查，不是“全游戏所有画面无残留”的证明。
原有25个韩文命中和26个排除项仍逐字段保留其非显示数据／消费者证据。

## 字节候选与图片

VM存储、边界、声明类守卫、5处双端序猜测以及逐函数重建说明见
[VM_STRING_BOUNDARIES](VM_STRING_BOUNDARIES.md)。
新读取器是独立opt-in，不放宽既有严格UI执行器，也不执行游戏脚本。

445个非类型化候选的分组：168个纹理bulk（含DLC2）、76个几何／地形数值数组、
14个地形权重字节数组、94个保留但已脱离活动export表的旧对象、
91个旧重定位纹理的SourceFilePath标签、2个旧纹理bulk。
每行保留当前包、原始候选、owner、偏移和证据摘要；不是仅按文件名猜测。

39个native正文不是只读到UObject的None标签就排除：38个StaticMesh的
KDOP、section、vertex/UV、index、edge、face及尾部均读到完整export末尾；
ShaderCache完整86,903字节包含198个shader CRC、20个vertex-factory CRC、
95个编译代码容器及95个GUID/FName全局引用。容器长度、元素数和引用互相核对；
MaterialShaderMap=0，所以该分支的FriendlyName字符串槽不存在。
**High-confidence deduction，而非Verified语义：** Shader子类参数尾部呈4字节HH布局，
但尚无本版本native serializer证明各数值的具体用途。它们保持明确有界的opaque参数区，
不把“读到整个export结尾”升级成“所有native字段语义已解码”。84个非空参数尾部共1792字节，11个尾部为空；当前同SHA包的266条原census候选与这些区间相交为0。445个候选的独立槽位证明不受影响。
复现与源锁见[NATIVE_PAYLOAD_COVERAGE](NATIVE_PAYLOAD_COVERAGE.md)。

图片的实际源锁、外置mip回溯和历史111纹理／121mip交叉重放见
[原生图片复核](PHASE_369_VISUAL_NATIVE_CLOSURE.md)。
保留B按钮1项、光效6项、品牌Logo1项、透明／色块／渐变15项。
只读解码器不扩大生产纹理写入器的支持范围。

## 31个英文默认值

| 默认值 | 数量 | owning UI |
| --- | ---: | --- |
| initial text | 5 | ButtonB技能名及4个影子标签 |
| Item Name | 6 | QuickMenu物品列表 |
| Quest Title | 9 | QuestJournal列表 |
| NO DATA | 9 | RemindTutorial列表 |
| Level UP / Level Up | 2 | LevelUp Point_Text_0/1 |

这31项均是实际序列化UI文本字段，不是未解码字节；它们不是韩语。
`FindWidgets`的Name/FName及循环查找、对应声明和50个相关函数已完整解析。
例如`SetInherentSkillName`和`SetTutorialList`是原生声明的空脚本存根，
不能把“存根无文本”写成“运行时绝不显示默认值”。本轮保留英文默认值，
不以猜测隐藏／覆盖关系删除文本；英文回退显示仍可作为普通UI验收项目。

## 测试入口、安装器与回滚

复用 `dist/MC2-display-repair-disc1`，保留candidate/raw-controls、配置、存档和runs。
重新核验并刷新入口元数据、补充当前测试清单，不生成新ISO或完整游戏目录。
游戏累计471／573资源和2个DLC的字节保持阶段368身份。

同名 `dist/MC2-CN-v1.0.exe`重打后携带本轮使用／验收说明。
新增安装器审计校验“嵌入说明等于当前源说明”，避免旧安装器自洽但说明落后仍显示PASS。
基线EXE因此仅因旧说明退出1；修改版全部payload、1044资源、2 DLC及版本核验通过。
回滚在独立EXE副本执行，并恢复到原SHA及相同的旧说明状态，修改版保持不变。

完整命令、实际输出、摘要和退出码位于
`build/phase-369-coverage-closure/VERIFICATION.txt`；
交付四件为`MODIFIED_FILE.exe`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`。
原基线134个保留项逐一核对：133项（含原版、配置、存档、runs）未变；唯一授权变化是测试清单，其旧版已独立保存。游戏启动／排版实测单列。
