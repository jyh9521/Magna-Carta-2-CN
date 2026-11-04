# 韩版 Xenia 图形候选：60 帧、tiling 与后处理（阶段358）

2026-11-05（Asia/Tokyo）。本轮按用户要求只做离线研究、修改副本和验证，**未启动游戏或模拟器**。原版、配置、存档、现有入口及阶段357 AF 候选不变；未重建 ISO、完整游戏副本或安装器。

## 当前结果

| 项目 | 韩版候选 | 证据性质 |
|---|---|---|
| 60 FPS | `0x8237C264: 39600002 → 39600001` | 已验证请求间隔 2→1 的编码、回调与 vblank 计数链；60 tick/s 下标称 30→60，实际游戏 FPS 待验 |
| 光照／阴影修复 | `0x8320AD30`、`0x8320AD98`：BE32 `1→0` | 已验证 tiling 选择器／开关及渲染消费者，移植上游双变量 workaround；像素修复待验 |
| 后处理 | `0x8249B3C4: 419A01BC → 480001BC` | **独立实验实现**：跳过每视图的 post-process-chain 代理构建；与美版原分支同源／等效关系未证明 |

三个区块均为 **`is_enabled=false`**，可以单独选择。它们未写入活动补丁目录、未接入已有游戏入口。

上游思路仍归属 boma，见 [上游报告](XENIA_PATCH_UPSTREAM_RESEARCH.md)。后处理候选单独署为独立韩版研究，不将它冒称为 boma 分支的逐条重定位。前轮 AF 保留，见 [阶段357](XENIA_PATCH_KOREAN_PORT.md)。

## 输入与版本守卫

| 输入 | SHA-256 |
|---|---|
| 原版 Disc 1 XEX | `26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f` |
| 原版 Disc 2 XEX | `44976b6bf9f978312f14387ea4e60bbdfffd1a8aa72f31841f7a58ab2ebef586` |
| 两盘独立还原的共同 native image | `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9` |
| 当前 Canary EXE | `82f7637bff8895b5e9ce625131a40d2ad709e9111dc55f59e03ffe3737a46d33` |
| 原配置（保持） | `e8f986eafaded303a8ac123f77a38b72144b077e9a2b743a9b6e76fab0369fb1` |

原生映像大小 20,119,552 bytes，基址 `0x82000000`，Title ID `4E4D0811`，模块 hash `0FAA852250B131D1`。模块 hash 的导入跳板处理规则沿用阶段357已重建的结果，不直接 hash 原始解码代码。

本机短提交对应完整固定提交 `96ce1ac47ee7646deac2a2c9c912351e8ff0edee`。8 项公开主源 URL/SHA 与语义参考记录在 `references/xenia-graphics-offline-research.lock.json`，完整源码/PDF缓存只在忽略的 build 目录。

## 已查证：60 帧候选的本地链

### 编码与请求语义

`0x8248AD88..0x8248AE2C` 的 RHI 调用者取得 `0x83250944` 的设备指针，调用 `0x8237C180`。该函数在 `0x8237C230` 读取 `device+0x351C`，将请求映射为回调 flags 的 bits 8–11：

| 请求值 | 原编码间隔 | 修改编码间隔 |
|---:|---:|---:|
| 0 / 1 | 1 | 1 |
| 2 | 2 | **1** |
| 4 | 3 | 3 |
| 其他受测 u32 | 0 | 0 |

`0x8237C264` 原指令为 `li r11,2`，修改为 `li r11,1`。其它 flags 位保持。**本轮证明的是请求为 2 时的路径，不把设备实际运行值恒为 2 当作已观测事实。**

### SCRATCH 协议与 guest 回调

1. `0x8236D6C8..0x8236D740` 初始化命令流：从 `device+0x2A94` 转换物理地址，发给 SCRATCH_ADDR（寄存器 `0x1DD`），然后写 SCRATCH_UMSK（`0x1DC`）值 `0x00020037`，包含 bits 4/5。
2. `0x8237C2A8` 选择 `0x8237BFD0` 为回调，flags 传给 `0x8236CF50`。该函数写 type0 header `0x0001057C`，之后两个 word 为 callback / flags。
3. [寄存器定义](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47ee7646deac2a2c9c912351e8ff0edee/src/xenia/gpu/register_table.inc) 确认 `0x57C/0x57D` 是 SCRATCH4/5；[Xenia scratch 写回](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47ee7646deac2a2c9c912351e8ff0edee/src/xenia/gpu/command_processor.cc) 将已启用项写到物理 SCRATCH_ADDR 的 `+0x10/+0x14`。
4. `0x823783BC..0x823783D4` 将 `0x8236D170` 和设备 userdata 注册到 VdSetGraphicsInterruptCallback。其 source1 分支在 `0x8236D188..0x8236D1A0` 读取 `device+0x2A94` 的 `+0x10` callback / `+0x14` flags 后间接调用。
5. `0x8237C018` 从 callback 参数提取间隔；`0x8237C07C..0x8237C0A8` 用旧 target+间隔、当前 tick 和延迟条件计算新 target。其排队／等待逻辑使用 `device+0x40A4` 作为刷新计数。

