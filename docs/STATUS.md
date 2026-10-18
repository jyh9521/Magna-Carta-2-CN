# 当前状态（2026-10-18）

## 当前主线：真实文本已绑定，字体绑定仍待证明

- **最新执行约定：游戏测试全部由用户进行。** 后续自主推进限离线分析、工具、合成测试及候选准备；不自行启动 Xenia、发送输入或部署游戏资源。历史运行记录不构成继续游戏测试的授权。
- **2026-10-19 持续推进：** 继承原型链与 CDO 平面已分开审计，不把缺失字段当成 false；Core.Default__Component 尾部仍明示未解析。ForcedExport/namespace/GUID 与完整 glyph/remap/六张图集的标准化指纹证明三份 General_15 候选数据等价，但不选择运行时胜出者，见 FONT_BINDING_AUDIT.md。
- **范围扩展到双盘全包：** D1 1912、D2 2233 个 .xxx 共 4145 包逐件 SHA256 和完整包表验证，零包头/字体身份错误；每盘恰三处 General_15 命名空间候选，三文件跨盘 hash 相同。这是类表调查，不是所有 Font payload 或游戏显示验收。
- **双盘离线包已构建、未部署：** 三别名同时做原有字形959→65 geometry 标记，三份候选标准化指纹一致，六份独立反向文件均等于 raw 对照；D1/D2 各有 hash 锁定 TOC。通用构建器、版本计划和回归测试已加入，不覆盖原件、不启动游戏。
- **新完成：启动警告的静态完整字体链。** 组件前缀已按 class/outer/flags 解析为 4/8/16 字节三分支；62 包中 16279 个已选 UI 对象全部解析，1327 个分类缺口单列。TitleMap 两个 LogIn_NewGame 标签经 StringRenderComponent、AssignedStyleID、GeneralFont 六状态和嵌套 TextStyle 指向 Startup_int export21 General_15；12 条路径不等于运行时选中。见 UI_STYLE_GRAPH.md。
- **离线诊断已备妥，未部署：** GeneralFont 六处 StyleFont 的同尺寸 21→20 候选（General_15→Subtitle）、原样 raw 对照及独立反向副本 hash 恢复通过；两候选共用单字段 TOC 大小副本。原版/对照/候选静态图均保留两条文本绑定、12 条路径。109 个 UIStyle、614 条状态映射完成结构验证。
- 新增通用 `--consumers` 离线扫描：对既有日志所列 62 包验 hash 后只读分析，122876 exports 中 52541 成功解析 tagged 前缀、58210 明示跳过、12125 明示未解析；59 条直接字体引用中，新增覆盖 MC2Game 的 16 条自定义默认对象引用与 Engine 的 2 条默认引用。所有 62 包再次核验 hash 不变。详见 FONT_CONSUMERS.md。
- 下一离线切入点：继承样式自定义值与 linker/import 对象选择。组件与嵌套样式静态主链已补齐，实际绘制绑定仍未证明。

