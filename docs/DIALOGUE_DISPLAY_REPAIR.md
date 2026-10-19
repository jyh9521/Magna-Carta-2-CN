# 对话标点、间距、换行与开场字幕修复（2026-10-19）

## 用户截图与纠正

用户截图显示首句“喂，你想害死我吗”末尾的问号消失；第二句的问号也消失，
并在框体仍有大量余宽时提前换行。用户还指出其他句中的标点、间距问题，以及启动提示和开场动画字幕未翻译。
先前“译文没有空格、句末有标点”的检查只覆盖字符串，遗漏了实际字形和运行布局，不能当作画面正确的证据。

原截图与逐步验证留在忽略目录 `build/dialogue-display-fix/`，不提交游戏画面。

## 已验证原因

**Verified / 真实候选字图：** 在旧包的 EngineMedium_Subtitle 中：

|字符|码点|旧 glyph index|实际 alpha 像素|
|---|---|---|---|
|…|U+2026|260|0|
|？|U+FF1F|1255|0|

原始引擎配置两处 MediumFontName 均为 Font.EngineMedium_Subtitle，SubTitleCharGap=3.0 保持不变；这是静态配置证据，不冒充运行调用跟踪。
二者不是没有 remap，而是 remap 指向了完全透明的字形。旧覆盖器只检查映射与正宽高，因此错判通过。
还发现 U+00B7 在 General_15 / Subtitle、U+2014 在 Subtitle 中透明。
“疑似删除最后一个字符”不是已证实的原因；实际透明问号也会在句中消失，透明省略号会占宽却无像素。
REA 对当前 PPC PE 映像仍报告 unsupported PE architecture；本次修复不使用未经证明的原生末字补丁。

**Verified / 提前换行：** 第二句原样本中的字面 `\n` 正好位于“备战，”之后，
与截图分行位置一致；这是保留韩文排版带来的硬换行，不是该帧框宽不足。
本批 66 条对白移除继承的 `\n`，但按稳定 ID、源 hash 和明确的源/目标换行数量逐条授权；
教程、属性、启动提示等功能性多行仍保留。未知标签、占位符和其他控制标记不得随之删改。

**Verified / 指标：** 旧补字的 BC3 cell 宽直接充当 USize，包含较多透明横向 padding。
新计划把 cell 占位和可见采样/推进宽度分离；按实际非透明 ink 宽保留最多两像素横向余量。
例如 Subtitle 新句号/逗号/问号的 USize 为 11/8/15，而不是 cell 的 32。
这提供了字图层面的间距修正；真实逐字定位、字偶距和全部 UI 的视觉效果仍须游戏内验证。

## 通用工具变化与保护

- `font_ink.py` 实际解码 BC3 alpha，检查 glyph rectangle 内有像素；空白字符单独排除，不把空格当缺字。
- `replace_blank_codepoints` 只允许重新映射经解码确认完全透明的旧字形。
  旧 tagged/native glyph、旧字图像素保留，只有明确选择的 remap value 改指新 glyph；不生成重复 remap key。
  旧的“全部 remap 保留”标志在发生替换时为 false，另报告未选 remap 的保护结果。
- 可选 glyph `metric_width` 控制 USize，必须位于 cell 内；alpha 超过采样宽度仍拒绝，不缩放、不裁字。
- `line_break_policy={source_count,target_count}` 是按条目显式计数的布局例外，默认仍严格保留全部 token。
  反向还原交换两个计数，仍逐字节恢复整个原 Coalesced。
- route 的 `verify_glyph_ink=true` 对所有显式七别名检查全部译文和字幕的字形像素，
  `reports/ink.json` 与字体/文本/TOC 报告一同纳入 manifest 并独立重放。

字号仍为 22/15/27px；新增字形高度沿用上批显式的 25/18/29px。
三类字体末图都显式扩展至 2048px 高，原宽分别为 512/256/512；该纹理尺寸的实际兼容性待游戏验收。
本轮不改 UI 框体、不改 XEX、不添加原生行宽补丁、不调整用户画质或输入配置。

## 启动提示和开场字幕

