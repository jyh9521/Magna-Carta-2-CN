# 强制折行测宽修复候选（2026-10-19）

## 场景与证据边界

用户扩展样本截图显示：标题弹窗窄框内汉字、标点和 ASCII 可见，末段确实自动分行；
前两行却越过左框，最后的“里。”居中。原截图只保存在忽略的本地验证目录。
**用户另行指出：标题弹窗很小，游戏内剧情对话框宽得多。两类场景必须分别验收。**
本轮不把小弹窗当剧情宽框的验收结果，不宣称剧情也有此问题。

**Verified / 静态：** 两处原版警告组件已设 `WrapMode=3 / CLIP_Wrap`、
横纵 `TextAlignment=1 / UIALIGN_Center`，无需把对齐改成左对齐或加手动换行。
TitleMap_MSPT 原 SHA256 为 e094df8399beac753e07a1ee388d5192b8f0a721fa854d786104de7439e98395。
两个 WrapMode 值逻辑偏移 9403144/9407507，横向对齐值 9403201/9407564。

**Verified / 指令与受控回放：** 下述静态分支确有“绝对右沿当相对宽度”差异，
原始/修改/回滚指令片段分别复现/消除/恢复该差异。
**High-confidence deduction：** 此差异解释截图中“强制分割行左偏、最后短行正确居中”的形态。
**待用户确认：** 警告的实际活动路径、补丁加载和修复后游戏像素；本轮不启动游戏或模拟器。

## 缺陷链与最小修改

