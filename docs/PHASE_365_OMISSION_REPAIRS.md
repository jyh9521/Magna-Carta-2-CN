# 阶段365：29项遗漏的成套修复

## 范围与计数

本轮逐项接续不可变的 `omission-findings-v34.json`，不改写上一轮筛查结果。
结构化结案表为 `locales/zh-Hans/omission-repairs-v35.json`；每项绑定原始身份、
源计划SHA、译文及实际成品载体SHA，状态为 **repaired-offline**，不是游戏／用户验收。

| 家族 | 独立内容 | 物理范围 | 修复 |
|---|---:|---:|---|
| WorldMap目的地电影 | 11 | 双盘16成员 | 全部360帧的旧字支持域修复、原生字号／锚点中文 |
| 换碟提示电影 | 2 | 双盘4成员 | 第1／2张光盘提示，保留白字／黄色盘号及原边框 |
| 正常流派树属性标签 | 8 | 双盘32个normal别名 | 中文属性及HP的“提升”，保留原生透明轮廓 |
| 任务通知Quest前缀 | 8 | 两盘共用一份主INT | 只将前5码点Quest改为任务，后缀及控制符不变 |
| 合计 | **29** | **26个资源成员＋两份TOC** | **28条发布资源身份变化** |

另同步独立包的2个 `STR_normalcopy` 别名。其原字是日文“攻撃”，不是韩文；
单独恢复红色底图并改为“攻击”，不计成第9个正常属性或第30项遗漏。
8个空白／选择背景不改，13个既有字体导出及83,405个未选导出保持。

地图译名依次为风息岛、阿巴泽特、老狐峡谷、柯塔马雷、海底洞窟、杜南丘陵、
杜南平原、鲁哈尔特、贝尔福特、哨兵研究所、拉·斯特拉达。
普通目的地**不是**用户所报剧情后的独立大章节卡。

## 图片／动画不是涂抹后盖字

### WorldMap：先独立验收清底，再画中文

每片分别测量原生字芯高度、位置和色阶；采用NotoSerifCJKsc-SemiBold的自然字进，
不把中文横向拉满旧字宽度。除风息岛经过单独查看采用32px对33px源字芯的1px光学校正外，
其余十片的源／中文字芯高度与X/Y锚点差为0。原字体身份没有恢复。

旧文字、暗描边及色光的完整支持域使用稀疏逐帧时序背景重建；原生罗盘／扇形装饰不重画。
3960张源清底与3960张最终Bink原生帧分别经过有界检查，不能只检查中文覆盖后的中帧。
原字遮住的地形属于推断的背景延续，**不是恢复未知原画**。编码前未授权RGB逐字节保持；
重新有损编码后的域外量化误差与此严格保证分开记录。

交叉复核实际退回了四个候选：老狐14个橙色下沿像素、杜南14个暗橙像素、
鲁哈尔特7个很暗且随背景变化的红色像素，以及老狐首次改版仍漏的 `(269,377)` 单像素字缘。
固定亮度／稳定度阈值、6px字芯外扩均不是完整去字证明；改用实际完整字身及暗缘后重新做模型、
清底、编码和原生回读。最终老狐R2在360帧×7077个授权像素中，
全部 **2,547,720** 个RGB像素独立匹配选定的无中文清底，再与最终实际Bink对照。
失败结果保留但不进入当前目录选定的生产计划或安装器。

### 换碟：双侧原生行供体，不用平滑底条

两片各30帧，1280×720，无音轨。分别核验旧字两侧55px宽的干净区域：
每一原生行在左右供体内RGB均恒定，左右也完全相同，最大差为0。
`row_background.restore_rows` 只运输显式6235／6116个旧字及阴影像素；
不平均、不插值、不接触边框或装饰。隐藏渐变的连续性仍标为推断。

“请放入《真名法典2》”为原生白色，第1／2张光盘为原生黄色。
通用视频前景增加互斥的 `parts` 分支，复用既有有界文字段渲染器；先修复背景一次，
再合成两段前景，不用第二段擦除第一段。

### 属性：可重放的原生像素运输，保留原BC3 alpha