离线验证对 SCRATCH4/5 的硬件写回使用**固定源码契约桥接**：PPC 发包和 guest 参数读取分别解释，中间由显式模型按上述 Xenia 规则填入合成共享内存。这不是实际运行 GPU／中断的记录。

### 为什么该计数代表刷新

[GraphicsSystem](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47ee7646deac2a2c9c912351e8ff0edee/src/xenia/gpu/graphics_system.cc) 的 MarkVblank 发送 source0 中断；[内核 DPC](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47ee7646deac2a2c9c912351e8ff0edee/src/xenia/kernel/kernel_state.cc) 传给 guest 的两参数为 source / userdata。

韩版 ISR 的 source0 路径读 `0x7FC86544` bit0；Xenia ReadRegister 的 `0x1951` case 返回 1（vblank）。该分支调用 `0x8237BEB8`，`0x8237BED4..0x8237BEE0` 将 `device+0x40A4` 增一。因此限频链是 **guest vblank 目标调度**，不是 VdSwap 参数。

本机原配置为 `vsync=true`、`framerate_limit=0`、`time_scalar=1`，符合当前源码选择标称 60 tick/s 的条件。请求间隔 2→1 因而对应标称 30→60 次机会；负载、其它计时器、实际帧率与操作手感仍待游戏验收。没有修改任何计时或图形配置。

