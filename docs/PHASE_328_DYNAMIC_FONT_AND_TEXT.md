# 阶段328：动态文字字体与截图问题（2026-10-28）

本轮用户最终决定覆盖此前“译名先记录”的要求：标题和剧情内同词一律使用
“真名法典”。字体采用已选定的朱雀仿宋合成500；图片文字不参与换字体。
仅控制器说明图的左侧“切换目标”和右上孤立线段获得明确的局部修订授权。

## 已验证的改动

- `gameplay-text-v8.json` 对已部署的 Coalesced 做52项源值哈希保护的覆盖：
  46条含旧译名的文本（48次出现）及6项拾取消息语法字段。
  独立 `csm09-40.txt` 另有3条字幕；使用单独时码/源值锁定计划修订。
  两盘全部INT/TXT运行资源分别23/25个，替换后旧译名出现次数均为0。
  不修改历史批次、韩文源标识、文件名或其他“卡尔塔”概念。
- `diction.Objective_0/1` 原为“已”，脚本另拼接空格及“获得”。
  现在保留脚本和空格，只把两个前缀置空，四个后缀分别设为完整的
  “已获得”或“已习得”。实际字段回放由 `100SID已 获得` 变为
  `100SID 已获得`，空格位于消息词组之前。
- 控制图左侧墨迹框高度27→19px，采用右侧同一套字形/渐变参数。
  原生BC3解码后白字核心宽度由100/79变为79/79。
  右上被旧擦除窗口隔开的引导线尖端在12×12px区域补清；该区最大alpha
  由216降至1，余下2个alpha=1的黑色采样属于上方新文字阴影边缘。
  两个采样别名仅223个native块变化；授权矩形外解码像素完全一致。
- 四个包中的七个动态Font别名切换到朱雀仿宋。大/小/字幕字体覆盖
  2580/2580/2583个已有映射；包括中文、拉丁字母、数字和标点。
  图标字体、伤害数字美术字体、未选韩文槽、已完成载入影片及图片文字不变。

## 字体方法和边界

源字体仍为 v0.212 Regular400，无可变字重轴，SHA256：
`558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4`。
沿用阶段327选定的 `.006em` FreeType轮廓扩张；500是合成目标，
不是修改OS/2名称或冒称上游存在原生Medium文件。

| 角色 | 中文栅格字号 | 拉丁光学字号 | 可见字格高 | 全角最小advance |
|---|---:|---:|---:|---:|
| SmallFont | 15 | 12 | 18 | 20 |
| General_15 | 22 | 18 | 25 | 27 |
| EngineMedium_Subtitle | 27 | 22 | 31 | 32 |

全量字库不是37字预览样本：字幕中文前景联合高度达30px，故字格由29增至31，
容纳完整前景和1px右下黑影。拉丁 U+0000..00FF 使用显式光学字号范围，
避免重音字母超高；不是运行时兜底到别的字体。全角 `１ＤＩＬＳＶ` 使用
同一朱雀字体的对应ASCII轮廓，仍保留原码点及全角advance。
旧advance能容纳新墨迹时保留，个别较宽字形以墨迹宽度加边距扩宽。

`reface_font` 同时更新 tagged/native 两份 FontCharacter 字段，
重新分配所选atlas内4px对齐矩形，避开全部未选字形；保持remap、
其他Font导出及其他图片字节。Xbox native BC3须进行16位字节交换。
写后逐字重新取块、解码并核对RGBA摘要。七别名共18066个字形回读通过，
轮廓增长越界采样为0，两个字幕别名各新增213237个黑影像素且阴影裁切为0。
现有8项真实文本消费者边界/换行/阴影回放通过。

原文中两个已知损坏字段 `MC2Game.int [] ItemName/Accept` 继续保留，
不能把错误UTF16拼接得到的伪汉字当作正常字形需求。报告逐ID/SHA列出它们。
这些离线证据不等同于Xenia实际shader、全流程和艺术效果验收；本轮不启动游戏。

## 重建与独立验证

输入是阶段325已验证的资源字节，而非任意版本的原包。两盘共享资源按SHA
核对后只保留一份输入，独立字幕来自第二盘。源字体下载/许可依赖见
`FONT_COMPARISON_PREVIEW.md`，控制图沿用既有哈希锁定源纹理和字形源。

