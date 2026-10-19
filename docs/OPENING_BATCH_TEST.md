# 开场 NPC、教程与菜单独立测试批次（2026-10-19）

## 文本范围与术语状态

`locales/zh-Hans/opening-batch.json` 是累计 231 条的源 hash 锁定计划：

- 保留 batch-001 的全部 27 条，包括开场 CSMB00_10 的 21 句。
- 新增 MC2NpcTalk / Ch00_0 全部 45 条。
- 新增 MC2Tutorial 前 42 条：场景动作、普通攻击、耐力/超限/过热、固有技、冲刺、
  场景道具、KAN、事件、队员/临时同伴和采集。
- 新增 81 条常用菜单/交互标签、36 条姓名/物品类别名称（累计名称 38 条）。
  菜单覆盖 MC2UI_Field 前 42 条、MC2UI_Pillar 前 14 条、MC2UI 的 ButtonA 与两个菜单帮助标签。
  姓名覆盖 MC2CharacterName 前 17 条；物品类别覆盖 MC2UI 前 19 条。

此批为 **draft**，不是全游戏翻译。`opening-batch.review.json` 保存逐条分类；
`terms.json` 与生成的 GLOSSARY.md 保存 23 条有源 ID 的批内统一候选，包括朱特、梅莉莎、
洁菲、守护者、哨兵、耐力、超限、过热、固有技、单手剑/双手剑和 KAN。
同一个韩文姓名在多 key 中使用同一译名；斯特拉斯等不宣称已确认跨作品身份。
候选统一不等于维护者定稿，也不把自动检查标为人工 reviewed。

## 字体工程的显式变化

**Verified / 离线字形测量：** 本批包含 673 个不同字面字符（保护标签不作正文收字）。
Noto Sans CJK SC 的 15px 字形并集为 18px，其中“箭”的单字 bbox 已达 17px，
超过旧 SmallFont 的 16px。22px 字形并集为 25px，超过 General_15 的 23px。
原有样本仍按旧计划构建；本批不缩小字号、不删字、不改译文迁就容量、不裁像素。

新的通用补字计划选项：

- `glyph_limit` 显式开启较大批次，上限 2048；不传仍限 128。
- `metric_height_growth: {original, candidate}` 必须锁定真实原最大高度，candidate 必须与
  `metric_height` 相等；未显式开启仍拒绝提高原最大高度，alpha 越界仍拒绝。
- 本批仅新增字形：General_15 指标 23 → 25px、SmallFont 16 → 18px；
  Subtitle 保持 29px。旧字形、旧 remap 和字图非补字区域保留。
- 三类字体、七个驻留/独立别名均重新收字；哈希锁定的生成计划在 `opening-fonts/`。
  General_15 / SmallFont / Subtitle 分别补 650 / 650 / 648 字，末字图分别扩为
  512×1024 / 256×1024 / 512×2048；逐别名证据记录在 operations 报告。

**Unverified / 运行布局：** 新增字形的最大高度可能影响行距、基线、裁切和框体容量。
离线覆盖、像素保护与容器往返不是游戏画面验收。不得沿用旧小样本的布局结论。

## 可复现构建

从项目根目录运行，输出目录必须全新。输入版本、Noto 字体和 LZX 来源沿用 BUILDING.md。
完整原文 catalog、原始游戏和生成完整资源只在忽略的 build/dist。

```powershell
python -m tools.sample_catalog export build/poc-game/disc1/MC2Game/Localization/Coalesced.int locales/zh-Hans/opening-batch.json --output build/opening-edit/catalog.json
# 从 opening-batch.review.json 按 ID 为本地 catalog 添加 text_kind，编辑后导入时显式检查标点。
python -m tools.sample_catalog import build/poc-game/disc1/MC2Game/Localization/Coalesced.int build/opening-edit/catalog.json --style-rules locales/zh-Hans/style-rules.json --output build/opening-edit/plan.json
python -m tools.prepare_text_sample --base-route locales/zh-Hans/story-subtitle/route.json --sample locales/zh-Hans/opening-batch.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output locales/zh-Hans/opening-fonts --glyph-limit 1024 --metric-height 0=25 --metric-height 1=18
python -m tools.build_font_route_probe --plan locales/zh-Hans/opening-fonts/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/opening-batch-disc1-lf
python -m tools.build_font_route_probe --plan locales/zh-Hans/opening-fonts/route.json --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/opening-batch-disc1-lf
$h=(Get-FileHash build/opening-batch-disc1-lf/manifest.json).Hash.ToLower()
python -m tools.prepare_oneclick_probe --source-root build/poc-game/disc1 --packet-root build/opening-batch-disc1-lf --manifest-sha256 $h --game-sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --output-root dist/MC2-opening-batch-disc1
```