[Microsoft XNA 2.0 官方文档](https://download.microsoft.com/download/D/F/6/DF6BE85E-8523-46DF-9DA6-730EABDDFDE4/XNA_Game_Studio_2.0_en-us.pdf#page=3853) 第3853页也说明 One/Two 对应每次／每两次显示刷新，支持 Xbox 360；该文档只补充间隔意义，不用于猜测 MC2 结构偏移。超过60的时序问题保留上游说明，不宣称此补丁适用于任意刷新率。

## 已查证：光照／阴影 workaround 的两个变量

UTF-16BE `TILING`（`0x8217BEB4`）和 `TILINGMODE`（`0x8217BEC4`）直接关联 `0x8248D7F0..0x8248D9A8` 的控制台分支：

- `TILING` 切换／清零 `0x8320AD98`；对应上游命名 GUseTilingCode 的角色。
- `TILINGMODE` 先检查该开关，再对 `0x8320AD30` 循环、解析和夹限到 `0..4`；对应 GTilingMode 的角色。
- 两个原 BE32 值均为 1。指令/数据使用关系已验证，和上游符号名的对应是高置信语义匹配，非恢复了原始调试符号。

`0x8249ED64..0x8249ED7C` 的场景分支在开关为零时跳过 tile setup；视图分支 `0x8249FFD4..0x8249FFE8` 同样跳过子像素偏移。`0x826D9708..0x826D9744` 以 mode 索引 surface 表。

**mode 0 的原始标签是 `1280x720 4xAA, 3 tiles`，单独 mode=0 不等于关闭 AA。** 本候选照上游组合同时设置 mode=0、开关=0，由开关绕过 tiling 路径。surface 表初始为 BSS 零指针，离线只证明索引和调用，不冒称已看见初始化后的 surface/GPU 对象。

## 已查证：独立后处理实验候选

`SHOW POSTPROCESS` 绑定 mask `0x40`；UPostProcessEffect 与 Uber 的谓词检查同一位。主视图构造函数 `.pdata` 范围为 `[0x8249AF60,0x8249B590)`。

- `0x8249B300/B304/B308` 将 view 的 `+0x6D4/+0x6D8/+0x6DC` 代理数组清空，基类 copy 不复制旧代理。
- `0x8249B3BC` 读 view+0x10 的链；`0x8249B3C4` 原为链空时跳到 `0x8249B580`。
- 非空链的 +0x3C/+0x40 为 effect 数组／数量，经 vtable+0x114 判断、+0x110 创建 scene proxy，再加入视图代理数组。
- 把 `419A01BC` 改为 `480001BC` 后，无条件走既有空链出口；`B580→B584` 共用返回。
- `0x824A0F14..0x824A0F20` 的消费者对代理数量<=0跳过数组读取和虚调用，继续下一视图。

已验证跳过代理构建与空数组分支，**未证明所有最终 GPU 后处理均消失，也未证明与美版 `0x824289E0` 分支完全等价**。故独立命名为 Experimental skip post-process-chain proxies，不混入“已逐条移植的原版补丁”结论。

## 工具与离线验证

计划：`references/probes/mc2-graphics-offline.json`，包含4个期望字写入、33个上下文窗口及3个独立关闭的 patch sections。实际只有5字节发生变化：

```text
0x8237C267: 02 -> 01
0x8249B3C4: 41 -> 48
0x8249B3C5: 9A -> 00
0x8320AD33: 01 -> 00
0x8320AD9B: 01 -> 00
```

`tools/runtime_patch.py` 的可选 patch_sections 必须把所有守卫写入恰好分配一次；重复、遗漏、未知地址、类型错误和 section 身份覆盖均报错。省略新字段时，旧 AF／强制折行 TOML 输出逐字节不变。

`tools/ppc_fragment.py` 是标准库限定片段解释器：只读取已声明窗口，每次最多256步；不执行宿主调用、不加载游戏、不实现完整 guest/GPU。未知寄存器、未知内存、未支持指令、BL和窗口逃逸均报错。合成内存与输入独立，原始映像只读。LFS只保留原始32位，不计算FP/FPSCR；carry模型为64位，受测 LWZ 限定的间隔分支在word/doubleword carry下选择一致。

每态 **214次有界片段回放**：编码、vblank增量／目标、scratch初始化／发包／参数读取、tiling两个gate／索引、后处理空数组／分支／消费者。包含请求3的减法下溢边界，记录含可重建输入及逐PC轨迹；不是214次游戏或GPU执行。

| 状态 | 间隔 | tiling开关/mode | 后处理代理链 | 退出状态 |
|---|---:|---|---|---:|
| BASELINE | 2 | 1/1 | 原逻辑 | 0 |
| MODIFIED | 1 | 0/0 | 绕过 | 0 |
| ROLLBACK | 2 | 1/1 | 原逻辑，原SHA恢复 | 0 |

原映像 SHA-256 为 `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`；修改映像为 `146a2356dee997d7995c7c8bb862e7433a7d9b35ac466c7c7bd4a304ddb7d27d`。隔离回滚副本与原映像逐字节一致，交付修改副本保持修改状态。

另验证全部8种独立开关组合，并在内存中与阶段357 AF、既有汉化强制折行写入合成：无重叠、可完整还原，同样214个图形片段通过。没有改这些既有候选或包。

源码修改前 runtime14 + sampler7 通过；修改后相关回归90项通过。推送前干净源码全量门禁和远端身份以本地 `VERIFICATION.txt`／`closeout.json` 为准，静态门禁不替代上述游戏验收。

## 复现

从仓库根目录执行，输出目录必须为新路径；若原生映像尚不存在，先按 [NATIVE_IMAGE](NATIVE_IMAGE.md) 从用户原版 XEX 还原。

```powershell
python tools/runtime_patch.py --image build/xex-native-verification/final/disc1-pycryptodome.bin --plan references/probes/mc2-graphics-offline.json --game build/poc-game/disc1/default.xex --exe xenia/xenia_canary.exe --output build/phase-358-xenia-graphics/candidate
python tools/inspect_graphics_patch.py build/phase-358-xenia-graphics/candidate/original.bin --plan references/probes/mc2-graphics-offline.json --brief
python tools/inspect_graphics_patch.py build/phase-358-xenia-graphics/candidate/modified.bin --plan references/probes/mc2-graphics-offline.json --brief
```

补丁为 `candidate/4E4D0811 - Magna Carta II KOR Graphics Candidates.patch.toml`，三项默认关闭。builder锁定实际XEX/映像/模拟器，未知版本先重验，不移除守卫。

四件本地证据位于 `build/phase-358-xenia-graphics/`：`MODIFIED_FILE.bin`、`DIFF_FILE.json`、`VERIFICATION.txt`、可执行的 `ROLLBACK.sh`。回滚脚本只接受该目录内独立修改副本，拒绝源文件、交付文件和硬链接。

额外证据：`fragment-replays.json`、`independent-toggle-replays.json`、`composition-check.json`、`fps-evidence.asm`、`tiling/`、`postprocess/`、`present-sources/`。它们与完整原生映像均留在忽略的 build，不进入公开仓库。
