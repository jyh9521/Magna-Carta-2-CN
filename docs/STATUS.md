# 当前状态（2026-10-18）

## 当前主线：真实文本已绑定，字体绑定仍待证明

- 用户专用配置原始字节与图形设置保持不变；可选键盘测试偏差完整记录，见 XENIA_TESTING.md。
- 真实启动警告的 INT `GameStart/LogIn_NewGame` 已由可见 `TST` 标记验证，不再以待机视频代替交互证据。
- 原字体及 General_15 / EngineMedium_Subtitle 的外部、常驻补字候选均未显示两枚测试汉字；字体绑定与最小中文显示尚未通过。
- LZX 无修改重编码对照也会引起 guest fault；独立解码正确不足以证明游戏兼容。清除三处压缩状态的 raw 外层副本能加载警告，但不是发布方案。
- 五项曾部署资源已恢复原始 hash；F7 原版基线已取得同一警告的原文恢复画面。最新恢复运行再复核中。详细矩阵见 RUNTIME_TEXT_BINDING.md。
- 新增同尺寸 Font remap 探针：只改既有映射的 uint16 glyph index，具备整包 hash/原映射/目标范围防护；静态反向恢复 byte-identical，245 项测试通过。真实 Editor 及外部/常驻 General_15、Subtitle remap 探针已捕获警告，均无预期字形变化。
- 新证据：Default__Engine 的 Tiny/Small 指向此前漏查的 MC2EditorResources 三套韩文字体（各 11534 字形，无 CJK remap）；另有 Xe 配置不同引用，实际优先级未验。见 FONT_REFERENCES.md。
- 下一步对同一可见字形同时做 tagged/native 几何 sentinel，区分 remap 消费方式与字体选择；如仍无变化再追踪渲染路径。不盲目补字、不开始批量翻译。

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

追踪启动提示 `MC2UI_TCR.int [GameStart] LogIn_NewGame` 在原版 Xenia 中的真实读取与字体绑定，取得原版同场景基线；在完成此证据前不开展批量剧情翻译或宣称补丁可用。

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
