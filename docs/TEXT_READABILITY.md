# 字距与非剧情句号修订（2026-10-19）

## 用户反馈与修订

**Verified failure：** 用户截图确认上一版对白及开场字幕字距过紧。此前按 ink 压缩 USize，左右仅约各1px，窄笔画汉字也随 ink 变窄；文字虽未缺失，但可读性退化。

**Verified offline：** 新计划 `locales/zh-Hans/readability-fonts/route.json` 保留22/15/27字号及25/18/29高度，对新字形显式设置 `ink_padding={left:2,right:3}`。宽字符字母（Unicode L + EastAsianWidth W/F）advance 至少为字号+5，即27/20/32；多余留白居中分配。标点采用自身 ink 宽+5，不统一塞满汉字宽格。不改译文空格，不缩放笔画，不改引擎的 SubTitleCharGap，不改旧字形/用户配置/XEX。

**Runtime pending：** 离线像素及资源验证不是游戏画面验收；相同场景的视觉效果、自动折行、姓名与菜单宽度仍待用户截图。

非剧情标点规则已扩展到所有明确分类的非剧情条目，而非仅物品描述：无内部标点的单句不以 `。` 或 `.` 结尾；多句、含逗号的句子及问号/感叹号不据此删除。对描述按行检查，对系统提示等按完整逻辑消息检查，避免误删多句提示的末句句号。剧情 dialogue/narrative/story_subtitle 保留语气标点。未分类条目必须先分类。

`readability-fix.json` 累计262条，相比 display-fix **仅4条系统文本去除末尾句号**：存储设备没有剩余空间、没有已保存的游戏数据、正在检查下载内容、将添加下载内容。66条对白和49条独立字幕内容不变；控制码、占位符及已核验的去硬换行策略保持。

## 可重建流程

```powershell
python -m tools.build_font_route_probe --plan locales/zh-Hans/readability-fonts/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/readability-spaced-disc1
python -m tools.build_font_route_probe --plan locales/zh-Hans/readability-fonts/route.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/readability-spaced-disc1
```

重新收字：沿用 `opening-fonts/route.json` 作基底，sample 使用 `readability-fix.json`，prepare_text_sample 显式传 `--glyph-limit 1024 --repair-blank --fit-ink-widths --ink-padding 2 3 --wide-letter-tracking 5`，并传原四份 display-subtitles 的 `--additional-plan`。输出目录必须新建。未选择新参数的历史构建行为保持兼容。

新安装可按 DIALOGUE_DISPLAY_REPAIR.md 的 prepare_oneclick_probe 命令替换 packet-root/manifest/output。已存在的完整测试副本可用 `tools.refresh_oneclick_probe`：显式锁定旧 PREPARED.json 和新 manifest 的 SHA256，先核验候选、原文对照、XEX及新包，再完整备份待写文件，原子替换候选资源和入口。拒绝原版目录、不同资源集、变动的原文对照和原生补丁包；失败回退已写文件。它不复制整盘，也不触碰 runs、存档、原文对照、用户配置或原游戏。

本地刷新入口仍为 `dist/MC2-display-repair-disc1/开始中文测试.cmd`，刷新备份在 `build/readability-verification/package-backup`。不自动启动模拟器。REFRESH.json 保留每个文件前后hash，旧资源与入口可恢复。

## 手动测试清单

1. 退出旧模拟器，从同一个“开始中文测试.cmd”启动；确认启动“正在检查下载内容”末尾没有句号。
2. 不跳过开场字幕，检查“向陛下——转！”字距及破折号/感叹号间距；检查居中、完整显示与清屏。
3. 回到“自作自受。大家都在忙着备战，你居然还能睡得着？”；检查字距、逗号/句号/问号留白，不出现人为插入空格。
4. 检查“喂，你想害死我吗？”及长对白；标点完整，宽度不足时自然折行，没有继承的硬换行。
5. 检查姓名、菜单、教程、NPC及存取档：文字不挤压、不越界、不裁切；非剧情单句无多余句号，多句提示保留必要标点。
6. 同场景可用“开始原文对照.cmd”核对；异常请附完整截图和相应 runs 的 run.json/runtime.log。

## 2026-10-30选中物品用字的后续合同

阶段337针对689条物品名称涉及的595个宽字母码点，解除其固定最小advance，以左2/右3透明留白为裁边目标，保留原本较小的边距及全部alpha>0字形/阴影，图集和字号不变。不是回到旧的左右各1px方案。595字以外的字格不变；共享别名同步，其他界面同一字也会变窄。原生字芯间隙在七别名检查为5–8px，游戏内整体阅读/折行仍单列验收。历史段落描述的是对应阶段合同；当前数据和证据见 [阶段337](PHASE_337_LOADING_ITEM_SPACING.md)。
