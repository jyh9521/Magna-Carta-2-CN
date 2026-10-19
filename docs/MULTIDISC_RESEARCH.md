# 双盘合一与单一启动研究

## 当前优先级更正（2026-10-19）

用户确认主要目的是避免重复翻译，现决定暂缓合盘，优先共享译库、核心名词表及分批翻译。
两盘同路径Coalesced按完整hash共享翻译工作；44份独有Movies字幕按盘保留并单独提取。
已落实流程见 [SHARED_TRANSLATION_WORKFLOW](SHARED_TRANSLATION_WORKFLOW.md)。
下文保留2026-10-18的只读研究与未验证问题，不代表合盘仍为当前开发主线。

日期：2026-10-18。阶段：只读调查 / 可行性前置验证。**没有合并 ISO、修改 XEX、重封装或完成换盘游戏流程验收。** 汉化初始化已经完成，合盘是并行长期目标，不是文本提取、字体研究或汉化的前置条件。

## 1. 三个独立交付目标

1. 单一启动入口：一次启动，不要求玩家在换盘时手动选择另一盘。
2. 单一游戏目录：所需资源位于同一目录；可能仍需保留两份可执行/配置身份，不能据目录合并宣称单盘。
3. 真正单一镜像/容器：必要资源、身份与索引都在同一可运行容器中，不再依赖第二盘；目录 PoC 成功也不代表此目标成功。

最终优先研究真正资源合一（C），同时保留自动换盘（A）与单入口双盘（B）候选。只公开构建工具/差异补丁，不发布完整镜像、XEX、字体或原版资源。保持原版 Xbox 360 格式与玩法，优先 Xenia Canary；Xbox 360 原生兼容必须单独实测，不由模拟器结果推断。

## 2. 已有资源与版本（Verified）

两张 ISO 实际存在；本轮重新只读解析目录并重算完整 ISO SHA256，与已保存的完整成员哈希清单对应，身份未改变。

|项目|Disc 1|Disc 2|
|---|---|---|
|字节数|7838695424|7838695424|
|ISO SHA256|`23e96219aa8b2116239c35e6f65013329bfd298d46a726edffa5224498028ac5`|`9497b336d37529fd8ed1d0d64b560b130354fa1d6168fad1dd428e51e8f6bea2`|
|文件 / 目录|2016 / 12|2340 / 12|
|Title ID|4E4D0811|4E4D0811|
|Media ID|4C23BE53|4D4C6B53|
|Disc Number / Count|1 / 2|2 / 2|
|XEX raw Version / Base|00000001 / 00000001|00000001 / 00000001|

XDVDFS 分区基址 0xFD90000，扇区 2048 字节。其他区域、Title Update 和 DLC 未验证。XEX 魔数、完整哈希、字段地址与更多结构见 [RESOURCE_SURVEY](RESOURCE_SURVEY.md) 与 [FILEMAP](FILEMAP.md)。同 Title ID 不意味着两份 XEX 可互换。

### 基于完整成员 SHA256 的并集清单

|分组|文件数|自动处置|
|---|---:|---|
|同路径、同大小、同 SHA256|1631|仅记录相同；不删除任何原盘文件|
|同路径冲突|3|保留两盘完整身份，不选择覆盖方|
|仅 Disc 1|382|全部保留为独有资源，必要性待流程证据|
|仅 Disc 2|706|全部保留为独有资源，必要性待流程证据|

合计 2722 个不同文件路径。这是元数据并集，不是已构建游戏目录。

三个冲突是 `default.xex`、`MC2Game/Config/Xenon/Cooked/Coalesced.ini`、`MC2Game/Xbox360TOC.txt`。完整双方大小、ISO 偏移、SHA256、独有路径在本地 `build/multidisc-research/disc-comparison.json`；没有任何冲突被自动覆盖。

|独有资源扩展名|Disc 1|Disc 2|解释边界|
|---|---:|---:|---|
|.xxx|318|639|UE3 包候选；地图、脚本、语音等包内职责仍待解析|
|.bik|43|44|视频候选；未把编号自动解释为章节顺序|
|.txt|21|23|存在于资源分布中；用途需逐份确认|