`native_pixel_transport.transport_rgba` 对每个修复像素声明干净原生供体坐标，
镜像／重复列／直接复制均显式记录；禁止读取同源旧字支持域，禁止写未授权像素。
单独审查无字底、圆角／边缘和实际BC3编码回读，不拿禁用或选择态替代正常态。

`texture_overlay` 的显式 `alpha_encoding=preserve-source` 要求合成前后alpha完全相同，
然后保存每个原BC3块的8个alpha字节，最终再检验全部压缩alpha和解码alpha。
默认及已有adaptive-range路径不改。编码前域外RGBA与编码后授权4×4块外RGBA严格相同；
授权块内仍有RGB量化影响（本轮SRV最大单通道差66），没有声称块内未绘字像素全部无损。
34别名已逐项回读，原资源及独立回滚后的17个原生标签再次核对。

## 文本保护与重扫

`quest-prefix-fix-v35.json` 逐字段稳定ID及前值SHA守卫，仅改8项前缀；
18176字段的其余内容和 `%s` 等控制符不变。新增“任务”已在现有字符集，新增字形为0，
不重建字体。源INT→修改INT→独立回滚副本的结果：

```text
BASELINE: QUEST_PREFIX_GAPS=8 FIELDS=18176 EXIT=0
MODIFIED: QUEST_PREFIX_GAPS=0 CHANGED_FIELDS=8 TOKENS=UNCHANGED EXIT=0
ROLLBACK: QUEST_PREFIX_GAPS=8 BYTE_IDENTICAL=YES MODIFIED_REMAINS_CHANGED=YES EXIT=0
```

新策略 `omission-screen-v35.json` 只更新有效主INT身份，63项既有分类仍为40 pending／23 excluded。
`성쇄`、未闭合拼接、测试／文档等保留项不批量猜译；315个字幕cue不改。
沿用v34选择器，从最终recipe重新生成49个文本视图／52个物理成员，
原盘全SHA前后复核，再运行 `audit_text_residuals --require-classified`。
前缀遗漏0与已分类保留63分别报告，不说“全游戏没有韩文”。

## 生产重建入口

字体、Pillow／numpy／fontTools以及FFmpeg／RAD身份由各源计划固定。
电影普通重建重放冻结的稀疏补片，不依赖再次运行神经模型。
ProPainter研究来源、固定提交和许可见[第三方说明](../LICENSING.md)；
不提交电影、完整原帧、模型、权重或游戏包。

从锁定原盘只提取小型资源子集：

