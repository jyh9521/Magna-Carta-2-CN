# 阶段325：实机截图反馈、载入影片与增量交付

本轮接续用户的12张游戏截图反馈。工作在用户完成磁盘清理并明确恢复后继续。
原始双盘、配置、存档、运行记录保留；不启动游戏，不再制作整盘副本。

## 修订集合

| 反馈 | 实际资源改动与验证 |
|---|---|
| 震动、开启/关闭、正常/反向 | “手柄振动”；统一同套字形与状态基线/采样窗。原图的未选灰色与选中白色/红光是有意差异，不应消除；先前混用字族不是原图效果。 |
| 主菜单左栏、道具标签、饰品数字 | 依据真正消费者UV窗口而非整张图集居中；饰品文字与1/2基线配对。 |
| 位置、游戏时间、SID | 标签13px，保留原值与字段位置。 |
| 当前成员上方残留、耐力黑线 | 修复擦除范围、采样相邻行与阴影厚度。 |
| Juto、风息岛 | 原生alpha连通分量修复；完整邻接英文、地图原生块和人物123,959可见像素保持。地图底部淡影补清4行，中文新增行alpha为0。 |
| 主标题选中动画偏移 | 统一普通/选中/影子对应采样原点；包括Back的U0/U122配对，不改变原动画。 |
| 按钮说明遮挡、断句、出框 | 四项受保护的Coalesced修订：“切换”“移动”、完整地点括号、恢复原句间换行；18,172项其他条目保持。 |
| 白背景字幕 | 两个Subtitle别名增加1px黑色alpha阴影，2,391字形的原前景、度量、UV与字距保持。最终shader是否保留atlas RGB仍待游戏内验收。 |
| 载入图文字 | 14个角色/设定片和通用loading循环，采用结构化译文与原片测量的标题渐变、细亮倒角、深色边缘/柔影、正文行距和左右对齐；保留90帧与原精确时间基。 |

文字/字体证据见 [PHASE_325_TEXT_RUNTIME](PHASE_325_TEXT_RUNTIME.md)，地图/人物原生证据见
[PHASE_325_ART_NATIVE](PHASE_325_ART_NATIVE.md)。所有游戏画面验收仍由用户执行。

## 纹理与文字的合成顺序

1. 保留 `ui-labels-reviewed-v6.json` 作为已接受基线。
2. 对其Startup **pre-overlay base** 加字幕阴影；不是对已经叠过v6文字的成品再次画完整v7。
3. `ui-labels-gameplay-v7.json` 包含完整受影响包的全部历史标签，
   `tools.build_texture_delta` 只选择真正变化的包。第一盘9包、第二盘8包。
4. 用 `build_texture_delta --verify-root` 从锁定原文与计划独立重放；
   地图tail是单独的2/1包后续差异，其他候选复用，未重复生成整套包。
5. 在部署前仍须执行阶段324的 `normalize_package`，不能把可离线解码的
   generated stored-LZX直接当作已证明兼容游戏的包装。

正式计划SHA256：`e8ae524a13ad91f595333b515865b78f10ff03b14f60fdb3c805df5ee30dd936`。
旧1718快照仅供阶段中途包重放，不替代最终计划。最终选择记录在
`build/phase-325-gameplay-feedback/texture-final-resources.json`。

已通过64项消费合同、35项真实UV采样及10个art物理别名。
这些是资源/序列化消费者证据，不是模拟器截图。

## Bink影片管线与风格

`locales/zh-Hans/loading-captions-v7.json` 是语言数据：包含逐片原始SHA、
原始解码帧SHA、原字形连通分量、中文行文、锚点、字体、描边、柔影、倒角、
颜色渐变及锁定的栅格器版本。通用工具不含角色名字或中文专用路径。

- 01/11/12右对齐，其他左对齐。标题按原可见底边锚定，中文不做横纵不同倍率拉伸。
- 标题上白下灰，底部与侧面有细亮边；正文接近白色，不套用标题金属渐变。
- 原文字的字体身份没有从烘焙图中恢复；当前字族是逐图对照后的匹配选择，
  不宣称是原字体，也不把参数对齐表述为艺术验收“丝毫不差”。
- 字后光带是原背景，不是给所有中文新增的一条通用光效。
- 擦字采用逐个已核对连通分量；不能用全矩形亮度阈值，否则02天空与08白手甲
  会被当成白字抹掉。只替换原字支持/效果范围；被原字遮住的底图是局部重建，
  不是声称找回不可见的原始像素。与08同名的两张Style_Argo纹理是另一姿势，
  已核对并未拿来强行覆盖。
- 所有编码前支持区外像素逐帧精确不变；Bink是有损格式，编码后另报背景/字区误差，
  不冒充整片像素无损。

### 正确的批处理与时序

