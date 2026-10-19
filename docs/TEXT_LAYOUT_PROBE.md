# 扩展中文布局探针（2026-10-19）

## 当前证据

- **Verified / 用户截图：** 2026-10-19 用户提供 Disc1 标题警告弹窗，
  `踢击! FONT CHECK`、英文及三处手动换行可见，没有观察到两字缺字。
  截图只证明这一个场景；同时补过两种字体，不能据此单独判定实际字体路线。
- **Verified / 离线：** 本轮样本保留同一 LogIn_NewGame 稳定 ID、原容器及
  原文 SHA256；仅修改一条记录，保留原来的三个字面 `\n` 控制码及顺序。
- **待用户验收：** 扩展字形的游戏显示、长句自动折行、标点禁则、边界裁剪及按钮区域。
  本轮不启动模拟器，不把静态通过视为游戏显示通过。

## 样本

源文件：`locales/zh-Hans/text-probe-layout.json`。它是测试文字，不是正式警告翻译。

```text
中文测试：长句与标点
“你好！”（测试），。！？
ABC 123 / 中文
这是一段没有手动换行的中文长句，请检查文字能否自动换行并完整显示到这里。
```

前三处换行是受保护的显式控制码。最后一段没有空格、软换行或隐藏断行字符，
只有它在游戏中出现的额外折行才能作为自动换行观察。不要把前面三次手动换行当自动换行通过。
末尾必须能看到 `到这里。`。记录逗号/句号/右引号/右括号是否单独落在行首、
左引号/左括号是否留在行尾，以及 CJK/ASCII 的基线和间距。

## 字图与指标

样本含 53 个不同字面字符；两种字体各需增加 45 个字符。
General_15 最后一张 atlas 原为 512×64，空余只能放 3 个 24×24 cell。
本候选显式 `atlas_height=128`，仅扩高至 512×128，宽度不变，
保留旧 tiled 存储和旧可见行像素；逐块验证新字之外像素不变。
SmallFont 原 256×256 空位足够，无需扩图，继续显式 identity-256。
三个 General_15 和两个 SmallFont 别名全部装配并重新比对完整指纹与字面覆盖。
General_15 最大字高仍为 23，SmallFont 为 16；不修改字体家族选择、UI尺寸或 XEX。

通用补字计划上限由 16 扩至 128，继续拒绝越界、重叠、无字形及坏版本。
扩图只允许显式 raw-atlas、单 mip、增大的二次幂高度（128..2048）。
新计划按原字图全部 glyph 的 BC3 block 矩形避让，不复用旧 padding 的不明字形区域。
较大样本还暴露了旧 raster 的可选底边留白导致 SmallFont 上缘越界：
现在仅在需要时使用这一个可用像素，按整组 bbox 检查共享基线；不缩小字、不裁切字。
这只证明离线字图/指标一致性，不证明引擎运行时扩图兼容或实际断行规则。

## 复现（项目根目录，Python 3.12+）

原件：用户提供的 Disc1 完整目录，见 RESOURCE_SURVEY.md；字体和 LZX 依赖见
WARNING_FONT_ROUTE_PROBE.md。以下 `build/layout-probe-disc1` 必须是新目录。

```powershell
python tools/build_font_route_probe.py --plan locales/zh-Hans/layout-probe/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/layout-probe-disc1
python tools/build_font_route_probe.py --plan locales/zh-Hans/layout-probe/route.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/layout-probe-disc1
```

更换样本文字时，用通用生成器自动收字/找空位/生成 hash 锁定计划，再执行上述装配工具：

```powershell
python -m tools.prepare_text_sample --base-route locales/zh-Hans/font-routes-disc1.json --sample locales/zh-Hans/text-probe-layout.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --output build/new-layout-plans --lzx-library build/lzx/native-verified/ue3_lzx.dll
```

输出目录必须是项目内全新目录、与原件不相交；生成器不写原件或启动游戏。
提交的 `locales/zh-Hans/layout-probe/` 是本次可重建锁定计划，直接复现无需重新生成。

## 一键入口与验收

本地准备路径：`dist/MC2-layout-test-disc1/开始中文测试.cmd`。
它保留完整独立游戏副本，先核对六资源 hash，再沿用用户原配置启动；
日志、缓存及存储隔离到该入口的 runs/。旧两字入口 `dist/MC2-oneclick-disc1/` 保持不变。
准备命令：

```powershell
$h=(Get-FileHash build/layout-probe-disc1/manifest.json).Hash.ToLower()
python tools/prepare_oneclick_probe.py --source-root build/poc-game/disc1 --packet-root build/layout-probe-disc1 --manifest-sha256 $h --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/MC2-layout-test-disc1
```

双击中文入口，在与上次相同的标题弹窗截图；不要先按 A/B 关闭弹窗。
检查：完整字形、九类中文标点、ASCII/数字混排、末段额外折行和末尾 `到这里。`、
左右边界及下方 A/B 按钮是否被挤压或覆盖。若末段仍单行超框，应记录自动换行失败，
不预先插入手动换行掩盖问题；若文字缺失，区分缺字与整段被裁切。
原文对照入口为同目录 `开始原文对照.cmd`；旧两字入口用于已知成功基线比较。
退出新测试后，双击原文对照或旧入口即可切回独立副本，不需手动覆盖资源。
构建器在另一个副本逐项演练六资源恢复；真实恢复后的游戏行为仍需用户观察。

仅准备 Disc1；不把 Disc1 TOC 套到 Disc2，不宣称双盘切换验收。
完整游戏与候选资源只留在忽略的 build/、dist/，不提交原版资产。