`display-fix.json` 累计 262 条 Coalesced 回填：原 231 条基础上重排对白，并补齐 MC2UI_TCR 的 31 条
登录/存储/保存/下载内容/光盘提示。`display-fix.review.json` 仍标 draft，词汇并非人工定稿。

另有 49 条开场字幕，独立于 Coalesced：

- `MC2Game/Movies/csm_prologue.txt`
- `MC2Game/Movies/csm00-10.txt`
- `MC2Game/Movies/csm00-12.txt`
- `MC2Game/Movies/csm00-20.txt`

文件实测是配套 Bink 的 UTF16LE BOM 文本，不因用户称呼“即时演算”而假定其技术类型。
公开 `display-subtitles/*.json` 只保存源 hash、cue 起止时间、源值 hash 和译文；原 txt/video 均不提交。
新 `subtitle_text.py` 保留 header、BOM、CRLF、SYNC 毫秒时间、KRCC class、清屏 `&nbsp;` 与原 `<br>` 结构。
KRCC 是运行格式字段，不能为了中文改成另一类名。没有重编码视频，也没有修改配音。
兰兹海姆、修恩泽特、伊芙琳、露等新增专名为本次草稿选择，需后续术语审核。

## 可重建步骤

已提交 display-fonts 是完整 hash 锁定的计划，常规重建无需重新准备计划。仓库根运行，输出须新建：

```powershell
python -m tools.build_font_route_probe --plan locales/zh-Hans/display-fonts/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/display-repair-disc1
python -m tools.build_font_route_probe --plan locales/zh-Hans/display-fonts/route.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/display-repair-disc1
$h=(Get-FileHash build/display-repair-disc1/manifest.json).Hash.ToLower()
python -m tools.prepare_oneclick_probe --source-root build/poc-game/disc1 --packet-root build/display-repair-disc1 --manifest-sha256 $h --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/MC2-display-repair-disc1
```

改译文后，重新收字用 `python -m tools.prepare_text_sample`，基底仍为 `opening-fonts/route.json`，
sample 为 `display-fix.json`，显式传 `--glyph-limit 1024 --repair-blank --fit-ink-widths`，
并用四个 `--additional-plan` 指向 display-subtitles 下的 JSON，输出到全新计划目录。
文档末尾的两条像素命令是无需启动游戏的针对性回归；旧包失败退出 1、新包成功退出 0。

## 新入口与验收顺序

目录 `dist/MC2-display-repair-disc1`，双击 **开始中文测试.cmd**；同目录保留 **开始原文对照.cmd**。
旧包保留，但不再把旧包的字符串检查当作本次显示验收。

1. 退出旧模拟器，从新入口进入；如触发未登录提示，应显示“你尚未登录。”及完整中文确认内容。
2. 新游戏不要跳过序章、岛上开场、瞭望台前后动画；检查字幕、标点、清屏时间和 `<br>` 不裸露。
   序章首条“兰兹海姆历1149年1月……”，岛上首条“那时的我，只是个一无所知的毛头小子。”。
3. 对照用户这两张截图：第一句末尾必须看到“？”；第二句必须看到末尾“？”，
   原“备战，”之后不再被继承的 `\n` 强制断开。实际宽度不足时仍允许引擎自然换行，不承诺所有分辨率永远单行。
4. 第三句核对“北部军打过来又怎样？”和末尾“吗？”，再检查句中问号、省略号、中点及逗号后的间距。
5. 检查长对白的自然换行、边界、行距、顶底裁切、姓名与按钮遮挡；回归 NPC、教程、菜单和存取档。
6. 有异常时退出并用原文对照同场景比较，附完整框体截图和对应 runs 的 run.json/runtime.log。

开发阶段只做离线构建/像素检查/启动前准备，不自动启动游戏；新包实际画面和字幕加载仍待用户验收。
后续章节、全部动画字幕、Disc2 与通关不在本次完成范围。

```powershell
python -m tools.font_ink build/opening-batch-disc1-lf/candidate/MC2Game/CookedXenon/font.xxx --font-object EngineMedium_Subtitle --characters "？…" --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -m tools.font_ink build/display-repair-disc1/candidate/MC2Game/CookedXenon/font.xxx --font-object EngineMedium_Subtitle --characters "？…" --lzx-library build/lzx/native-verified/ue3_lzx.dll
```