```powershell
$p = 'build/phase-328-dynamic-font-adoption'
python -X utf8 -m tools.build_gameplay_revision --profile locales/zh-Hans/gameplay-revision-v8.json --source-root "$p/baseline-resources" --output build/rebuild-v8-new --lzx-library build/lzx/native-verified/ue3_lzx.dll
$h = (Get-FileHash locales/zh-Hans/dynamic-font-zhuque-500.json -Algorithm SHA256).Hash.ToLower()
python -X utf8 -m tools.build_font_reface --profile locales/zh-Hans/dynamic-font-zhuque-500.json --profile-sha256 $h --source-root "$p/baseline-resources" --verify build/rebuild-v8-new/fonts
python -X utf8 -m tools.replay_text_consumers --resource-root "$p/final-resources" --ui-package "$p/final-resources/MC2Game/CookedXenon/MC2Game.xxx" --native-image build/xex-native-verification/disc1-native-image.bin --profile locales/zh-Hans/gameplay-text-consumers-v8.json --output build/text-consumers-v8-new.json
python -X utf8 -m unittest discover -s tests -v
```

两个独立构建的最终7个规范化资源字节相同。构建器不部署，不启动外部视频工具。
所有完整包、原图、字体文件和ISO均位于忽略目录，仅提交工具、计划、测试和文档。

## 测试入口与事务

本轮用户明确要求更新ISO；复用两张既有v6测试ISO，按哈希保护的追加资源+
TOC/目录项刷新完成，不生成额外整盘副本。保留原盘与可逆目录字段、前缀摘要。
本地计划在 `$p/disc{1,2}-refresh-final/plan.json`。
`repair_disc_image prepare-refresh` 接受阶段325前驱计划、当前ISO和
`disc{1,2}-replacements.json`；应用前先 `preflight`，应用后 `verify`。
验证覆盖当前完整ISO摘要、活动资源、TOC以及反向目录映射后的旧前缀摘要。

既有文件夹测试入口也通过 `compose_incremental_comparison` +
`refresh_oneclick_probe` 更新。注意旧文件夹控制图包的SHA是
`25b11fc83dc6cacb450d5972b2ccc96e85adebbfc36472c3de3157529d14d4ee`，
ISO中对应规范化包是
`183bc82c6241a13b29816e2bfa4ac93baec152c834d492b273b3be1bd06c77aa`；
两者语义相同但不能混用before哈希。新两处统一使用规范化资源。
保存配置、存档、runs、XEX和原文对照；不自动运行游戏。

`$p/MODIFIED_FILE.json` 列明七个文件的前后哈希，`DIFF_FILE.patch` 保存源码差异，
`VERIFICATION.txt` 保存完整执行记录，`ROLLBACK.sh` 是可执行的隔离资源回滚入口。
脚本参数可指定新的证据子目录，已存在路径会拒绝覆盖。
真实七文件隔离复制→还原后，原字体、旧译名51次、旧拾取间隔和旧控制图均恢复，
当前修改候选保持不变。不是声称已经物理还原并再次制作两张完整ISO。
运行 `repair_disc_image recover` 会修改测试ISO，应仅在明确需要撤回时使用。

## 人工复测

检查两边“切换目标”、右上指示线、拾取道具/SID/武器/技能消息，
无存档提示与剧情标题名，以及15/22/27px动态文字、长句换行、白背景字幕黑影。
载入图片、标题美术字、按钮美术字和先前已完成图像应保持上一轮样式。

## 本轮交付记录

沿用 `dist/MC2-test-iso-v6/`，文件名未变，当前完整镜像摘要为：

| 文件 | SHA256 |
|---|---|
| MC2-Disc-1-zh-Hans-test-v6.iso | `9cc5d550bbe87c2625eb3bf3fd5708b3d92e4b753395f505b4fc283f9d80ed46` |
| MC2-Disc-2-zh-Hans-test-v6.iso | `55ab51269308709456641491a263c84bacbf7a636c93cda87ad2ef64fbe0cd8a` |

两盘独立验证分别读取2016/2340个文件；全部活动文件摘要、目录字段和TOC通过，
逆向旧前缀摘要分别恢复至 `d5aca132…` / `a0c8ebaf…`。
文件夹测试入口419资源核对通过，原文对照、配置、runs和存档保留。
全套2440测试通过（其中1项按原条件跳过），8项文本消费者回放通过；
两盘2362个有效中文需求在三个动态角色字体中均无缺字。

清理尚未执行：本轮已列出并核对89个可再生中间文件，合计2,165,448,701字节；
删除命令被执行工具拦截，实际删除0字节。`cleanup-plan.json`/`cleanup-result.json`
保留清单与未执行状态，不把这部分写作已释放空间。最终资源、原件、独立回滚副本、
活动包依赖及研究报告继续保留。