- 用户专用配置原始字节与图形设置保持不变；可选键盘测试偏差完整记录，见 XENIA_TESTING.md。
- 真实启动警告的 INT `GameStart/LogIn_NewGame` 已由可见 `TST` 标记验证，不再以待机视频代替交互证据。
- 原字体及 General_15 / EngineMedium_Subtitle 的外部、常驻补字候选均未显示两枚测试汉字；字体绑定与最小中文显示尚未通过。
- LZX 无修改重编码对照也会引起 guest fault；独立解码正确不足以证明游戏兼容。清除三处压缩状态的 raw 外层副本能加载警告，但不是发布方案。
- 五项曾部署资源已恢复原始 hash；F7 原版基线已取得同一警告的原文恢复画面。最新独立恢复画面仍待复测。详细矩阵见 RUNTIME_TEXT_BINDING.md。
- 新增同尺寸 Font remap 探针：只改既有映射的 uint16 glyph index，具备整包 hash/原映射/目标范围防护；静态反向恢复 byte-identical，245 项测试通过。真实 Editor 及外部/常驻 General_15、Subtitle remap 探针已捕获警告，均无预期字形变化。
- 新证据：Default__Engine 的 Tiny/Small 指向此前漏查的 MC2EditorResources 三套韩文字体（各 11534 字形，无 CJK remap）；另有 Xe 配置不同引用，实际优先级未验。见 FONT_REFERENCES.md。
- tagged/native 几何探针已实现且独立反向回退通过，253 项原生测试通过。本轮只取得候选标题/视频，自动短按未稳定进入警告，不记作字体阴性结论；四项部署已恢复。见 FONT_REFERENCES.md。
- 新发现：debug 文件请求跟踪中的 62 个现存 CookedXenon 包完成类表扫描；MC2Game.xxx 也嵌入 Font.General_15 和 12 个 font_ui.Font 对象。文件请求不是绘制绑定；此前探针没有覆盖这个 General_15 副本。新增 --inventory 类枚举工具可复现此遗漏，256 项测试通过。
- MC2Game 原样解压对照只捕获标题/视频，未取得警告，兼容性仍待验证；该包几何候选只做静态验证，未部署。MC2Game 与 TOC 已恢复原始 hash，专用 TOML 未变。下一步先取得这个 raw 对照的警告，再测其几何标记及恢复，不盲目补字或批量翻译。
- 字体枚举增加对象索引、outer 链与原始 linker flags；MC2Game 的 General_15 为 export34612，父包 Font 为45279，两者 export_flags=1；13 项记录在原版/raw 间一致。258 项测试通过。新一轮 raw、全原版 F7、全原版 Insert 短按对照均只取得标题/视频，没有警告；不能将输入失败归因于 raw 包。所有自建测试进程已关闭，资源与用户配置保持原版。

以下为历史累计记录；如与此节冲突，以本节及新的运行矩阵为准。

## 已完成

1. 审读现有 11 份 Markdown；原模板保留，当前事实单列，见 DOCUMENT_AUDIT.md。
2. 空远端对应目录初始化 main；本地规范、ISO、Xenia、完整原文及派生资源排除。
3. 两份系列 GLOSSARY 完整读取；固定 2 个 commit、9 个文件 SHA256；参考 2139 项、共有原词 9、字面译名冲突 0，见 SERIES_TERMS.md。
4. 本项目 terms.json 为唯一术语维护源，当前 0 项、继承 0 项；生成 GLOSSARY，避免把同名当同概念。
5. 两盘 XDVDFS 完整目录、全文件 SHA256、双盘差异；XEX2 title/media/disc 身份，见 RESOURCE_SURVEY.md / FILEMAP.md。
6. 独立 MIT Coalesced 提取器、通用记录校验器；8 个真实容器全部 byte-identical 内存往返；本地化物理行候选每盘 35901（不是可见剧情数）。
7. 76 个自制数据单元测试通过；真实缓存 fresh-fetch 9 文件通过；术语结构与 GLOSSARY 同步检查通过；compileall 通过。
8. .gitignore 修改副本/原始 hash/diff/回退脚本及独立副本恢复测试成功，证据保存在本地 build/verification/。该恢复测试不代表游戏汉化回退验收。

## 里程碑

|项目|状态|
|---|---|
|1 固定系列参考机制|完成；人工确认继承为 0|
|2 从当前原版提取实际文本|Coalesced 子集完成；全包/剧情覆盖未确认|
|3 无损提取与回写|容器内存无修改往返通过；磁盘回写及资源加载未实现|
|4 Xenia 中文与实际回退|未验证；没有中文部署或画面证据|
|5 字体/布局/术语游戏验收|未验证|
|6 全游戏汉化|未开始|

## 尚未解决

- 从文件名可知输入标为 Korea；其他发行版本、Title Update、DLC 不在已验证资源集合内。
- .xxx 只校验包头候选；包压缩、font 字符映射、glyph atlas/metrics、简中覆盖未解析。
- INT 实际含韩文；KOR/INT 的运行时优先级及本地化查找绑定未验证。
- Xbox360TOC 更新、重封装、存档兼容、换盘、完整游戏流程均未验证。
- 两上游字面无冲突不代表其世界观概念相同；别名/称号使用仍需语境复核。

## 下一轮唯一优先任务

沿已建立的静态链继续核对继承覆盖与 linker/import 选择，不将序列化路径升级为实际绘制绑定。游戏内同场景原样对照/字体引用候选/原版恢复由用户执行；此门槛前不开展批量剧情翻译或宣称补丁可用。