共享字体、文本、UI/标题候选包均哈希相同，清单见 FILEMAP；这不证明字体支持简中。语音可能在包内；本轮未拆包或确认其完整性，不能宣布语音已纳入合并。

## 3. 新的本地静态证据

### 3.1 配置身份（Verified 字段；运行作用待验证）

重新比较已解析的两份 Coalesced.ini：恰有 4 个已解码 INI 值不同。

- 嵌入 `MC2Game.ini` 和 `Xe-MC2Game.ini` 各有 `[MC2Game.MC2DataManager] DiscNumber`：D1=1、D2=2。
- 上述两个嵌入文档各有 `[IniVersion] 1`：D1=`1249018610.000000`、D2=`1249018773.000000`。

**High-confidence deduction：** 数据管理配置和可执行头都保留盘身份，因此仅把独有文件复制到 Disc 1 目录仍可能触发盘号逻辑。
**Unverified hypothesis：** DiscNumber 是否直接控制换盘、仅作缓存，或参与资源检查；本轮没有修改字段来猜测。

### 3.2 TOC 的路径/长度/位置（Verified 关联；运行读取待验证）

两份 Xbox360TOC.txt 各 3063 行；所有行均符合五字段 `整数 整数 整数 路径 整数`。
将反斜杠转为斜杠并移除路径开头 `../` 后，与本盘目录精确匹配：

|检查|D1|D2|
|---|---:|---:|
|能对应本盘文件的行|2012|2336|
|第一字段与本盘字节大小相同|2011|2335|
|第三字段与本盘 XDVDFS 相对扇区相同|2012|2336|
|未对应本盘文件的行|1051|727|

大小唯一例外是 TOC 对自身的大小字段 0，并非实际文件长度。未对应项不能直接称为缺失资源或另一盘资源；含不在两盘上的候选/构建残留，需分别分类。

**High-confidence deduction：** 第三字段承担位置索引；目录版是否忽略它、镜像版是否依赖它均待运行证据。整合后路径存在不等于索引有效，不能原样选一份 TOC 或直接拼接两份 TOC。

### 3.3 XEX 差异（Verified 原始字节；代码差异未知）

两份 default.xex 长度相同。以头记录的 PE data offset 0x4000 分界，头区有 310 个字节不同，后部原始载荷有 19518602 个字节不同。
压缩、加密等封装会放大原始差异，因此这些计数**不证明**对应数量的游戏代码不同，也不证明只改盘号就能互换。未解密、反编译、修改或执行这些差异。

## 4. 旧研究复用

