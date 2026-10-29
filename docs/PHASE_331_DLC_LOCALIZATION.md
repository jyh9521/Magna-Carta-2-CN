# 阶段331：短剧与特殊武器 DLC 汉化

## 已核实结果

输入是用户提供的两个 `4E4D0811/00000002` LIVE 包，原文件未修改。容器身份、成员表、块链及 SHA1 树见 [STFS 记录](PHASE_331_STFS.md)。本轮没有启动游戏，也没有生成 ISO 或完整游戏副本。

| 包 | 内容 | 修改后字节数 | 修改后 SHA256 |
| --- | --- | ---: | --- |
| `18B8C8A148D63B0BAFE42CF63E203D482BE029C24E` | 3集短剧 | 115937280 | `0232648ce81e9986cd6dc27cb841426ac021113ad9440dba826927560271f2f3` |
| `A6075CF4FC20724B15DA064AB2FCAB16B1CCC3FD4E` | 12种特殊武器 | 13336576 | `7acd0f68c228ec8c18e90cd70073695d084b4c78ed4649be450dc7f6bd97234e` |

* 两包 `spa.bin` 的 XSTR 都有221条字符串，原表内容一致。共享译表修改210条，分别写入两包，共420处。其余11条为空值、技术占位或既有公司名称等，按源摘要显式保留。成就分值、编号、标志、图片、默认语言编号及非字符串 payload 保持不变。
* 包名、简介的 English 槽0与 Korean 槽6，以及 `title_name` 汉化，共10个头字段。保留控制台语言、许可证字段、title ID、缩略图；不写不存在的简中槽16。
* 短剧字幕引用本体 `Coalesced.int`，不是在DLC中另藏一套韩文对白。完整解析568个 ShowCSMBSubtitle 对象及613个 SoundNodeWave 对象，获得568+25=593处字幕文本引用，解析错误0。最终593处均唯一绑定本体中文，按当前字宽/禁则/静态行数预算检查全部通过；这是引用数，不是独立对白数。
* 原包存在23处字幕键错配（每集4/13/6处），其中4处指向不存在的键。16处有同名声音对象字幕佐证；另7处由 `#005_2` 下相同 FaceFX 标识的独立字幕对象直接佐证。没有按相邻数字猜补。只改等长 ASCII FString 的 `SubTitleWrap[].Subtitles[].Text`，不改声音、动画、时点和人物标识。
* 12个 `.DLC` 文件各为1MiB空格，属于武器解锁标记，不是待翻译文本。保留文件名和全部字节。逐个绑定本体 `data_weapon.xxx` 的 ItemName、Description、ShortDescription 共36个字段，名称和说明均已有中文、字形覆盖完整。资源标识与开发注释不冒充玩家显示文本。
* DLC不含 Font/MultiFont；240个 Texture2D 导出中，37张短剧场景图逐张离线查看，未发现需替换的烧录文字。3个 Data_ExtraDrama 标记包不含显示文字。图像、模型、音频保持原数据。

## 可重建源数据与通用工具

* `locales/zh-Hans/dlc-strings.json`：编号、源文字摘要、译文与显式保留项。
* `locales/zh-Hans/dlc-packages.json`：两原包 SHA256、大小、SPA 身份、头字段与依赖摘要。
* `locales/zh-Hans/dlc-assets.json`：23个字幕字段的源包/导出/佐证导出摘要和精确字段选择。
* `tools/stfs_package.py`、`tools/xdbf_strings.py`：独立的容器和字符串表技术；语言数据不写进解析器。
* `tools/ue3_subtitle_refs.py`：有独立同声音标识佐证的精确字段修订。
* `tools/build_dlc_localization.py`：完整源锁、重建、读回和未选成员一致性校验。
* `tools/audit_dlc_localization.py`：按传入的本体、DLC与排版配置检查引用、字形和当前翻译状态。

在仓库根目录执行；原游戏与原DLC由使用者提供，LZX 库沿用 BUILDING.md 的本地依赖步骤：

```powershell
python -B -X utf8 -m tools.build_dlc_localization `
  --source-root 4E4D0811/00000002 `
  --profile locales/zh-Hans/dlc-packages.json --project-root . `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll `
  --output build/dlc-localized-new

python -B -X utf8 -m tools.audit_dlc_localization `
  --packages build/dlc-localized-new/packages/4E4D0811/00000002 `
  --project . --game dist/MC2-display-repair-disc1/candidate `
  --profile locales/zh-Hans/dlc-packages.json `
  --layout-profile locales/zh-Hans/gameplay-text-layout-v9.json `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll `
  --output build/dlc-audit-new.json
```

