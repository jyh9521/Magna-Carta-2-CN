# Xenia 补丁韩版移植调查与 16×AF 静态候选

日期：2026-11-05（Asia/Tokyo）。公开来源见 [上游报告](XENIA_PATCH_UPSTREAM_RESEARCH.md)。

## 结论

| 美欧版功能 | 韩版调查结果 | 本轮交付 |
|---|---|---|
| 60 FPS | 显示间隔相关代码只有线索，尚未证明实际限帧赋值 | 不生成候选 |
| 动态光照 / 阴影修复 | 两个 tiling 全局尚未定位 | 不生成候选 |
| 关闭大部分后处理 | 分支与目标基本块尚未定位 | 不生成候选 |
| 16×各向异性过滤 | 已独立验证调用链、查表和 GPU 位域 | **默认关闭的韩版静态候选** |

官方固定快照只有 `4E4D080B` 的美欧版条目，未发现独立日版 / 韩版条目。
五个上游原地址在当前韩版的内容均不支持直接套用；不是改 Title ID/hash 即可移植。
本轮未启动游戏、未部署补丁、未改现有配置、存档、测试资源、ISO 或安装包。

## 已查证：输入身份

| 对象 | SHA-256 / 标识 |
|---|---|
| 韩版 Disc 1 XEX，19,611,648 bytes | `26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f` |
| 韩版 Disc 2 XEX，19,611,648 bytes | `44976b6bf9f978312f14387ea4e60bbdfffd1a8aa72f31841f7a58ab2ebef586` |
| 两盘分别还原的 native image，20,119,552 bytes | `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9` |
| 原生基址 / Title ID / 模块 hash | `0x82000000` / `4E4D0811` / `0FAA852250B131D1` |
| 本机 Canary `96ce1ac47` EXE | `82f7637bff8895b5e9ce625131a40d2ad709e9111dc55f59e03ffe3737a46d33` |
| 原配置（本轮保持） | `e8f986eafaded303a8ac123f77a38b72144b077e9a2b743a9b6e76fab0369fb1` |

上述文件及两盘映像均重新读取校验。两个 XEX 不互换；同一解码映像支持相同指令地址，不等于双盘游戏内验收。解码方法见 [NATIVE_IMAGE](NATIVE_IMAGE.md)。

### 模块 hash 必须包含导入处理

