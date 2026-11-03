# 阶段355：存档点裁切、任务完成居中及奖励底框核对

承接阶段354任务通知去句号。用户另外提供了存档点、奖励底框和任务完成标题截图；
本轮只改三个包的20个浮点字段，不重绘文字、不更换字体、不改奖励数值。

## Verified：存档点底部确实被取图窗口裁掉

文字位于 `UI_Name_Jpn.Pillar.Piller_Menu_Title`，原生中文字芯边界为
`[175,3,217,17]`；旧消费者从V=0只取16行，因此最后一行字芯及下方阴影被截断。
源贴图本身完整，不能用“贴图里看得到三个字”替代消费者检查。

- 两个包中的三个场景副本、每场景三个槽位，共9个 `SavePoint_Title`。
- 每个消费者只将 `Position.Value[3]` 和 `StyleCustomization.Coordinates.VL` 从16改20。
- UV高度与控件高度同步扩大，比例仍为1:1；X/Y、字形、字号、纹理及其他数值不变。
- `UI_Pillar.xxx`六个槽位、`TitleMap_MSPT.xxx`三个槽位全部覆盖。
- 独立 `UI_Pillar_Title.xxx` 没有这些导出，不能仅凭包名追加修改。

原生金色字芯阈值 `[100,80,50,160]` 下，9个窗口合计漏采72个像素，修改后0；
其他较低阈值的描边/阴影也因扩大采样范围而恢复。本检查未把阴影算作文字字芯。

## Verified：任务完成按自己的可见边框居中

实际消费者驻留于 `MC2Game.xxx`：
`UI_Core.Scenes.QuestCompleteReward.Base.Quest_Check_Window.Quest_Check_Title_img`。
它采样 `UI_Name_Jpn.Tex.Quest_tex01` 下方的“任务完成”；左对齐字芯保留了原文布局的偏移。

- 字芯原生边界 `[3,38,80,57]`，旧屏幕局部中心 `[312.5,4.5]`。
- 自身边框是另一个 `Quest_Check_Title` 图像消费者，绑定 `UI_Core.Textures.Quest_tex02`。
- 完整可见亮边（含右侧卷纹、不含微弱外晕）的边界 `[5,18,212,54]`，
  经实际UV/坐标换算后的局部中心为 `[342.5,7]`。
- 边框高度并非猜测值：消费者未覆盖高度，实际继承 `Engine.Default__UIImage` 的50。
- 仅将标题文字X从271改301、Y从-11改-8.5。修改后中心差X/Y都为0。
  边框、字号、图像尺寸及奖励区域完全不动。

`tools.audit_ui_image_bounds`逐一追踪 `ImageComponent → ImageRef → ImageTexture`，
读取实际UV、坐标、显式默认值和原生纹理。区域、阈值、引用名称、默认来源与原生摘要
均在locale合同中；工具不硬编码游戏对象名或中文内容。

双盘完整候选视图共扫描4145个包（第一盘1912、第二盘2233），
每盘都只有以上三个包包含本轮目标消费者；发现数为4/3/6，其中4包含标题与原版两个奖励底框。

## Verified：EXP / SID 黑色底框与原版相同

两个对象 `Black_Box_EXP`、`Black_Box_SID` 的控件、图像组件及UITexture载荷与原版逐字节一致。
它们通过相同的样式ID绑定 `Startup_int.xxx` 中 `style_ui.Base.BlackBox`；
该样式及六个状态子对象共7份载荷与原版一致。
实际底图是 `UI_Field.xxx / Textures.Field_Style_BlackBOX`：

- 原版与当前的原生BC纹理字节完全相同。
- 解码尺寸512×128，65536个RGBA像素全部相同，差异像素为0。
- 贴图中心RGBA为 `[0,0,0,164]`，这是**贴图数据**，不是对游戏最终画面透明度的描述。
- 用户截图看起来接近全黑。离线Alpha不能单独证明运行时的材质混合、叠层或最终观感；
  本轮没有原版实机对照截图，也没有以合成图冒充原版实机。
- 用户要求“原图不是黑底才修改”，故这两个原版底框保持不变。

`build/phase-355-save-point/reward-background-comparison.png` 上方展示原版/当前资源
在同一棋盘底色上的对比，下方是用户游戏截图裁图；证明文件为 `reward-comparison-proof.json`。
`save-title-comparison.png`为实际原生纹理按修正前后序列化坐标离线合成，也不是游戏截图。

## 可复现修订与三态验证

语言层计划：`save-reward-{save,title,game}-fields-v28.json`；
几何合同：`save-reward-image-bounds-v28.json`。

```powershell
python -m tools.patch_tagged_fields apply INPUT --source-sha256 SHA --profile PROFILE --profile-sha256 PROFILE_SHA --output OUTPUT --report REPORT
python -m tools.audit_ui_image_bounds --root CANDIDATE --fallback USER_GAME_COPY --plan locales/zh-Hans/save-reward-image-bounds-v28.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --report REPORT
python -m unittest discover -s tests -p test_ui_image_bounds.py -q
python -m unittest discover -s tests -p test_save_reward_v28.py -q
```

基线：`IMAGES=11 CLIPPED_PIXELS=72 CENTER_FAILURES=1 RESULT=FAIL`，退出1。
修改：`IMAGES=11 CLIPPED_PIXELS=0 CENTER_FAILURES=0 RESULT=PASS`，退出0。
隔离回滚恢复三个原始包摘要，并重现基线输出/退出1；修改产物保持。

证据目录保存 `MODIFIED_FILE.json`、`DIFF_FILE.patch`、`VERIFICATION.txt`、
可执行 `ROLLBACK.sh`、原始资源摘要、逐字段offset/字节差异、双盘资源与刷新报告。
双盘各3个包变化，资源总数仍442/543，TOC字节和2个DLC保持；
阶段354的任务提示文字保持。沿用既有测试目录，保存增量备份；不生成ISO/整盘副本，
不启动游戏，不重打包安装器。用户从原测试入口重新载入资源后复看真实画面。