输出目录必须全新。源容器、SPA、导出、译文源、依赖摘要任一不符即停止。编译后的三份短剧资源采用已验证的非压缩 UE3 446/25 包，因此短剧容器变大；对象偏移仍与原逻辑字节空间一致。逆向应用23处字段后，与规范化原逻辑包逐字节一致；不将其说成压缩原包逐字节复原。另有原容器备份与容器/XDBF 的独立逆向夹具。

## XDBF / XSTR 格式（Verified）

两SPA采用 big-endian `XDBF` 版本 `0x10000`，目录项18字节：section(u16)、id(u64)、相对数据区偏移(u32)、长度(u32)。实际目录容量=使用数，payload紧密排列；自由表首项指向内容尾部、大小0，其余为零。未知稀疏/重叠/尾随形态拒绝。

section3 / id7 是韩语 XSTR 表。头含 magic、version、size、u16 count，后跟 u16 string ID、u16 UTF-8 字节数和文字。实际 size 为块长度减4；通用读写器也测试了 size 等于块长度的另一显式约定，保留输入约定。重建仅调整字符串块、受影响目录偏移/长度和自由表尾位置。所有非字符串条目的 payload 保持不变；每包的 XDBF 反向计划精确恢复原 SPA。

当前 Xenia 语言17在此表中不存在，仍走原 XSTC 默认语言7，所以修改原7号表而不是随意改默认语言。格式依据、作者、固定提交和文件摘要见 [XDBF研究锁](../references/dlc-format-research.lock.json)；与当前 Canary 对应的内容查找/语言槽证据另在STFS研究锁及本地 binding 报告。

## 增量部署与测试入口

已部署两个原文件名的修改后内容包到：

`xenia/content/0000000000000000/4E4D0811/00000002/`

当前直接用 `xenia/xenia_canary.exe` 打开既有 v6 ISO 时使用这一共享 content root。既有中文测试文件夹另有严格清单的 `dlc-content/`，`开始中文测试.cmd` 添加 `--content-bundle` 和固定清单 SHA256，每次只复制两份DLC进新建 run 的 content root，不复制或迁移档案/存档。`开始原文对照.cmd` 保持原行为。

`tools/content_bundle.py` 校验完整目录清单、文件大小/摘要和无链接；`launch_xenia.py` 在准备及真正启动前分别校验。源42位容器文件名是原样保留的不透明标识，不截成40位SHA1。后续 `refresh_oneclick_probe.py` 会保留已验证的 content_bundle 绑定，避免下一轮刷新把DLC参数丢掉。

`tools/install_dlc_bundle.py` 实际只新增5个文件、修改2个入口元数据文件，共7项；每项有写前状态、写后摘要和可逆日志。48个既有原DLC、配置、档案、存档与runs文件复核零变化。真实启动检查仅运行 prepare，不带 `--launch`。

## 验证与回滚

本地证据根：`build/phase-331-dlc/`。其中：

* `MODIFIED_FILE.json` 列出两包绝对路径与最终摘要。
* `DIFF_FILE.json` 记录容器/头字段与23个精确字幕字段差异。
* `VERIFICATION.txt` 记录命令、输入、原样输出、退出码、源测试和保留项检查。
* `ROLLBACK.sh` 调用带日志摘要保护的回滚工具；可传入两隔离目标目录。实际在仅含7项修改副本的夹具中运行，恢复测试入口及DLC安装前的缺省状态；真实已修改安装保持不变。默认无参数是回滚本轮真实DLC安装，不会回滚此前阶段330本体修复。

最终审计：BASELINE 的 strings/metadata/bindings/missing refs 为 **420/10/23/4**，退出1；MODIFIED 为 **0/0/0/0**，退出0；593处字幕布局检查、36个武器文本绑定和字形覆盖均通过。ROLLBACK 恢复7项，退出0。两次独立完整重建得到相同最终字节；另从Git暂存树导出干净源码，以LF规范化译表再构建，两包仍逐字节相同。

全库测试：基线2511项、修改后2596项、隔离源码回滚2511项，全部通过。基线/回滚各1项条件跳过，修改后另有1项Windows符号链接创建权限跳过，等价的链接/目录联接拒绝分支有mock测试。新增测试覆盖原42位包名、三层内容清单防护、源锁、XSTR逆向、STFS边界、字段佐证、重复/空值与部分写入失败回滚。

**尚待用户游戏内验收：** DLC实际枚举、短剧播放时序/缩放/换行观感、12种武器解锁装备、成就弹窗显示。当前结论是离线资源与模拟器输入准备验证，不是游戏流程已通关。原发布方签名字节保留但修改后不重新签名；这份候选面向现有Xenia测试环境，不声明原Xbox360签名验收。
