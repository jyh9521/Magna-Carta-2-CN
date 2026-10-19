# 当前状态（2026-10-18）

## 当前主线：单场景中文显示已确认，强制折行测宽候选待复测

- **2026-10-19 长句布局修复候选：** 用户扩展截图显示窄标题弹窗前两行左溢、末行居中；
  静态发现强制分段遗漏 origin 扣除，16字节运行时跳板修复的216组回放及120组受控布局检查通过。
  样本文字/字库/框体不变，新入口及同中文资源无修复 A/B 入口见 WRAP_WIDTH_FIX.md。
  用户说明剧情对话框比标题弹窗宽；剧情与修复后实际像素仍分别等待用户验收。

- **2026-10-19 简化玩家入口：** 新增完整独立游戏副本准备器；两份副本分别内置中文候选/原文解压对照，提供用户双击 CMD 与可拖入 Xenia 的 default.xex。先逐件核验再发布启动文件，不使用硬链接；准备阶段不启动游戏、不修改原件或用户配置。用户不再需要手工覆盖六份资源。

- **2026-10-19 手测入口核对：** 给现有六资源候选加入独立、只读、标准库阶段核对器。固定 packet manifest hash 后检查原版/raw-control/candidate，列出缺件/混用与错误光盘 TOC；不启动、安装或改写测试目录。候选资源字节保持上一提交不变；匹配结果仍不等于中文显示或游戏行为验收。

- **2026-10-19 转向实际中文候选：** 新单包实验同时覆盖三份 General_15 与此前未补字的两份 SmallFont；Startup_int 两个字体顺序合成后重新验证，不互相覆盖。SmallFont 仅显式 identity-256 模式转为映射字体并补两字；新警告为同长度 ASCII/中文诊断面板。双盘各六资源、带独立 raw-control 和原件恢复副本，未部署、未游戏测试。辅助函数草稿暂存，不再作为当前主线；见 WARNING_FONT_ROUTE_PROBE.md。

- **2026-10-19 Font序列化链：** UFont/UMultiFont操作数注册链、独立callback/table窗口及slot34的六个完整函数模板通过；17/20字节glyph、4/8字节map与6C先于68的传输顺序已静态核实。UFont前方非NUL指针数据导致旧扫描漏检，新增精确操作数锚而不放宽旧profile。外部archive/helper语义、寄存器保持与实际字体仍未证明；见 FONT_SERIALIZATION.md。

- **2026-10-19 Font声明补齐：** Array/Map声明通用读取与独立Class/property审计已加入，五个Font属性解析通过、FontCharacter五成员及Texture2D inner已绑定；CharRemap null/null仍显式opaque。Next到同owner ScriptStruct边界单列，不假装UClass.Children或native布局已还原。新增15项回归，默认658项通过；见 FONT_DECLARATIONS.md。

- **2026-10-19 字符度量分支：** TextSize绑定已连至47-word helper和122-word无call窗口，核实mode-word+68的direct-index/键值链分支及7F替代路径；native glyph stride20与磁盘17字节分开。新增15项静态回归，未将磁盘IsRemapped直接当native状态或升级实际覆盖证明。下一离线处理Font Array/Map声明与序列化桥；见 TEXT_MEASUREMENT_PATH.md。

- **2026-10-19 测量入口静态绑定：** 新native-only完整header盘点与独立initialized row8读取器核实Font2/MultiFont1/Canvas10共13项；Canvas12个非native脚本只记省略、不执行或强行解析。原6套cold相关计划不变，464/470等native token保留；下一步沿StrLen/TextSize及Font wrapper追helper，不推断SmallFont直接索引。见 INITIALIZED_NATIVE_TABLES.md。

- **2026-10-19 reference helper：** 判定函数调用的0x826c5ec0完整90-word模板及三条name/class注册参数链已核实；静态关联DefaultTextStyle/ImageStyle/ComboStyle和三种UIStyle类，记录+3C parent循环而不假称实际终止。双盘一致，新增15项回归；外部lookup/name构造、字段native映射和实际fallback仍待证明。见 STYLE_REFERENCE_HELPER.md。
- **同轮补齐实际覆盖入口：** 修正coverage auditor只认imported Engine.Font而拒绝Engine本地Font Class的假设；本地类型必须精确解析到Font Class，新增3项身份防护测试。两份SmallFont均为256 glyph/IsRemapped=false，警告39个literal只记为non-remapped-font-mode-unverified（exit1），不猜直接索引或缺字。默认602项测试通过。