提交、推送、Actions 结果以本次交付报告与 GitHub 实际运行记录为准；此文档不预先宣称远端 CI 成功。

## 双盘合一补充需求（2026-10-18）

已纳入正式长期路线，见 [技术调查](MULTIDISC_RESEARCH.md)。保持既有初始化与术语锁；不暂停汉化主线。

- Verified：本地双盘齐全；复用旧研究并重新核验目录与完整 ISO SHA256。新版比较工具复现 1631 相同 / 3 冲突 / 382 D1 独有 / 706 D2 独有，保留逐文件 hash。
- Verified：配置 DiscNumber 不同；TOC 路径/大小/扇区关联，详见研究文档；这些字段运行作用仍待验证。
- 合盘进度：只读调查完成，具备继续研究条件；A 自动换盘、B 单入口双盘、C 真合一均未获游戏内验收。
- 本轮未合并 ISO、修改 XEX、删除重复资源或执行重封装。换盘、章节、存读档与语音/视频/战斗/地图全部待验证。
- 现有“下一轮唯一优先任务”不变；合盘下一调查是取得原版换盘基线，不作为汉化前置条件。

本轮新增 10 项比较工具合成测试，总计 86 项通过；原有 76 项作为修改前基线通过，系列来源/生成术语表回归通过。README 路线字段已在独立副本恢复到修改前 hash，非游戏回退验收。完整命令输出保存在本地 build/multidisc-verification/。

## 字体与最小实验推进（2026-10-18）

- 138 项合成测试通过：新增包表 28、字体 15、回写 9；此前 86 项保留。
- 五个真实包 summary 验证，四个未压缩包表解析；Startup_int 压缩表仍需 LZX，未冒充完整解析。
- 26 个真实 Font 对象 tagged/native 数据一致；两个主要韩文显式映射没有 U+4E00–9FFF 字形。30 条原版 atlas bounds 异常保留，不为通过检查而修改。
- 实现 SHA256/原文/稳定 ID 防护的 Coalesced 副本回写，9 项测试通过，真实等长 ASCII 与中文干运行再提取通过；修改后游戏生效尚待验证。
- 当前 Canary @50e9c715d 已实际进入原版标题与村庄；原版画面、独立 storage/content/cache 与日志留本地。Esc 仅退出游戏，不暂停开发。
- D1 独立提取 2016 文件逐一 hash 一致，无 ISO 修改。下一步按 COALESCED_REBUILD.md 验证同场景 ASCII 绑定与回退，再补字验中文；不等待合盘。

## 两字补字原型与保留性检查（2026-10-18）

- 上一批源码40086fb已推送，138项测试及CI通过。
- 固定可选libmspack native解码器已编译并验hash；Startup从summary-only推进至包表/逻辑区可读。41个直接StyleFont静态引用可解析，未冒充具体提示运行绑定。
- 35个字体Texture2D对象完成结构调查；10个独立font纹理经过LZX解压与Xbox BC3反平铺，预览可辨识。原版raw resident与独立compressed atlas一致。
- Noto Sans CJK SC来源/版本/许可证已锁定；两字计划在locales/zh-Hans/font-supplement.json。仅加入“踢、击”，非正式翻译或完整中文字库。
- General_15保留原2608个字形，追加至2610；tagged/native/remap原记录保留；最大高度23不变；仅72个原空闲BC3块改变，其他像素/块/填充一致。
- 独立font.xxx及Startup_int.xxx副本已append/repoint构建并完整再解析。Startup保留4372个其他export、13个旧压缩chunk及原尾部；没有修改XEX或ISO。
- TOC候选只改上述两包首大小字段，保留路径/扇区/其他列/CRLF；字体、Startup、Coalesced和TOC四份中文候选均留本地，尚未部署中文。
- 基线138项通过，当前215项native-enabled测试通过；默认CI不依赖DLL/原版资源，可选native测试跳过1项。字体副本2608→2610→2608与hash回退通过，不是游戏内回退。
- ASCII隔离尝试已恢复原容器；没有KCK可见证据，不标为绑定成功。当前游戏内中文仍为待验证；下一步唯一优先：受控同场景确认文本绑定，随后部署中文候选并取得修改/回退画面，不做全量翻译。