已提交的 opening-fonts 无需每次重新生成；调整译文才重新收字生成全新目录。
本批不加载原生行宽补丁，避免把字体高度变更与代码补丁混在同一个对照变量里。
用户原 Xenia 配置有 SHA 校验；画质/输入设置不替换；新运行使用隔离 storage/cache/log。
一键入口依赖本机 repo 的工具、字体包 manifest 和 Xenia，不是可直接发给其他玩家的便携发布包。

## 用户具体测试清单

目录 `dist/MC2-opening-batch-disc1`：退出现有模拟器后双击 **开始中文测试.cmd**。
开发构建不代替用户运行游戏，也不自动导入旧存档；请从新游戏开始。

1. **标题和新游戏：** 标题登录/未登录提示仍为原文，此批不改该警告。
   确认能正常进入游戏，不把原文警告当成汉化未加载。
2. **完整开场：** 第一句“喂，你想害死我吗？”，继续看到“守护者”“斯特拉斯”“哨兵”
   及最后的“嘁……”。共 21 句；截图至少包含第一句、一处双行和一处三行。
3. **姓名与村民：** 检查朱特、梅莉莎、风息岛村长等标签。村内尽可能与各 NPC 交谈：
   “现在能做的”“店里新进了一批恢复道具”“你知道[单手剑]和[双手剑]的区别吗？”
   是定位参考，不从 key 猜具体 NPC 外观和准确触发顺序。Ch00_0 共 45 条；剧情推进可能改变分支。
4. **教程与按键：** 按剧情触发场景动作/战斗教程；核对 A/B/X、LT/RT、左摇杆按下等操作
   与原文对照一致，检查耐力、超限、过热、固有技和冲刺。稍后再测 KAN、事件与采集。
   采集页重点拍“箭头”“3秒”，验证新增高字形、数字及全角括号。
5. **菜单：** 打开主菜单，依次查看道具、战斗风格/技能、装备；检查选择、取消、是/否、
   单手剑/双手剑/木剑与物品分类。能力不足或技能不可学时的提示也要测试。
6. **保存/读取与样式：** 到可保存地点查看保存、读取、覆盖确认、取消；
   检查 A/B 显示为原样式按键，而不是裸露的 `<Styles:...>`。保存至测试用空栏位，退出后
   在同一中文入口读取验证；原文对照入口是独立 storage，不自动共享此存档。
7. **逐页排版：** 检查缺字/方框、顶底裁切、行距跳动、左溢/右溢、姓名和按钮遮挡、
   翻页节奏、问号/省略号。说明类单句无句中标点时无句末句号，剧情正文保留自然标点。
8. **原文回退对照：** 退出游戏，双击 **开始原文对照.cmd**，在相同场景和相同配置截图；
   它使用完整独立原文资源副本，不覆盖中文包或原始游戏。

反馈请附：具体文本、完整框体截图、操作步骤及该次 runs 下的 run.json/runtime.log。
批次以外出现原文属于预期；菜单其他字体、后续剧情、Disc2 和通关均未随本批验收。

## 离线证据

`build/opening-batch-verification/VERIFICATION.txt` 记录 baseline/modified/rollback 的真实命令、
退出码、输出和 SHA。231 个目标行回填后，其余 17,945 行逐项不变；逆向还原完整源 SHA。
ROLLBACK.sh 仅对另一个副本演练，并拒绝对 MODIFIED_FILE/ORIGINAL_FILE 证据文件执行覆盖。
它不是安装器；切回游戏原文使用原文入口。