- **2026-10-19 selection predicate：** 四个已核实组件表的slot124均指向同一36-word函数；+104、+F4..100和helper返回两word参与条件选择，不是恒定owner路线。双盘报告一致，新增11项合成回归；运行vptr/字段值/实际分支仍未证明。下一离线追踪0x826c5ec0的name/class fallback及PrimaryStyle声明对应；见 STYLE_SELECTION_PREDICATE.md。

- **2026-10-19 新增标签默认平面审计：** 两个警告标签自身无 PrimaryStyle，但独立 CDO 链保留 DefaultComboStyle；六状态嵌套 TextStyle 各自的 CDO 引用 EngineFonts.SmallFont，两份命名空间候选完整语义指纹相等。新增12条默认平面观察与原12条 General_15 组件路径分开，未合并默认值、未证明 native alternate-owner 分支或运行字体。16项自制测试加入，默认573项通过；见 OWNER_PRIMARY_STYLE.md。

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


## Core 祖先与嵌套标量补充（2026-10-19）

- 原版 Core.xxx hash 验证后，renderer CDO 尾链闭合为 Engine15602→15479→6065→Core4→Core2→null；修正有 Core 时仍将 Component 当根类而误报不兼容的问题。缺失 Core 时保留原有边界，坏定义继续报错。
- 嵌套 Int/Byte 字段增加精确值与编码；两处警告 renderer 的 TextAlignment[0]/[1] 均为 u8=1，bOverrideAlignment=1；数值不冒充枚举意义。
- 两条 prototype 链与十二条字体候选路径不变；完整已检查 CDO/prototype 没有显式 DrawFont 覆盖。原生初始化、实际继承值、加载选择和中文显示仍未验证。
- 基线319、修改327（native327）、独立源码回退319；仍无游戏启动、部署或配置修改。七项非 UI 分类错误保留在报告中，不伪装全包完整反序列化。


## 最小补字候选覆盖补齐（2026-10-19）

- 补齐 MC2Game 原容器的两字 append-only 候选，与既有 font/Startup 三份独立解码后均为2610字形/remap，完整语义指纹一致。MC2Game保留83390个其他export、52个旧压缩chunk和3241尾字节；原文件hash复核未变。
- 双盘各生成仅三字体大小变更的独立TOC候选，反向大小回写逐字节复现各盘原TOC。未改文本、未部署；该候选区别于三别名geometry诊断及早期两字体+Coalesced组合。
- 下一离线项是通用多别名补字装配/验证入口；只保留两字技术原型，不提前批量剧情翻译。游戏实测仍全部由用户进行。


## 多别名可复现装配入口（2026-10-19）

- 新增通用 tools/build_font_supplement.py，locale下分别保存双盘版本计划；提取共享namespace/版本防护到 font_binding_plan.py，原geometry CLI保持兼容。源包、glyph计划、源字体、原/新完整字体指纹及TOC均受校验，raster只生成一次。
- 双盘完整装配重现三份既有候选hash；六份独立候选副本通过hash保护的原始物理字节备份恢复；双TOC反向大小回写逐字节一致。非从新压缩容器无备份重构原件，不代表游戏回退。
- 基线327、修改337、native337、独立源码回退327；新增10项合成回归，无游戏/原字体/DLL依赖。所有原件、配置、部署状态不变。
- 后续离线工作：最小文本候选的字符→字体remap覆盖、源字符串/保护标记一致性和可复现装配；仍仅技术原型，不提前批量剧情翻译。用户负责全部游戏验证。


## 源值锁定文本与字面字体覆盖（2026-10-19）