RAD的自动关闭参数是 `/#`，不是 `/AutoClose`。
参考：[RAD官方FAQ](https://www.radgametools.com/binkfaq.htm)。
旧参数导致帮助窗口；新工具在独立、从未切换到前台的Windows desktop中启动
明确的自有编码器进程，先加入kill-on-close job再运行，超时180秒就停止该子树。
不改用户桌面/窗口设置，不启动Xenia。Win32依据
[CreateDesktopW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createdesktopw)与
[STARTUPINFOW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow)。

原片`10000000/333333`约为30fps。直接把此数传给AVI会被容器改写为
`999991/33333`；实测RAD只编码89帧，即使AVI解码仍有90帧。现在以精确30fps
作为临时AVI运输时间基，确认输出仍90帧后，仅恢复BIKi头的原有分子/分母。
不复制/删除内容帧，不变速度，不添加音轨。非近整数时间基未验证，工具明确拒绝。

```powershell
python -m pip install -r requirements-font.txt
python -X utf8 -m tools.build_video_captions --plan locales/zh-Hans/loading-captions-v7.json --plan-sha256 PLAN_SHA --project-root . --source-root ORIGINAL_LOADING_DIRECTORY --output-dir NEW_LOCAL_BUILD_DIRECTORY --ffmpeg FFMPEG_EXE --ffmpeg-sha256 FFMPEG_SHA --encoder RADVIDEO64_EXE --encoder-sha256 ENCODER_SHA
# --entry loadingmovie_05 可单片执行；--verify 在同一输出目录独立解码重放。
# --preview 只生成检查图，不运行编码器。
```

`ORIGINAL_LOADING_DIRECTORY`内保存用户原盘提取的`loading.bik`与01–14。
每份源文件必须匹配计划大小/SHA。输出保存逐帧散列、90帧重放、工具身份与
私有桌面记录。AVI为可再生中间文件，单片成功后即清除；禁止批量转存PNG帧序列。
影片和原始PNG都不提交Git。55项纯函数/边界测试不依赖游戏或编码器。

## 增量刷新契约

ISO沿用`dist/MC2-test-iso-v6/`的两个既有路径。
`tools.repair_disc_image prepare-refresh` 消费SHA锁定的前置计划与实际变化成员清单，
归一化xxx，追加变化资源和TOC，再修改已有8字节目录字段。新增目录字段绑定会
证明偏移确实属于指定path的真实XDVDFS目录项；完整输入/输出哈希、全部成员及
逆向旧前缀都要一致。两轮小型镜像真实应用/隔离还原已测试。

提取测试目录继续用`dist/MC2-display-repair-disc1`，它仍是独立的v6基线，
不能拿ISO的before哈希代替文件夹before哈希。新增的Style_CountryJuto和15个BIK
需要显式enrollment；不变的旧packet成员只复用不可变阶段视图，不复制整盘。
当前用户配置内容保留，入口记录更新其真实哈希。

回滚入口与实际交付身份由本轮根目录`VERIFICATION.txt`记录。
阶段324和旧packet是保留的前置，不是最新部署的替代描述。

### 本轮离线结果

- 完整本地测试：2,403项，`OK (skipped=1)`；纯影片边界测试55项。
- 15影片共1,350帧，总129,825,332字节。编码前支持区外改动0像素；编码后
  最大单帧背景通道平均误差1.244/255、文字支持区3.615/255。
  15次编码均保持原前台desktop未变，全部90帧及原精确fps保持。
- 第一盘追加264,386,560字节；第二盘追加263,405,568字节。
  不是新增两份12GB镜像。所有2,016/2,340个成员、TOC与虚拟逆向旧前缀均通过。
- 第一盘当前：12,005,189,632字节，SHA256
  `d5aca132c8d2981fa96fefa83be4c01398de6c2e538c803c6f743ec4fdedc55c`。
- 第二盘当前：12,528,769,024字节，SHA256
  `a0c8ebaff256b7dabd4817ee11ed082edc8809070ff86394e3b297904154fbcb`。
- 后续增量前置计划改用本轮`disc1-refresh/plan.json`与`disc2-refresh/plan.json`，
  SHA分别为`d3ffcb16efa361e9d0a607afb4ba8a9ed6c71505280aece38ae08705e31bc724`、
  `4f92cc01673ca24da9c63844202b035b35ab4588fff11b822ec8edc742dbae15`，不要继续传阶段324计划。
- 已清除本次失败的AVI/BIK中间输出257,234,114字节，失败头部/哈希/89帧原因和日志保留。
  成功编码的临时AVI逐片自动清除；原始影片、最终影片、事务资源与回滚证据保留。

## 人工复测

沿用原测试入口。核对设置所有切换态、主菜单各选项/道具标签、饰品1/2、耐力、
朱特姓名、风息岛标题、主标题脉动；重播亮背景字幕，检查完整地点括号和底部两行。
载入画面另看14个人物/设定、左右版式及循环过渡，尤其02的山体与08的手甲局部。
离线边界、解码与结构通过并不等于这些游戏内画面已经通过。
