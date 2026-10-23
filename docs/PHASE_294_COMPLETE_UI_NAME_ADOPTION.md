# 第294阶段：UI_Name完整菜单与技能图片实际回填

## Verified / 已采用边界

新增剩余56张UI_Name_Jpn源图、274文字层、204双盘真实别名（各102），累计461图片组、708文字层、2004别名（997/1007）。UI_Name_Jpn的184张原导出全部进入当前纹理计划；这不是所有游戏图片/教程/硬编码或游戏验收完成。源包并集273，纹理组件D1/D2为173/230资源，对照包198/257资源；新增纹理资源每盘2个，但Startup_int已有Font组件，所以对照包每盘只新增1个，不能将组件数量直接相加。INT仍14159/batch121，七Font和315字幕保留。

## 逐图原文与上下文

17张技能图集含98层；81层有精确INT/JPN同字段与最终采用译文依据，193层是可读源图/菜单语境的新译法。技能图片和同排字段有真实不同，保留原图裏空進槍、秘奥義一撃必殺等，不按英语leaf/排号猜成最终技能名。同原词로드在存档菜单是读取，不套武器法杖；选项초기화为恢复默认，不套卡蒙德初始化。全部双状态成套采用。显式身份/GUID、payload、tiled、RGBA与尺寸匹配的204实际别名入包，不只修改UI_Name独立包。

窄邮件TO./FROM.采用致/来自，窄装备보조采用辅助，宽菜单保留辅助装备；这是语义等价短标签，不把三字缩到6px。原研究垂直余量只检查6px，而实际rasterizer要求8px：保留实际守卫并逐层收字号，存档点小旁注为8px，其他字体至少12px。实际字形/描边有界，未放宽glyph、图像尺寸、重叠或保护检查。

## 编码后实际审看纠正

56原图与真正BC3编码再解码预览逐张审看。186/187卡蒙德分类原图为32px行距，研究28px分带会在底部残留韩文字形且后几行错位；已改四个32px完整区间，两状态一起修正。176/178原普通选项灰字与177/179白字红光选中状态明确保留。菜单标题花饰/暖桃色、店铺粉色属性/金色操作与图标/1、2、3计数保留。字图受限区域与运行时UV分别记录，不声称恢复了所有调用裁剪。

源RGB在alpha0处有删除字/红横线/调试字符，实际不可见，不猜译；保护块和crop hash保留。原图余下低alpha投影/编码边缘不当作新词，真实字芯残留检查和最终原图/新图审看分开保留。修正前预览、mask和审看残留统计只留忽略的本地证据，不覆盖原研究。

## 通用边界与Font底包链

真实188店铺图有17个非重叠文字区域，旧16区域守卫确实拒绝。因此只将每图可编辑区域有界扩为32，33仍拒绝，保护区域仍16，其他512源/512导出/1024层/512成员、像素、hash、对象及未选块约束不变。自写32区域真实包重建fixture验证非选导出和区域外块/padding保持。默认/旧405组像素逐项保持。

新增纹理成员Startup_int必须叠加现有Font候选，不得用原件覆盖字体。MC2Game与Startup_int共82个disc/alias交集的原payload/tiled在Font底包中逐项核对相同；组合器继续验证Font语义、字形覆盖/墨迹、INT及字幕。不为图片汉字重建运行时字库：图片只使用hash锁定Noto字体渲染，未增加INT字形需求。

## 复现与收尾

先按texture计划的original引用和原盘成员hash只读提取缺失的273源资源；现有引用必须hash匹配，不能整盘复制。保持Font base链。首次构建使用全新output-dir，重放用verify-root：

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-294-verification/disc1-texture-bundle
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-294-verification/disc2-texture-bundle
```

本轮全量基线/隔离旧源码1889测试，修改/清洁源码1904测试；保留三阶段命令/输入/字面输出/退出状态、273候选检查点、隔离旧源码回滚和旧197资源测试根回滚证明。现有D1测试目录只显式纳入1个新资源并hash保护刷新，保留原件、配置、存档和runs；不启动游戏，不生成ISO/完整游戏副本。完整证据位于build/phase-294-verification/VERIFICATION.txt。

后续继续UI_Battle语言图、GameStart全屏战败/提示、两张Tutorial语言标题、窄BC3 packed-mip与BC1/Format02完整读写证明、原生未知UI/성쇄；原扫描111项不是全都格式未知，19张raw教程已可被现有atlas解析器读取。其余截图/品牌/按钮不按未译文字数虚报。完整汉化和游戏流程验收尚未完成。