本机版本的 [CalculateHash](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47/src/xenia/kernel/user_module.cc#L1148-L1184) 对代码页 `[0x822D0000,0x82EA0000)` 计算 XXH3-64。
直接计算原始解码代码得到 `6CBEBC778AC32F0C`，这不是补丁匹配 hash。
[SetupLibraryImports](https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47/src/xenia/cpu/xex_module.cc#L1224-L1275) 会先改写内核导入跳板。

本轮按真实 XEX 的 `0x103FF` 导入表确认了 xam.xex / xboxkrnl.exe 的 246 个 type-1 跳板，仅在隔离映像中替换为 `44000042 4E800020 60000000 60000000`（`sc 2; blr; nop; nop`），再算同一区间得到 `0FAA852250B131D1`，与保留的旧运行日志一致。这是当前源码规则下的离线还原，不是本轮新运行的加载日志。

证据为 `build/phase-357-xenia-patches/module-hash-reconstruction.json`、`import-normalized-code.bin`、`xxhash_code_pages.c` 及 `hash-build/Release/code_hash.exe`。XXH3 使用已有本地 Zstd 1.5.7 的 xxhash 头文件私有副本；只在副本取消禁用 XXH3 的宏，原始上游树不变。首次使用裁剪配置发生链接失败，启用副本并重编译后通过。导入名称表有非零尾部填充，应按声明名称数量解析，不假定填充全零。

## 已查证：直接照搬的错位

地址均为 VA，不使用 PE raw pointer。

| 美欧写入位置 | 韩版原字或包含该字节的字 | 观察 |
|---|---|---|
| `0x8237BFEF` | `0x8237BFEC: 3D608200` | `lis r11,0x8200`；照搬会变成 `lis r11,0x8201` |
| `0x8321BD2B` | `0x8321BD28: 3F298809` | 非布尔值；邻域可解为浮点序列，未证明是 GTilingMode |
| `0x8321BCC3` | `0x8321BCC0: 3F569B8D` | 不支持 GUseTilingCode 布尔变量假设 |
| `0x824289E0` | `4BEA7761` | `bl 0x822D0140`，不是已验证的后处理条件分支 |
| `0x8244A5D0` | `897F2ABE` | `lbz r11,0x2ABE(r31)`，不是 AF 参数加载 |

浮点表用途仍未命名，不声称完整数据结构已被识别。不同函数的地址差不统一，单点偏移不代表其余补丁也匹配。

## 已查证：AF 静态链

唯一候选修改为 VA `0x8244A2B0` / image RVA `0x44A2B0`：

```text
38A00004  li r5,4
38A00010  li r5,16
```

实际只有 RVA `0x44A2B3` 一个字节由 `04` 变为 `10`。

1. 调用者 `.pdata` 范围为 `[0x8244A1F8,0x8244A30C)`；`0x8244A210` 将 r28 置零。
2. `0x8244A2A8` 复制到采样器索引 r4；`0x8244A2B0` 设置参数；`0x8244A2B8` 调用 `0x8236FF98`。随后索引加一、与 16 比较、回到参数加载处，覆盖 0–15。
3. 被调函数用 `(sampler+0x30)*24` 寻址 fetch 常量；仅在 mag/min anisotropic-walk 任一标志开启时更新当前 fetch，总是保存请求值到 `device+0x2E9C+sampler`。
4. `0x82150308` 的 17 项 BE32 表为 `[0,0,2,2,3,3,3,4,4,4,4,4,4,5,5,5,5]`。
5. `table[4]=3`、`table[16]=5`，通过 `rlwimi r9,r10,25,4,6` 写入 fetch dword3 的位 25–27，掩码 `0x0E000000`。

独立语义依据为 Xenia 的 [AnisoFilter](https://github.com/xenia-canary/xenia-canary/blob/838850fed8389bdb28dc38f89bcb73bb43db1494/src/xenia/gpu/xenos.h#L127-L135) 及 [texture fetch constant](https://github.com/xenia-canary/xenia-canary/blob/838850fed8389bdb28dc38f89bcb73bb43db1494/src/xenia/gpu/xenos.h#L1237-L1252)。因此这是把该调用点的最大 AF 请求从 4× 提高到 16×，**不是强制所有纹理启用 AF**。被调函数没有通用参数边界检查，本计划只接受已核对的 4 和 16。

三个完整窗口散列存于 `references/probes/mc2-sampler-anisotropy.json`，并验证整幅原始映像及期望指令。REA 对真实 PPC PE 返回架构不支持；这里使用本地 Capstone 5.0.7、已有 `.pdata` 读取器和逐字节核对，不冒称 REA 反编译或 GPU 实测。

## 复现与产物

通用 `runtime_patch.py` 新增可选 `description` / `author` / `is_enabled`；省略新字段时，旧强制折行补丁 TOML 的输出字节完全保持。新候选明确 `is_enabled=false`，没有写入活动补丁目录。

```powershell
# 从仓库根目录执行，输出目录必须不存在。
python tools/runtime_patch.py --image build/xex-native-verification/final/disc1-pycryptodome.bin --plan references/probes/mc2-sampler-anisotropy.json --game build/poc-game/disc1/default.xex --exe xenia/xenia_canary.exe --output build/phase-357-xenia-patches/candidate
python tools/inspect_sampler_patch.py build/phase-357-xenia-patches/candidate/original.bin --plan references/probes/mc2-sampler-anisotropy.json
python tools/inspect_sampler_patch.py build/phase-357-xenia-patches/candidate/modified.bin --plan references/probes/mc2-sampler-anisotropy.json
```

映像尚未生成时先按 NATIVE_IMAGE.md 从用户原版 XEX 还原。计划锁定本轮原版和模拟器身份；更换版本时先重验，不移除 hash 守卫。产物是 `candidate/4E4D0811 - Magna Carta II KOR 16x AF.patch.toml`。

四件本地证据位于 `build/phase-357-xenia-patches/`：

- `MODIFIED_FILE.bin`：独立构建的修改映像；根目录名与候选文件硬链接，不与原版硬链接。
- `DIFF_FILE.json`：原/新 SHA-256、完整指令及唯一变化字节。
- `VERIFICATION.txt`：实际命令、输入、字面输出、退出状态。
- `ROLLBACK.sh`：只恢复该目录内独立副本，拒绝交付候选、原版及硬链接。

## 验证与剩余项

| 状态 | 静态参数 | AF 枚举 | 退出状态 |
|---|---:|---:|---:|
| BASELINE | 4 | 3（4×） | 0 |
| MODIFIED | 16 | 5（16×） | 0 |
| ROLLBACK | 4 | 3（4×），原 SHA-256 恢复 | 0 |

修改映像 SHA-256 为 `751b537d1e057f3516c8d3cdec93285b79a247ff2edc12cb204ac1a5c57cb842`。
隔离回滚副本与原映像逐字节相等，交付候选保持修改状态。每态 256 个**静态派生状态模型**案例覆盖 4 种标志 × 4 种原位模式 × 16 个采样器，验证其余位不变；这不是 256 次真实 PPC 或 GPU 执行。

修改前 runtime-patch 14 项通过；修改后 14 项 runtime-patch + 7 项 sampler + 22 项 XEX + 16 项 launcher，共 **59 项通过**。原版、候选、回滚及四件证据均重开校验。

**待游戏验收：** 当前模拟器实际加载、远处/斜面纹理差别、帧率与稳定性、双盘切换。
**待研究：** 60 FPS 的参数链、两个 tiling 全局、后处理分支。`0x8237C264` 仅保留为枚举映射线索，不发布为正确限帧地址。匹配版本的美版或日版原始 `default.xex` 可进一步用于跨区函数/数据对照。

本轮没有游戏资源变动，现有测试目录无需增量刷新；没有生成 ISO、完整游戏副本或新安装器。仅提交工具、测试、结构化计划与文档；完整映像和实验产物留在忽略的 build 目录。