原生虚拟映像 base=82000000，SHA256
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`。
REA 对该 PPC PE 报 unsupported architecture；本轮使用本地 Capstone5.0.7 与现有
独立 .pdata/映像读取器，未把这些结果标成 REA 成功分析。

| 地址 | 实际作用 |
|---|---|
|826c8850..826c9030|折行函数，.pdata 声明504字、完整 SHA 锁定|
|826c8a7c|f30=f25，累计右沿从本行起点开始|
|826c8c4c|f30 += XScale × glyph advance|
|826c8ca0|普通词组完成：f26=f30-f25，得到相对文字宽度|
|826c8e50|无空格长词强制分割：f26=f30-XScale×溢出字形；**未扣 f25**|
|826c8fb4|f26 写入 WrappedStringElement +0x0c（行宽）|
|826c9c60|UIString 分段调用该折行函数|
|826c9dc0..9dd0|返回行宽/高复制到 split node +18/+1c|
|826ca838..826cae34|按节点汇总各行 extent 并绘制；826cac3c..5c 为居中计算|

居中分支使用单/双精度 0.5 常量（82096f70/820a9860）。错误宽度多计 origin，
故居中起点额外左移 origin/2。窄框更容易触发强制分割；宽框若不需要折行，
不会经过本次修改的分支。这里不是“把小框改宽”的修复。

仅修改16个映像字节，不改 XEX 原件、文本、字库、UI尺寸、字体选择或自动分行的位置：

```text
826c8e50: ef40f77c -> 487c5d50   b 82e8eba0
82e8eba0: 00000000 -> ef40f77c   原 fnmsubs f26,f0,f29,f30
82e8eba4: 00000000 -> ef5ac828   fsubs f26,f26,f25
82e8eba8: 00000000 -> 4b83a2ac   b 826c8e54
```

跳板位于原 .text 结束82e8eb9c与下一 BINK 起点82e8ec00之间的100字节全零对齐区域，
处于原 XEX kind1 可执行页，且不与任何 .pdata 声明函数相交。
构建时复核整个映像 SHA、三个完整上下文函数 SHA、预期原字节、零区及可执行页。
跳板是无栈、无调用、无 link 的两次浮点运算/直接返回；不建立伪造 .pdata 记录。

此候选不做段落均衡；末行仍可能只有“里。”。短末行本身不判失败，
验收重点是所有实际折行使用正确行宽、留在框内且分别居中。

该分支对无空格长词通用，不按中文码点硬编码。单个字形本身宽于容器等其他极端路径
未由此补丁修复；排版禁则、运行时字体偏移与所有剧情窗口仍需独立测试。

## 已运行的验证

1. 指令片段受控回放：216组（不同 origin、scale、advance、长度）。
   原版180组失败；修改0组失败；在另一副本回滚后180组失败恢复，原映像 SHA 完全恢复。
2. 原样本真实 glyph USize 与原 Coalesced 回写结果：120组受控布局组合，覆盖两种字体、
   origin0/193/640、宽128/380/396/800/1200、scale0.5/1/1.5/2。
   基线58组失败；修改0组失败；33组无需折行的组合前后均无失败。
3. 本轮样本完全未改，Coalesced.int SHA仍为
   `70abfd5406bd9908b07c1e6a61187a2d16a8d35dab40c197c647337ae048c730`，
   三个原显式换行控制码保留，末段仍无空格/软断行/手动换行。
4. 新游戏副本六资源全部匹配旧扩展样本；XEX、模拟器及原配置 hash 不变。
   模拟器 prepare-only 检查确认补丁副本写进本次 run/storage/patches，不启动进程。

回放不是完整 CPU/FPSCR 模拟或游戏执行；受控布局明确假设 glyph USize advance、
零附加运行时 bias/kerning，宽度和缩放不是从屏幕测得的活动值。
宽框组合证明的是这一模型/分支不回归，不是游戏内剧情宽窗口验收。

## 重建与复核

先按 NATIVE_IMAGE.md 从用户 Disc1 XEX 重建映像；按 TEXT_LAYOUT_PROBE.md 构建字体/文本包。
本轮使用相同原版资源与用户模拟器，不需要更改 TOML 配置。

```powershell
python tools/runtime_patch.py --image build/xex-native-verification/final/disc1-pycryptodome.bin --plan references/probes/ui-string-wrap-width.json --game build/poc-game/disc1/default.xex --exe xenia/xenia_canary.exe --output build/layout-width-runtime-patch
python tools/replay_wrap_width.py build/layout-width-runtime-patch/original.bin --plan references/probes/ui-string-wrap-width.json
python tools/replay_wrap_width.py build/layout-width-runtime-patch/modified.bin --plan references/probes/ui-string-wrap-width.json
```

构建输出必须是新目录。原片段回放退出1表示成功复现缺陷；修改回放退出0。
`runtime_patch.py` 不重写加密 XEX，只生成 Xenia 的16字节运行时补丁与保留的离线映像副本。
`audit_wrap_layout.py --help` 给出实际样本/字体的120组合复核参数；报告须新建在输入目录之外。

## 一键入口与 A/B 复测

```powershell
$rh=(Get-FileHash build/layout-probe-disc1/manifest.json).Hash.ToLower()
$ph=(Get-FileHash build/layout-width-runtime-patch/manifest.json).Hash.ToLower()
python tools/prepare_oneclick_probe.py --source-root build/poc-game/disc1 --packet-root build/layout-probe-disc1 --manifest-sha256 $rh --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/MC2-layout-fix-disc1 --patch-bundle build/layout-width-runtime-patch --patch-manifest-sha256 $ph
```

- `dist/MC2-layout-fix-disc1/开始中文测试.cmd`：相同长句/字库，加原生测宽修复。
- `开始未修复对照.cmd`：**同一中文资源副本和同一配置**，不加载本次原生修复。
- `开始原文对照.cmd`：原文 raw-controls，不加载原生修复。

退出前一次模拟器，再双击下一入口；先查看标题栏是否有 `[Patches Applied]`，
并截图相同窄弹窗。期望各自动折行都位于框内、按各自真实宽度居中、末尾“到这里。”完整。
不改变字体大小/窗口尺寸来掩盖问题。游戏内宽剧情框应另截图验收；不从这个弹窗外推。
日志应包含 `Patcher: Applying patch` 与 `Correct forced-wrap line extent`；缺少加载证据时先检查补丁入口。

配置逐字节快照、storage/content/cache/log 隔离规则不变。该版本 Xenia 从 storage_root/patches
读补丁，因此新 launcher 在每次 run 的 storage 下复制已校验补丁；**不是写全局 xenia/patches**。
XEX SHA、模拟器 SHA、可信 manifest SHA与每个 TOML SHA 均在启动前核对；版本不符即停。
真实补丁加载与像素仍等待用户复测，不把 prepare-only 当成已加载游戏。

退出模拟器后改用“开始未修复对照”即回退；原 XEX/资源从未被此运行时补丁覆盖。
旧入口未安装补丁，继续保留。本地 ROLLBACK.sh 另用于离线映像副本的字节回滚演练，
不是用户游戏目录卸载脚本。

## 外部格式来源

本作函数缺陷与指令修复为本轮静态发现；Xenia 补丁格式、模块 hash 匹配、
storage_root 查找和可执行页映射来自 Ben Vanik / Xenia contributors，
BSD-3-Clause，xenia-canary/xenia-canary 的50e9c715d版本；精确文件 SHA见
`references/runtime-patch-research.lock.json`。只作格式研究，未集成上游源码/运行库。
原版游戏数据、模拟器二进制与完整派生映像都只在忽略的 build/、dist/ 中。