- 新增通用 audit_text_font_coverage.py：源 hash/ID/保护标记/编码/再提取与全容器逆向一致性通过后，检查所有显式 Font 的字面 Unicode→remap/指标；输出按条目/字体的缺口，不选运行字体、不验证像素或动态展开。
- build_coalesced.py 保留 literal 接口，新增显式 sha256-utf8 源值模式并拒绝 True/浮点 schema、未知模式、混合字段；locales/zh-Hans/text-probe.json仅存源值 hash、ID与既有两字技术探针，不需要未跟踪原文计划。
- 双盘从各自原件复现相同1495972字节候选（仅6字节变化），各自落盘逆向副本完整 hash/字节等于原件。原三字体均缺两字；候选双盘全三字体字面覆盖通过；额外缺字负对照全三字体均正确失败。Kick记录不冒充LogIn警告控件绑定。
- 基线337、修改355、native355、独立源码回退337；新增18项合成回归，无游戏、字体raster依赖或DLL要求。源资源、配置和部署状态保持不变。
- 后续离线项：最小候选的字体/文本/TOC组成与依赖一致性清单及隔离装配，继续区分候选准备和用户游戏验收；不批量剧情翻译。


## 五资源依赖校验与隔离候选装配（2026-10-19）

- 新增 build_locale_candidate.py 与 locale 下双盘 candidate 计划；共用 read_locked_json 读取精确hash/范围内JSON。校验所有原/新Font身份与完整指纹、候选二进制hash、文本源/标记/逆向/字面覆盖及TOC原大小/输出hash，不信任上游manifest成功标记或缺省源列表。
- 双盘各构建3字体+文本+TOC的原路径候选、物理原始对照和独立备份恢复；10份资源恢复原始完整hash/字节。D1换输出目录重复装配18文件全hash相同（含报告/manifest），元数据路径均相对。
- 实际错盘TOC与损坏候选+伪成功manifest均在输出目录创建前失败；可变长文本TOC更新由合成样本证明。本轮未追加任何glyph或翻译行，未启动、部署或修改配置。
- 基线355、修改367、native367、独立源码回退355；新增12项合成回归。外部raster源字体本轮未重读，manifest明确只记录其期望hash；真实候选包以完整字节hash和语义指纹另行验证。
- 后续离线项：搬移/复制后的候选树按可信计划进行独立复核，再整理用户手测候选入口；所有游戏操作仍由用户负责，静态通过不算中文显示验收。


## 搬移候选独立复核（2026-10-19）

- 新增 verify_locale_candidate.py，基于可信计划而非生成器声明读取闭合候选树，重解析原/新Font、重放文本与TOC及逆向恢复，严格比较typed metadata；不调用装配构建器，也无需原游戏根目录、原bundle或raster源文件。
- 双盘移动副本每盘5资源/18成员通过原manifest可信hash锚定与独立复核，36份文件hash前后不变；五类真实负对照（伪hash资源、伪报告及配套hash、多余成员、错盘TOC、后代junction）均以exit2失败且无新成功报告。
- 未传manifest锚定时仅证明可信计划下的资源/重放契约，不宣称原producer metadata字节身份；历史额外输入声明和外部raster文件均保持未重开/未验证标记。当前verifier实际输入另行snapshot复核，不混淆两种证明。
- 基线367、修改381、native381、独立源码回退367；新增14项合成回归，含False/0与1/1.0类型、晚期篡改和路径读回复核。原游戏/配置/部署状态不变。
- 后续回到UI原生默认值、有效覆盖与linker字体选择的静态缺口调查；候选装配和完整性不能替代该证据。所有游戏验证继续由用户执行，最小中文验收前不批量剧情翻译。


## UI持久结构默认值与作用域绑定（2026-10-19）

- 新增ue3_struct_defaults/inspect_struct_defaults读取器；深度UI审计可选--audit-struct-defaults，经Class15601→property15535/15534→ScriptStruct5371/5255绑定，不按叶名称猜结构。
- 6个定义全解析，两个renderer各两字段绑定成功。持久定义显式bOverrideDrawFont=0、DrawFont=null；STYLE_ID无自有默认值，继承Core.Object.Guid的声明及单列父默认记录，不将缺项当0。原生构造/动态覆盖和有效绘制仍未证明。
- TextAlignment两实例两轴均为存储槽1，其枚举名UIALIGN_Center；数组轴槽对应Horizontal/Vertical。Bool值原在tag-header而非size0的payload，旧flat偏移晚4字节，已修正并读原逻辑字复核。对象StyleFont探针偏移不变。
- 图仍1209个已解析UI、2匹配/12字体路径；7个非UI分类缺口保留。源码基线381、修改397、native397、独立源码回退381；新增16项纯合成回归。原包hash、配置和部署状态不变，无游戏操作。
- 后续静态调查已定位SetFont15555、DisableCustomFont15563、GetAppliedStringStyle15568、GetFinalStringStyle15571等Function出口；下一步验证声明/可读脚本或native边界，不凭名称断言行为，不调用游戏函数或提前批量翻译。


