# 阶段337：载入闪光残块与全物品字距

## 已验证的根因

- 用户截图对应 `loadingmovie_05` 第16–24帧附近。v10在不可逆旧字芯内，
  用最近已知像素的光照差驱动稀疏底图，闪光移动时形成分片常值色块；
  底图与原生背景的边界颜色也不连续。首帧和编码误差检查没有覆盖这种时间变化缺陷。
- `赤月斧` 三个码点之间没有空格。General_15原生字格宽均为27，
  “月”的左留白较多，实际字芯间隙12/9原生像素。这是透明留白，不是译文或字号错误。

## 实现与写集

`loading-captions-v11.json` 继续锁定15段原始Bink、v10稀疏底图、正文/标题
和提示字体。只替换indicator的时间光照算法：

1. 稀疏底图通过原生已知边界作有界谐波颜色校正，保留其纹理梯度。
2. 每帧只从扩展矩形周界计算光照变化；NumPy FFT实现可分离DST的Dirichlet解，
   不把受旧文字污染的内部像素当光照源，不再复制最近像素的闪光。
3. 原192×40区域扩为216×88，配置padding为左0/上24/右24/下24，
   以显式羽化权重过渡到当帧原图；左侧旋转标记不纳入扩展写集。
4. 保留90帧、1280×720、BIKi、无音轨、10000000/333333时基和三个点数状态。
   编码前精确写集之外逐像素相同；Bink有损误差另行检查。

`tools.fit_font_padding` 根据语言数据的595个物品用字，只调整四包/七别名
的 `FontCharacter.StartU/USize`，同步tagged与native副本。以左2/右3透明像素为裁边目标，原本较小的边距原样保留，
以alpha>0检查全部弱抗锯齿与阴影，字格只缩不扩。3438个字格改变；
图集、字形像素、字号、垂直度量、映射及未选择字格保持不变。
`赤月斧` 的General间隙变为7/6，小字体5/6，字幕6/6。

字体由多个界面共享，所选字在其他动态文本中的宽度也同步缩短，并非另建物品字体。
旧“所有宽字符至少字号+5”不再是本次选中字格的下限；完整字形与透明边距是新合同。
写集为4个字体包、15个Bink及尺寸联动TOC；存读档布局/标签贴图、数字、译文、DLC容器不变。

## 全量物品覆盖

`tools.audit_item_spacing` 从完整名称银行建立清单，不只搜索“赤月斧”或DLC：

- `MC2Item.int` 全部1630字段、586条名称；`MC2Kamond.int/Karmond` 的309字段、103条名称。
- 合计1939字段、689条物理名称记录。原表同键两次出现均保留核对，不猜测运行时重复键选择规则。
- 595个宽字母码点；2228个相邻字对 × 7别名 = 15596项检查。
- 12份1MiB空格型DLC标记逐一绑定 `data_weapon.xxx` 的实际导出和名称ID。
- 原生包逐一解包扫描；对压缩文件搜索原始字节会漏掉条目。
  ItemName专用有界读取器支持 `RelatedQuestID_2` 等合法编号FName，避免漏掉两个任务物品。
- 第一盘114个含物品包、1457条ItemName。9条原生字面量与48条原始缺失引用独立列出锁定；
  48条在原文Coalesced也不存在，未因翻译丢失。默认/测试样式字段的可达性未验证，
  不将其全部宣称为未使用数据。
- 第二盘流式扫描锁定安装recipe的“原始ISO区段 + 最终增量资源”，不提取完整游戏副本。
  共扫描2233包，其中151包含1789条ItemName；原始48条缺失引用和9条字面量与第一盘集合一致。
  两盘名称银行和共享字体以最终recipe中的文件摘要交叉核对。

字对合同为原生字芯间隙5–8像素；基线3568项失败，修改后0项。
原有拉丁字、数字、标点及合法分词空格保留，不通过改名删字掩盖问题。
`ITEM_SPACING_AUDIT.csv` 列出全部689条名称和三类字体的前后字距。

## 可复现入口

```powershell
python -m tools.fit_font_padding --profile locales/zh-Hans/item-font-padding-v11.json --profile-sha256 PROFILE_SHA --source-root PREVIOUS_PACKET/candidate --output NEW_FONT_BUILD
python -m tools.build_video_captions --plan locales/zh-Hans/loading-captions-v11.json --plan-sha256 PLAN_SHA --project-root . --source-root ORIGINAL_MOVIES --output-dir NEW_MOVIES --ffmpeg FFMPEG --ffmpeg-sha256 FFMPEG_SHA --encoder ENCODER --encoder-sha256 ENCODER_SHA
python -m tools.audit_indicator_lighting --plan locales/zh-Hans/loading-captions-v11.json --plan-sha256 PLAN_SHA --prior-plan locales/zh-Hans/loading-captions-v10.json --prior-plan-sha256 PRIOR_SHA --source-root ORIGINAL_MOVIES --ffmpeg FFMPEG --ffmpeg-sha256 FFMPEG_SHA --candidate-root NEW_MOVIES --output-dir NEW_LIGHT_AUDIT --max-curvature .01
python -m tools.audit_item_spacing --game FULL_TEST_CANDIDATE --font-root NEW_FONT_BUILD/candidate --profile locales/zh-Hans/item-spacing-audit-v11.json --dlc WEAPON_STFS --lzx-library LZX --original-coalesced ORIGINAL_COALESCED --output NEW_ITEM_AUDIT
# 第二盘：在上一条命令增加锁定的最终安装视图
# --resident-installer-recipe RECIPE --resident-recipe-sha256 RECIPE_SHA --disc 2
```

DLC整体审计继续使用 `tools.audit_dlc_localization`，增加
`--font-metrics-profile locales/zh-Hans/item-font-metrics-v11.json`。
overlay锁定原布局摘要，只允许改变advance摘要，不放宽字体、字高或映射合同。

15段全部1350帧经过源回放和成品Bink复解码。旧算法1335帧出现非谐波分片，
最大离散曲率155；新算法最大约8.53e-14，失败0帧。测量对象是实际修复使用的
时间光照场，不对自然纹理边缘施加平滑约束。曾试用“邻像素差≤4”，它误报合法陡梯度，
现以带反例测试的离散曲率检查替换，未把旧门槛结果当通过。
成品提示ROI最大均值误差1.950、最大p99误差14.334（门槛5/24）。
另检查15段解码预览及05的0/16/24/48/64/80帧，保留前后原生截图。

证据根 `build/phase-337-loading-item-spacing/` 包含命令/输入/退出码、1350帧报告、
字距CSV、重建一致性、独立回滚及 `VERIFICATION.txt`。四项交付证据为
`MODIFIED_FILE.xxx`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`。
资源回滚只在另一份20资源小副本测试，原始输入和正式修改结果保留。

## 交付和画面复测

复用441资源packet，通过阶段332外壳门禁后增量刷新既有中文测试目录。
安装recipe覆盖两盘共享资源，再重建单文件安装器；不新建ISO或完整游戏副本。
原配置、存档、runs、原文对照及DLC安装绑定保持。

退出旧进程后，沿原“开始中文测试”入口复测整个载入闪光循环，以及背包/装备/商店/
获得提示中的本体与DLC名称。已有独立ZAR/ISO不会自动刷新。
本轮离线逐帧、字体和资源审计不等于游戏内验收；游戏未启动。