只读来源：[MagnaCarta2-Recompiled / RESEARCH_DISC_LAYOUT](https://github.com/jyh9521/MagnaCarta2-Recompiled/blob/bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47/docs/RESEARCH_DISC_LAYOUT.md)，作者 jyh9521，固定 commit `bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47`。
其双盘数量/三个冲突与本项目实测一致，可复用清单调查方法。其包依赖候选图不能自动当成本项目运行依赖结论；换盘触发、搜索顺序、存档与 TOC 语义原本也标为未知。本轮没有迁入原生重编译、ReXGlue、SDK、生成代码或运行时。

## 5. Canary 多盘能力核对（固定源码证据）

本轮查询默认分支 canary_experimental，固定 commit `50e9c715df05e3d93ac18e253d14956900683226`。

- [xam_content.cc L755–800](https://github.com/xenia-canary/xenia-canary/blob/50e9c715df05e3d93ac18e253d14956900683226/src/xenia/kernel/xam/xam_content.cc#L755-L800)：XamSwapDisc 会检查当前盘号；需要换盘时撤销 LauncherData 挂载、获取新盘路径、挂载选择结果并发完成事件。源码仍有“校验插入文件是否为所需盘”的 TODO。
- [emulator.cc L1330–1371](https://github.com/xenia-canary/xenia-canary/blob/50e9c715df05e3d93ac18e253d14956900683226/src/xenia/emulator.cc#L1330-L1371)：GetNewDiscPath 两条线程分支最终都调用 ShowDiscPicker，弹出文件选择器。这条路径不是无需人工选择的自动换盘。
- [PR #1032：路径预测自动换盘](https://github.com/xenia-canary/xenia-canary/pull/1032)：本轮 GitHub API 查询为 open、merged=false，head=`e8435c75e1038d3b85351362e45909332ecd657e`。提案不是已合入版本保证；后续选择实际 Canary 构建须重新核验。

这些是模拟器源码事实，**不是《真名法典2》会调用 XamSwapDisc 的证据**，也不代表对 Canary 所有其他加载路径作了否定。当前本地 xenia.exe 旧日志只标 master@95a5c3ee2，并未证明它就是该 Canary 源码构建；本轮未更换模拟器或进行换盘实测。

## 6. A/B/C 技术路线与风险

|路线|目标|现有依据|主要未决条件|当前结论|
|---|---|---|---|---|
|A 双 ISO 自动切换|一次启动、仍保留两盘|Canary 有换盘 API 实现|锁定实际支持自动选盘的构建；确认本作调用路径；盘身份匹配与存档|候选备选，未验证自动切换|
|B 单入口 + 双盘资源|一次启动、保留两套身份|两盘资源齐全，身份和冲突可保留|启动器本身不能替代 guest 内的挂载/路径切换；章节/完成事件/资源句柄|未验证；快捷方式不是实现|
|C 真正资源合一|单目录，最终评估单容器|独有文件与共享冲突已确定|三个冲突、DiscNumber、盘检查、TOC、跨包依赖、容器布局|具备进一步研究条件，尚未证明可行|

C 的顺序：先建立换盘前后日志/存档基线 → 只读定位调用与资源查找 → 明确 XEX/配置/TOC 冲突语义 → 审阅最小隔离实验方案 → 必要时测试单目录 → 单容器单独评估。复杂 XEX 修改或大型兼容性重构先报告，不自动实施。

Xbox 360 原生：认证/签名、系统光盘切换、设备路径、介质容量/寻址与打包限制仍需独立调查。主机侧单入口/Canary 路径预测不会自动移植为原机单盘支持。原机和 Xenia 分别记录结果。

## 7. 构建流程接口（规划，不是已实现功能）

用户原版 D1+D2 → 全镜像/版本校验 → 按盘提取与哈希 → 保留冲突的整合计划 → 经批准的资源整合 → zh-Hans 回写 → 容器/引用/字体校验 → 隔离可运行输出。

当前仅实现前段只读清单和差异报告；没有“整合构建”开关。未来每份输入使用 disc/path/hash 身份，所有保留/重定向决策写 manifest；相同内容的物理去重也不得删除唯一输入，须保留两盘逻辑引用与来源。回退只操作隔离派生输出，原件始终不动。

## 8. 可复现清单与比较

```powershell
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --output build/disc1-hashed.json --hash-image --hash-files
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 2).iso" --output build/disc2-hashed.json --hash-image --hash-files
python tools/compare_discs.py build/disc1-hashed.json build/disc2-hashed.json --output build/multidisc-research/disc-comparison.json
python -m unittest discover -s tests -v
```

输入/输出都使用独立文件名；已存在的清单与报告不会覆盖，重跑须指定新输出。比较工具检查完整 hash、边界、大小、重复/大小写路径；不验证上游清单真实性，因此先从实际 ISO 建立并核验清单。本轮对当前树与完整 ISO hash 重新检查通过。工具仅写元数据报告，不提取、删除、去重、合并或修补资源。

## 9. 未来验收门槛与待验证问题

宣称真正合盘之前，以下项目必须全部有证据：

- 两盘必要内容清单闭合，独有资源无遗漏；冲突各有明确处置依据。
- 单一启动；原换盘节点无需手选且可正常通过，前后章节可反复加载。
- 语音、过场、战斗、地图与剧情完整；不能仅以启动或标题画面通过。
- 换盘前/后/跨章节保存读档、旧档兼容、失败恢复均正常。
- Xenia Canary 固定构建/配置/输入身份、日志、画面及复现步骤齐全；原机另验。
- 单目录与单镜像分别验收；不得混用状态。
- 从原版双盘重新构建结果可核验；派生输出可回退且原 ISO hash 不变。

目前全部游戏内项目为**待验证**。下一项合盘研究任务仅是取得原版换盘节点前后可重现基线并定位真实换盘路径；汉化主线仍优先启动提示与字体绑定，不等待合盘完成。