## UI函数声明与native边界（2026-10-19）

- 新增ue3_function_metadata/inspect_function_metadata，只读验证UField/UStruct/UFunction头、保留的非零Line/TextPos及FriendlyName、参数/返回声明和精确NativeParm桩；复用有界完整property_chain，不盲跳未知脚本。
- Engine Class15601 UIComp_DrawString的23个直属Function全部列入审计：18个native参数桩完整解析（含SetFont/DisableCustomFont及两个style getter），5个非native方法逐项保留为未解析，class模式exit1而非伪成功。18个NativeToken均0，不等于native实现已定位。
- 已确认SetFont参数为Engine.Font，GetAppliedStringStyle返回UIStyle_Combo、可选UIState；GetFinalStringStyle接收out UICombinedStyleData并返回Bool。这些是声明而非调用/行为证据，实际覆盖启闭和有效字体仍未证明。
- 基线397、修改415、native415、隔离源码回退397；新增18个纯合成测试，覆盖真实自编包CLI、逐字节截断/桩变异、参数顺序/归属、flags、头尾和部分失败；原游戏包/配置hash不变，无启动/部署。
- 后续沿5个脚本wrapper及可执行文件native注册/实现静态边界继续调查；不重跑已被拒绝的.xxx通用REA格式，不调用游戏函数，不把静态结果当中文验收。


## UI布局脚本与控制路径（2026-10-19）

- --include-scripted显式启用有界UE3 wrapper语法；保留默认native-only模式18/5与exit1，新的Engine+Core全类审计23/23、0未解析、exit0。5个脚本736字节/242 token全部消耗；不执行字节码。
- 已验证WrapMode/ClipAlignment写入、按Orientation索引的AutoSizeParameters.bAutoSizeEnabled、继承AutoSizePadding的Value/ScaleType两端写入，及bReapplyFormatting条件分支通往Outer上下文的RequestSceneUpdate(false,true,省略,省略)调用点。callee声明第二参数为bPositionsChanged；实际native效果仍未验证。
- Core.Object239个直属Function头内按唯一NativeToken绑定4个操作符声明，不按数字表猜语义；别名仅在operator flag下放行。local/Class/继承Struct引用、类型/enum、call参数、Skip/default跨度与前向语句目标均校验。Context skip含义与动态Orientation范围明确未验证。
- 新增23项纯自编包/脚本合成回归，基线415、修改438、native438、独立源码回退415；原游戏包与配置hash保持，无启动/部署/批量剧情翻译。见 docs/SCRIPTED_UI_LAYOUT.md。
- 下一步转向可执行文件native注册/实现及文本测量路径；SetFont等18个native方法的实际字体选择、原生构造、中文像素验收仍未完成，游戏测试继续由用户负责。


## 双盘原生映像可复现还原（2026-10-19）

- 新增xex_image/extract_xex_image：预检原hash/profile与边界后显式选择AES backend，完整CBC存储流解密后插零；逆向去零/重加密与原头组成全字节原XEX副本。none/basic之外的变体拒绝，不改签名/入口/原文件，不执行。
- 双盘原XEX完整hash不同，Media ID/盘号保留各自身份；D2新提取文件匹配旧独立全文件清单。PyCryptodome3.23.0及cryptography46.0.3各自还原两盘，4份20119552字节映像全相同，SHA=d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9；各盘物理逆向副本复读与原件一致，不因此交换完整XEX。
- PE32/PPCBE头及代码页范围已核实；PE原始指针/SizeOfImage不用于重映射，RSA和存储页digest语义保持未验证。REA两个目标均被格式/架构边界拒绝，无native session；有限Capstone查看不冒充完整反编译或游戏验证。
- 已找到4个intUUIComp_DrawStringexec...完整宽字符串及各1个数据指针，仍只是注册线索，不是SetFont等native入口地址。下一步追踪数据表/初始化及执行函数边界、字体覆盖/测量逻辑。
- 新增22项纯合成结构/CLI/cipher-contract与Git签名检测回归，基线438、修改460、native460、独立源码回退438。核心CI无需加密依赖；真实AES双实现证据另列。所有原包/配置hash保持，无启动、部署或批量剧情翻译。见 docs/NATIVE_IMAGE.md。