```powershell
foreach ($descriptor in @(
  'locales/zh-Hans/source-resources/worldmap-destination-movies.json',
  'locales/zh-Hans/source-resources/swapdisc-movies-v35.json',
  'locales/zh-Hans/texture-overlays/style-stat-sources-v35.json'
)) {
  python -B -X utf8 -m tools.materialize_resource_sources --descriptor $descriptor `
    --project-root . --inventory 1=build/disc1-hashed.json --inventory 2=build/disc2-hashed.json
  if ($LASTEXITCODE -ne 0) { throw '原始资源身份不符' }
}
```

每个源计划已有精确输入SHA；输出必须新建，不覆盖原片：

```powershell
$catalog=Get-Content locales/zh-Hans/worldmap-captions-v35.catalog.json -Raw | ConvertFrom-Json
foreach ($item in $catalog.entries) {
  python -B -X utf8 -m tools.build_worldmap_captions `
    --plan $item.plan.path --plan-sha256 $item.plan.sha256 --project-root . `
    --source-root build/phase-360-chapter-research/sources `
    --output-dir ("build/rebuild-worldmap-v35/"+$item.id) `
    --ffmpeg <固定FFmpeg绝对路径> --ffmpeg-sha256 <固定摘要> `
    --encoder <授权RAD绝对路径> --encoder-sha256 <固定摘要>
  if ($LASTEXITCODE -ne 0) { throw "电影重建失败: $($item.id)" }
}
```

换碟采用同一命令、`swapdisc-captions-v35.catalog.json`、源目录
`build/phase-365-swapdisc/original`，并选择另一全新输出根。
对每个同一输出再加 `--verify`，独立回解全片。
WorldMap66条原始PCM音轨、23760个压缩音频包保持原样，换碟仍为0音轨；
成品总计4020帧，不把视频帧率头正确当作真实帧数完整。

原生供体补片可独立按下列命令重放，9个PNG应匹配locale冻结SHA：

```powershell
$p='locales/zh-Hans/texture-overlays/style-stat-repairs-v35.json'
python -B -X utf8 -m tools.build_native_pixel_repairs `
  --recipe $p --recipe-sha256 (Get-FileHash $p).Hash.ToLower() --project-root . `
  --output-dir build/replay-stat-repairs-v35 --lzx-library build/lzx/native-verified/ue3_lzx.dll
$p='locales/zh-Hans/texture-overlays/style-stat-aliases-v35.json'
python -B -X utf8 -m tools.build_texture_alias_update `
  --profile $p --profile-sha256 (Get-FileHash $p).Hash.ToLower() --project-root . `
  --source-root <累计阶段363当前资源子集> --output build/rebuild-stat-aliases-v35 `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll
```

核心包输入必须为累计阶段363的 `6a5d568d…`，独立Style_Tree包为原始 `6f9562d8…`，
不可把原始核心包当成累计当前资源；别名工具保留非选字体／导出。
再通过现有增量comparison及安装器源准备工具组合；不得拿供体整个包替换当前核心包。

发布前另消除6份新JSON的Windows CRLF／Git LF身份差异：先归档原始字节，
再规范LF并重绑定父SHA。JSON语义与生成的生产子计划字节完全相同；
重新回解两段原成品60帧、重建Quest并重扫文本，所有游戏输出字节不变。
证据为本轮 `canonical-json-reverified.json`，不修改Git行尾合同或跳过SHA检查。

## 章节标题继续调查

新证据见[实际过场结束显示链路](PHASE_365_POSTCUTSCENE_TITLE_ROUTE.md)：
六个真实FinishCSMB结束事件已追到OpenEntranceTitle→HUD→Texture2D材质参数。
66个行动路线别名及另一路volume的37个别名均已原生独立重放为现行中文；两组计数有重叠。
34个动态位置宏另追到场地菜单位置标题，不是新的章节卡。
这排除了已查路线中的旧韩文字图，却仍未绑定用户所说的独立大章节卡；
`UI-20261107-02`保持未结，不以本轮11段WorldMap或既有47张入口图冒充完成。

## 增量发布与证据

最终双盘视图为471／573项资源、另2项DLC；相对阶段363恰28条资源身份改变，
未改变的资源、DLC和工具身份保持。阶段332外包门禁为 `ALREADY_CANONICAL`。
既有Disc1测试目录只显式登记9个原始成员并摘要增量刷新，
Disc2使用最终recipe的独立资源视图；不新建ISO或完整游戏目录。

本地证据根为 `build/phase-365-omission-repair/`，四产物为
`MODIFIED_FILE.exe`、`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行 `ROLLBACK.sh`。
BASELINE／MODIFIED／ROLLBACK均对实际EXE执行资源审计：旧／恢复版应重现28个旧身份失败，
修改版应为0；恢复只在另一独立副本进行，保留修改成品及发布入口。
三态精确命令、输入、字面输出、退出码和恢复身份写在同一VERIFICATION中。

发布自检核对完整内嵌payload、双层v1.0版本及临时引导目录清理；
原版、配置、存档和runs的133项受保护摘要另逐项复核。
单文件入口仍为 `dist/MC2-CN-v1.0.exe`，实际身份以本轮 `release-identity.json` 为准。
本轮实际EXE为1,743,439,419字节，SHA256
`b7d7f1ebba62a94cd469248b021498798780086d7aa7515f18806d515571c676`；
完整内嵌756文件通过，bundle manifest SHA256
`f1b31755e6069483674f511cf2b35c471695c0ae58b684b98f9f8003b49a407e`，
最终recipe SHA256
`f9f80fad31dfd7b90d909504248745aa357dfdcee9c661fc2d3b818701114ff2`。
正常提交推送须通过不可变源码／新venv预检，并等待同一提交四组云端CI；
检查结果另附本轮VERIFICATION，不以推送成功代替CI。
这些均不声称游戏启动、实际换碟、播放全流程或用户美术验收。
