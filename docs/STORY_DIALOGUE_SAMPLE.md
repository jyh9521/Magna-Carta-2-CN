## 2026-10-19 用户反馈：正文空白（后续更正）

用户截图确认：姓名“주토”和 A 按钮可见，宽框正文空白；中文主入口及同资源无行宽修复入口均空白。
因此旧样本游戏验收失败，行宽补丁不是空白的必要条件。先前 General_15 模板静态链不等于活动字体。
本地核查发现 font.xxx 和 Startup_int 的 EngineMedium_Subtitle 各缺 103 个字面中的 101 个，
旧版覆盖报告只检查显式提供的 General_15/SmallFont，遗漏 Subtitle。

新候选：`locales/zh-Hans/story-subtitle/route.json` 原样复用九句文本和前两种字体计划，
只增加 Subtitle 两别名的 101 个缺字；原 512×512 字图无需扩高，27px raster、29px 字形上限，
保留旧字形/映射/像素和其他字体的完整指纹。不把新增覆盖判为已证明的实际字体选择或空白根因。

新入口：`dist/MC2-story-subtitle-disc1/开始中文测试.cmd`，默认不加载原生行宽补丁。
请与旧目录的“开始未修复对照.cmd”在同一句比较，二者都不加载补丁、文本相同，区别是新增 Subtitle 覆盖。
标题原文、原画质/输入配置保持不变；完整原文入口仍保留。若仍空白，下一步应做 ASCII 文本绑定探针，
不继续把其他无关字体全部补上当成已修复。

构建/复核命令沿用下文 build_font_route_probe，将 --plan 换为 locales/zh-Hans/story-subtitle/route.json，
输出换为 build/story-subtitle-disc1。prepare_oneclick_probe 输出 dist/MC2-story-subtitle-disc1，
省略 --patch-bundle 和 --patch-manifest-sha256。所有完整资源仍在忽略目录中。

# 真实剧情中文样本与用户宽框验收（2026-10-19）

## 样本边界

本轮不改标题警告，也不扩大 UI 框体。`locales/zh-Hans/text-sample-story.json`
仅修改 Disc1 INT 容器中的九条真实对话：

| 文档 / section | key | 数量 | 首句或观察点 |
|---|---|---:|---|
| MC2CSMB.int / CSMB00_10 | voc_csmb_0010_00..06 | 7 | 喂，你想害死我吗？ |
| MC2NpcTalk.int / Ch00_0 | 00_101_00..01 | 2 | 现在能做的， / 朱特，你也别再偷懒了， |

