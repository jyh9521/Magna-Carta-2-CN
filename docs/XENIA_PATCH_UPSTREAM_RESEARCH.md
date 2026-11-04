# Xenia《MagnaCarta II》上游补丁调查

调查日期：2026-11-05（Asia/Tokyo）。本页记录公开上游证据；韩版地址重定位与本地二进制验证另行记录，不把上游补丁说明当作韩版运行验收。

## 已查证：现成的美版补丁

直接读取 `xenia-canary/game-patches` 的 `main`，固定到提交
`fe957a050e37f5a1e3f485ca43c2e37ee2a9c92d`。完整源码快照的 521 个 ZIP 条目中，对文本内容和路径检索 `magna.?carta`、`4E4D080A/B/C`、`4E4D0811`，只命中一个补丁文件：

[4E4D080B - Magnacarta2.patch.toml（固定版本）](https://github.com/xenia-canary/game-patches/blob/fe957a050e37f5a1e3f485ca43c2e37ee2a9c92d/patches/4E4D080B%20-%20Magnacarta2.patch.toml)。

文件标识：

- `title_name = "Magnacarta 2"`
- `title_id = "4E4D080B"`
- `hash = "B4CC5A66F752EBC3"`，对应 `default.xex`。
- 媒体注释为 Disc 1 `60DA537D`、Disc 2 `5DB3BBBC`，上游注明 USA / Europe；这些行被注释，不是启用的匹配条件，也不证明其他欧洲版 Title ID 通用。
- 四项作者均为 **boma**，默认均为 `is_enabled = false`。

| 功能 | 写入类型 | 上游虚拟地址 | 新值 | 上游说明 |
|---|---|---|---|---|
| 60 FPS | `be8` | `0x8237BFEF` | `0x01` | 改为 `D3DPRESENT_INTERVAL_ONE`；超过 60 FPS 有游戏时序问题 |
| 动态光照 / 阴影修复 | `be8` | `0x8321BD2B` | `0x00` | `GTilingMode = 0` |
| 同一光照修复的第二个写入 | `be8` | `0x8321BCC3` | `0x00` | `GUseTilingCode = FALSE` |
| 关闭大部分后处理 | `be16` | `0x824289E0` | `0x4800` | 文件未提供原始完整指令与被跳过的基本块 |
| 16 倍各向异性过滤 | `be32` | `0x8244A5D0` | `0x38A00010` | `li r5, 0x10` |

上述表格是补丁定义，不含原版期望字节，不能充当跨版本地址验证。

## 历史与作者依据

文件首次加入提交是
[b54a55fae0e2db7b8f9c44d752ffbe7a7e25743c](https://github.com/xenia-canary/game-patches/commit/b54a55fae0e2db7b8f9c44d752ffbe7a7e25743c)，来自 boma 的 [PR #169](https://github.com/xenia-canary/game-patches/pull/169)（2022-08-03）。作者把黑色阴影问题联系到 UE3 的 tiled MSAA，并报告关闭相关 tiling 后的改善；这是上游作者对其测试版本的结论，不是本项目已验证的韩版结论。

后续该文件历史只显示 2022-09-04 的帧率说明更新与 2026-07-13 的 Redump 链接更新；当前地址和值仍见上表。研究保留作者与来源，不把这些补丁思路记为本项目原创。

## 未发现：独立日版 / 韩版补丁

在上述固定官方源码快照内，没有独立的日版或韩版条目。GitHub 官方仓库 issue / PR 检索 `Magnacarta` 只命中 #169；`"Magna Carta"`、`4E4D080A`、`4E4D0811`、`4E4D080C` 没有命中。对游戏名、日文名、相关 Title ID 与 Xenia / patch.toml 的公开网页检索也没有找到可独立复核的日版补丁定义。

这是有界搜索结果，不表示所有私人补丁、Discord 附件或未索引分支都不存在。

## 已查证：hash 的含义与加载条件

当前 Xenia Canary 源码固定到
`838850fed8389bdb28dc38f89bcb73bb43db1494`：

- [`PatchDB::GetTitlePatches`（209–219 行）](https://github.com/xenia-canary/xenia-canary/blob/838850fed8389bdb28dc38f89bcb73bb43db1494/src/xenia/patcher/patch_db.cc#L209-L219) 同时检查 Title ID 和模块 hash。
- [`UserModule::CalculateHash`（1215–1254 行）](https://github.com/xenia-canary/xenia-canary/blob/838850fed8389bdb28dc38f89bcb73bb43db1494/src/xenia/kernel/user_module.cc#L1215-L1254) 找到首尾 `XEX_SECTION_CODE` 页，起点为 `base + first_page_index * heap.page_size`，终点为 `base + (last_page_index + 1) * heap.page_size`，对该内存区间计算 **XXH3-64**。这不是整个 XEX 文件的 SHA-256，也不是 PE 文件散列。
- [官方 README（固定版本）](https://github.com/xenia-canary/game-patches/blob/fe957a050e37f5a1e3f485ca43c2e37ee2a9c92d/.github/README.md) 明确区分匹配 hash 与移植：版本不同需要重新定位补丁，而不是仅替换 hash。标题栏或日志显示补丁已应用，只能说明补丁进入写入流程。

## 历史韩版线索：只改标识的博客不是移植证明

[Wuru4 的 2022-11-26 原始文章](https://wuru.tistory.com/196) 记录在 `4E4D0811`、TU0、旧 Canary 自定义构建上修改 Title ID/hash，正文要求保留原 patch 地址。作者以日志中补丁写入记录作为完成依据；正文没有提供原字节核对、反汇编对照或功能 A/B 测试。正文示例另有 `4E4D0801` 的 Title ID 笔误，hash 只写作 `0FAA...1D1`，完整内容放在截图。

因此该文章仅证明存在历史尝试，不能据此接受其“只换标识即可跨区”的一般化结论。韩版是否匹配必须由本地映像独立验证。

## 推断与下一步判据

本轮后续已完成一项 AF 韩版静态重定位与三态验证，见 [韩版报告](XENIA_PATCH_KOREAN_PORT.md)。另验证模块 hash 使用导入处理后的代码；246 个内核跳板离线归一化后得到 `0FAA852250B131D1`，而不是直接 hash 原始解码代码。

四项都是少量 PowerPC 指令或 UE3 全局状态写入，原则上有逐项重定位的空间；是否成功仍取决于韩版对应函数和变量的实际证据。

1. 锁定韩版 XEX / 解码映像的完整 SHA-256、大小、Title ID、模块 hash，并分别核对两盘。
2. 60 FPS 要定位实际 Present 参数赋值；光照修复要找到相应 tiling 状态和读写引用；后处理要核对完整分支和目标基本块；各向异性过滤要确认采样状态设置调用。
3. 不采用全程序统一偏移，不将“旧地址恰好存在”视为对应关系。
4. 使用默认关闭、原字节 / hash 守护的独立候选，逐项完成修改与回滚测试后，再由用户做游戏内对照。离线验证与真实帧率、画面、时序、稳定性验收分开报告。