## 原生方法静态关联与字体word指令链（2026-10-19）

- 新增ppc_native_bindings/inspect_native_bindings和hash锁定profile；18个完整intU...名称、typed Engine声明、cold row12表及sentinel全部对应。116条直线初始化指令按常量/符号栈字节恢复18描述符及零sentinel；不执行指令或改写映像。
- 32-word查找模板核实stride12、比较helper返回0时取row+4；比较/保存恢复helper语义及初始化实际到达仍未验证。双盘映像报告逐字节一致。SetFont静态code word=823fdb68，DisableCustomFont=823fdf28，GetAppliedStringStyle=826a8ff8，GetFinalStringStyle=823fe0d8。
- 配对指令链核实word+0xe4的设置mask20000000及清除keep-maskdfffffff、setter从stack+0x50写word+0xd8、addend0xc4。按作用域SetFont.NewFont参数与配对方法高置信推断为DrawFont/覆盖位；不是完整native struct、参数producer、构造值或活动Font证明。
- Engine包本工具不重读，使用已重新生成并逐字节复核的精确native-report hash锚定；不把success bool当证据。新20项纯合成回归，基线460、修改480、native480、独立源码回退460；涵盖逐字节模板/字段变异、1024 mask、符号栈/型别/边界/复读。
- 后续继续原生构造/默认值、getter和条件helper的字体选择/测量路径；原游戏/配置不变、无启动部署、不批量剧情翻译。见 docs/NATIVE_BINDINGS.md。


## Getter双条件覆盖与声明函数范围（2026-10-19）

- 原native plan保持不变，新增显式style_selection计划；四个窗口共96条指令逐字结构核验，双盘报告全字节一致。GetFinal wrapper直调0x826a90c0；该helper和GetApplied尾链均读virtual slot+0x128，具体vtable目标和producer/copy语义仍未证明。
- overlay0x826a92c0核实flag+0xe4的20000000位和pointer+0xd8都非零才写output+0x20；任一为零均绕过，其他store与+0x20不重叠。bit置1本身不代表字体已被替换。字段名称仍为配对作用域方法支持的高置信推断，不把对象相对位置当序列化offset。
- 新增通用CE/PPC .pdata读取器；44484条记录全检边界/长度/排序/不重叠，保留全部四种flag组合。18个native入口均有确切声明记录；initializer选段恰好从prologue-end至declared-end；overlay leaf无覆盖条目，不按下一个start推算边界。
- 既有struct读取器另解析UICombinedStyleData5390及9声明，DrawFont5387指向Engine.Font且持久默认null；不因此推算native layout/当前输出。新15项纯合成回归，基线480、修改495、native495、隔离源码回退480，默认CI不需要游戏/crypto/Capstone。
- 原件、配置和部署状态保持；无启动或游戏函数执行，不批量剧情翻译。后续沿base-style producer、virtual目标、条件refresh和原生构造/测量继续离线调查。游戏验收全部由用户进行，见 docs/NATIVE_STYLE_SELECTION.md。


## 类名前缀、leaf callback与静态样式table（2026-10-19）

- 新class_tables显式计划核验4个完整U类名与name+2参数链；DrawString/Editbox/Slider/Caption分别关联3个84字节leaf callback与3个只读table窗口。Slider/Caption共享callback但保留独立名称。Engine另独立复核4个Class及其本地继承关系，不把字符串匹配当原生ABI证明。
- 81-word窗口的slot128均指向0x826a8f00；61条getter指令验证slot124结果非零时选entry+E8、为零时选entry+28所读指针+174，后续使用所选base+1C的pointer。外部helper、slot124目标、完整native field语义和活动dispatch仍未证明。
- 初始指针搜索的第四匹配实际位于.pdata，现按PE虚拟.rdata类型/flags与不重叠边界拒绝；不按裸地址匹配猜table。较早的3个有cleanup调用的table-write候选未被冒充default constructor，真正选中的call-free leaf没有D8/E4写入，不据此假定字体指针/flag为0。
- 新20项纯合成回归；基线495、修改515、native515、独立源码回退495。双盘报告逐字节一致，原native/style计划输出仍逐字节兼容；无需游戏/crypto/Capstone的默认CI持续验证。
- 原游戏/配置/部署状态不变，无游戏或原生目标函数执行，不批量剧情翻译。下一离线项继续callback存储/调用、分配与属性初始化阶段、slot124及base-style producer；有效Font和中文显示仍待用户游戏验收。见 docs/NATIVE_CLASS_TABLES.md。