原版容器 SHA256：`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。
候选容器 SHA256：`6c460afcb6fcc269792dcc85d4b6f5285cc817177c26377630645b52414a2397`。
保留八个原有字面 `\n`（各记录数量为 0/1/1/1/1/1/0/1/2）、顺序和稳定 ID。
不添加软断行、空格或额外手动断行。其余 18167 条物理行记录原样保留。
前七条之后恢复原文属于本次有意限定的样本范围，不是提取遗漏。

译文为韩文原文对应的 draft 样本，不是正式剧情翻译或全游戏译库。
“朱特”是样本中的暂定音译，未提升为已审核术语；说话人身份没有从纯字符串表猜填。
INT 后缀不代表英文，本次读取的这些值是韩文。

## 已验证与待验证

**Verified / 静态绑定：** `MC2Game.xxx` 的
`UI_Core.Scenes.Scene_Balloon_*.Balloon_Base.Dialogue` 及
`Scene_YesNoBal_0.Balloon_Base.Dialogue` 含
`<Strings:MC2CSMB.CSMB00_10.voc_csmb_0010_04>` 引用。
既有 UI 图解析器解析其 StringRenderComponent / AssignedStyleID，六状态序列化候选
均通向 Startup_int 的 `Font.General_15`（14 个标签、84 条状态候选路径）。标签模板引用不证明某一时刻的活动剧情、
实际对话框像素宽度或 native 动态覆盖；CSMB00_10 场景包没有同一解析范围内的匹配标签。
完整本地对象/字体/偏移报告在 `build/story-probe-verification/`。

**Verified / 字节：** 原容器提取 → 九条可编辑 catalog → 导入 hash 计划 → 回填 →
再次提取，导入计划与提交计划相等；全部 18176 条记录身份和非目标值逐项一致。
独立副本逆向回填还原整个原容器 SHA，而不是只把九条字符串看起来改回去。
无改动原容器 parse/serialize 也逐字节一致。修改后的副本保持为中文。

**Verified / 候选装配：** 两种字体的五个别名都验证字面覆盖、最终完整语义指纹、
旧字形/remap 与非补字像素保护、TOC 大小和六资源恢复副本。
本次共 103 个不同字面字符，各字体补 103 个（含中文标点）。
General_15 末图显式 512×64 → 512×256；SmallFont 显式 256×256 → 256×512。
仍使用原有 22/15px raster 设置、23/16 glyph 高度上限，不缩字、不裁字、不调整 UI 尺寸。
扩图是新样本计划显式锁定的行为，不把离线解码成功当成游戏兼容性已通过。

**Verified / 受控宽度模型：** 九条记录各自最后一个原始换行分段，按两字体实际 USize、
origin 0/193/640、width 128/380/396/800/1200、scale 0.5/1/1.5/2 回放。
原版和补丁各 1080 组合，原版 220 组失败，补丁 0 组失败；
两边各 750 组无需折行，均零失败；完整计数见本地 `layout-summary.json`。
补丁仅沿用 WRAP_WIDTH_FIX 的行起点扣除，不改本次文本或框体。
无需折行的组合必须前后零失败；模型不是活动 UI 宽度测量、完整 CPU 或游戏执行。

**待用户验收：** 真实开场对话、NPC 宽框、活动字体、字图扩高兼容、缺字/裁切、
翻页节奏及运行时修复效果。本轮准备工具没有启动模拟器；不将自动验证写成游戏通过。
过场动画 Subtitle 字体/其他剧情框/Disc2 不在这九条样本的验收结论内。

## 可重建流程

从项目根目录运行。输出路径须全新；原件和可选依赖沿用 BUILDING / TEXT_LAYOUT_PROBE。

```powershell
python tools/sample_catalog.py export build/poc-game/disc1/MC2Game/Localization/Coalesced.int locales/zh-Hans/text-sample-story.json --output build/story-edit/catalog.json
# 只编辑 catalog 中的 translation；保留 id/source/selector/source_sha256。
python tools/sample_catalog.py import build/poc-game/disc1/MC2Game/Localization/Coalesced.int build/story-edit/catalog.json --output build/story-edit/plan.json
python tools/build_coalesced.py build/poc-game/disc1/MC2Game/Localization/Coalesced.int build/story-edit/plan.json --output build/story-edit/Coalesced.int
```

编辑后的译文先通过 source/token/换行/编码检查；新字面可能需要重新收字和计划锁定，
不能直接把新文本覆盖到本次字库。全部原文 catalog 只在忽略的 build 中。
本次固定译文可直接用已提交的锁定计划重建：

```powershell
python tools/build_font_route_probe.py --plan locales/zh-Hans/story-sample/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/story-sample-disc1
python tools/build_font_route_probe.py --plan locales/zh-Hans/story-sample/route.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/story-sample-disc1
$h=(Get-FileHash build/story-sample-disc1/manifest.json).Hash.ToLower()
$p=(Get-FileHash build/layout-width-runtime-patch/manifest.json).Hash.ToLower()
python tools/prepare_oneclick_probe.py --source-root build/poc-game/disc1 --packet-root build/story-sample-disc1 --manifest-sha256 $h --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/MC2-story-test-disc1 --patch-bundle build/layout-width-runtime-patch --patch-manifest-sha256 $p
```

运行时补丁重建步骤仍见 WRAP_WIDTH_FIX。`audit_wrap_layout.py` 新增可选 `--entry-id`，
用于在多条计划中选择一条真实对白的最后原始分段；不传仍保持旧单样本默认选择。
只审计一个分段的报告不证明其余显式分行布局。

## 一键实测

目录：`dist/MC2-story-test-disc1/`。三个入口使用两份完整独立资源副本，非硬链接。

1. 退出已有模拟器，双击 **开始中文测试.cmd**；保留用户原配置、不改输入和画质。
   按正常流程开始新游戏，进入岛上开场对话，不以标题警告或待机视频作为验收。
   标题警告仍是原文，这是预期行为。全新隔离 storage 不自动导入现有存档。
2. 第一处应出现“喂，你想害死我吗？”。保存含完整框体的截图。
   重点再拍第 3 条“北部军打过来又怎样？”及
   第 7 条“南部军……不是为了帮我们才待在这里的。”。
   第 3 条含原有换行；第 7 条完全没有手动换行。
3. 检查左右边界、每行位置、末尾标点、姓名/按钮遮挡、下一句切换与缺字。
   宽框能容下整句时保持单行也是正常结果，不要求人为强迫折行。
   能继续进村时，再寻找以“现在能做的，”开头的 NPC 两句样本。
   NPC 活动角色/触发条件仍需实测，不从 key 猜具体人物。
4. 退出后双击 **开始未修复对照.cmd**，同一中文资源和相同配置、不装原生行宽修复。
   在相同位置截图。它与中文主入口共用 candidate 游戏树，运行日志/存储分别隔离。
5. 退出后双击 **开始原文对照.cmd**，使用独立 raw 原文副本，不加载行宽修复。
   这是同场景原文资源对照，不是压缩封装兼容性的对照。

若第一句仍是韩文，请提供该画面和对应 runs 的 run.json/runtime.log；不要当成中文失败的确证，
需先确认活动语言/场景与资源读取。使用补丁主入口时检查 `[Patches Applied]` 和
`Patcher: Applying patch` 日志；无修复入口不应带本次补丁。
回退测试入口只需退出并改用原文对照，不覆盖原始游戏/XEX/全局模拟器配置。
`build/story-probe-verification/ROLLBACK.sh` 只演练离线文本副本逆向回填，不用于卸载游戏。

## 维护边界

新通用工具只处理 locale-neutral 的 catalog/ID/hash，不包含中文硬编码。
生成的完整字体包、原始 catalog、游戏副本和离线报告留在 build/dist，不提交。
公开仓库只保存九条新译文、锁定补字计划、工具、测试和技术记录。