## 原生probe的Git/LF字节契约修复（2026-10-19）

- 发现新style/class计划在Windows工作区仍为CRLF，而Git已按.gitattributes存为LF；旧文档锁的是本地CRLF hash，clean checkout会失败。未放宽输入hash校验，改为发布源码LF字节的正确hash，工作区6份JSON纯换行差异统一回现有Git blob，内容语义不变。
- 新增2项仓库字节契约测试；先在旧CRLF输入复现失败，再验证源码LF与文档hash一致。合计517项、native517、combined隔离回退495；新archive不再用工作区JSON覆盖来掩盖clean-checkout问题，真实CLI也直接读取Git归档计划复核双盘。
- 同一历史CRLF计划输入的报告仍逐字节兼容；改用发布LF计划时只允许报告的plan_sha256身份字段改变，其余字节须完全相同。游戏原件、语义计划数据和配置保持不变。


## Metadata callback链与中间clear阶段（2026-10-19）

- 新object_initialization opt-in计划验证20/21-word save/restore、57-word base与77-word metadata constructor、size getter及选定wrapper/allocator窗口；metadata参数r4写+50、r9经r28写+11C。metadata table的slot120指向读取+50的8字节getter，未将其误当UI component的方法表。
- selected callback site0x823b9b18从原Class或fallback helper返回指针+11C取地址，传allocation返回值r30；allocation结果0会跳过该调用点。Class空指针处理、fallback语义和较大callee的寄存器保持不冒充已证实。
- 40-word fill helper经精确模板与纯整数分区验证zero调用的prefix/16-byte/4-byte/tail覆盖；不是运行/模拟PPC。组件clear site之后还存在property/default相关候选调用，所以只证明满足前置条件时的中间clear契约，不证明callback入口或绘制时字体为0。另一个相同helper调用清的是stack buffer。
- 新20项合成/算术回归，基线517、修改537、native537、独立源码回退517；全部4个probe的LF/文档hash测试现精确匹配CLI参数，而不是文档任意位置出现hash。双盘报告相同，旧3个计划精确输入报告保持字节兼容；原件/配置不变，无游戏/原生目标执行或部署。
- 后续沿clear之后的默认值/属性阶段及base-style/measurement路径继续；字体生效和中文显示仍由用户游戏验收。见 docs/OBJECT_INITIALIZATION.md。


## 活动候选纠正到已调查的启动警告（2026-10-19）

- 对照真实目录与UI图发现：旧text-probe.json确实是MC2UI.int/[ButtonA]/Kick，不是两处警告的MC2UI_TCR.int/[GameStart]/LogIn_NewGame。旧资源/覆盖证明保留但不重命名为警告证明；优先修正可供用户验证的实验范围，而不是继续在错误文本候选上堆引擎分析。
- 新通用sha256-utf8-prefix模式检查完整source hash、可选精确selector、Unicode前缀边界和显式UTF16长度flag，保留源suffix/控制码；不提交完整警告原文。builder/auditor拒绝重复/非有限JSON，builder增加输入前后复核与输出字节重开/有限清理。
- 双盘活动candidate计划改指text-probe-login.json；警告首3个BMP字符替换为既有踢击!，66 units不变，仅6字节/1条记录改变，63字符suffix及3个literal换行token保留，输出349968ee...与历史警告marker资源字节一致。Kick与其他18175条记录保持原值，不是新游戏显示结果。
- 新鲜只读图仍1209 UI/2匹配/12状态字体路径；全39个结果literal在3份补字Font均覆盖，未添加任何新glyph或剧情行。双盘5资源装配和独立复核、10份原始备份恢复成立；旧Kick包必须被新可信计划拒绝。
- 新20项合成回归，基线537、修改557、native557、隔离源码回退537；仍不启动/部署、不改用户配置。原生property/default core0x823b0f98的156-word/copy/fill线索已保留但语义未冒充完成；后续继续与字体/measurement调查结合，所有游戏验收由用户进行。见 docs/LOGIN_PROBE.md。
