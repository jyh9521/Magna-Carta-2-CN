# v1.0 发布整理与界面对齐

## 已实现

- 窗口标题、产品信息及玩家说明首行统一为 `《真名法典2》简体中文汉化补丁`，界面显示 `v1.0`；Windows 数值版本为 `1.0.0.1`。
- 单文件入口内置 Flutter、Python、VC++ 组件、差异补丁和第三方许可/对应源码。运行时在系统临时目录展开，等待 GUI 结束后由引导进程清理；并非把 Flutter 改成不需要运行时的程序。
- `installer_singlefile` 在启动 GUI 前逐项核对内嵌清单及所有文件摘要。`--verify-only --report <新文件>` 运行无窗口自检及冻结后端身份检查；`--extract <新目录>` 可导出完整组件，GUI 帮助页也可打开许可与源码目录。
- 输出玩家说明由语言数据 `src/installer/USAGE.txt` 根据 ZAR/XEX、是否生成 DLC 选择段落，包含打开文件、换碟、DLC、存档备份、更新和移除步骤。工程实现与验收记录留在开发文档，不再塞进玩家说明。

## 游戏 UI：已验证的资源证据

`release-ui-geometry.json` 共 38 项离线契约。原版迭代资源失败 24 项：12 个标题位置、5 个数字控件右端、5 个数字对齐字段、2 个贴图别名边界。当前修改副本全部通过。

1. `UI_Pillar.xxx` 的存档/标题读取场景各有三槽。标题是贴图，不是动态文字。原“游戏时间”可见右端为 828，“SID”为 843；将两者统一为 840：PlayTime_Title 的 X 为 765，SID_Title 的 X 为 794。像素测量来自锁定字体和当前贴图配方；UV、字号、纵坐标不动，12 个动态数值仍保持原有右对齐字段。
2. `MC2Game.xxx` 五个 KanNum 控件的原左对齐造成可见右端随字宽变化。恢复右对齐，并将 36 px 槽改成 26 px，使右端固定于 231，与 A/B 标签右界一致。名字锚点仍为 202；实际一位数间隔 14–17 px，10 为 4 px，99 边界为 3 px。不能同时把独立控件的字间距锁为 3 px、又让不同宽度数字都固定右端；本次采用稳定右边界。119 名称 × 实际 0–10 消耗及 99 边界，共 7140 组合核对溢出及阴影锚点。
3. 商店类别控件取样宽 79 px，框宽 72 px，两者 X 又相差 2 px。只将四行选中背景的作者修复层限定在 X=8..68，并在内部羽化 6 px；字号、字形配方、正常状态及按钮框保持不变。Startup_int / UI_Name_Jpn 两个原生贴图别名同步更新，原生 BC 解码确认框外 alpha 为 0。

字段改动经 `patch_tagged_fields` 校验整对象前后摘要和独立逆操作。纹理经 `build_texture_region_update` 只替换声明矩形中的原生块，未选 export/块保留。新 packet 只包含资源增量并通过外包归一化门禁；不生成新 ISO/完整游戏副本，不启动游戏。离线契约并不等于游戏内最终画面验收。

## 重建入口

```powershell
python -m tools.patch_tagged_fields apply SOURCE --source-sha256 SOURCE_SHA --profile locales/zh-Hans/release-ui-game-fields.json --profile-sha256 PROFILE_SHA --output NEW --report REPORT
python -m tools.audit_ui_geometry --root CANDIDATE --plan locales/zh-Hans/release-ui-geometry.json --report NEW_REPORT
python -m tools.audit_ui_spacing --root FULL_CANDIDATE --plan locales/zh-Hans/gameplay-ui-spacing-release.json --output NEW_REPORT --lzx-library LZX_DLL
python -m tools.prepare_installer_sources --spec references/installer-inputs.lock.json --sha256 SPEC_SHA --output NEW_PREPARED
python -m tools.build_installer_bundle --recipe RECIPE --recipe-sha256 RECIPE_SHA --output NEW_BUNDLE --reuse-bundle PREVIOUS_BUNDLE --reuse-manifest-sha256 PREVIOUS_SHA
python -m tools.package_installer --bundle NEW_BUNDLE --manifest-sha256 MANIFEST_SHA --flutter FLUTTER --libmspack LIBMSPACK --zarchive ZARCHIVE --zstd ZSTD --output INTERNAL_STAGING --work NEW_WORK --single-file dist/MC2-CN-v1.0.exe
```

复用差异块仍核对其完整摘要，并针对本次原始资源独立应用、与目标逐字节比较；不根据文件名跳过验证。两盘仅在原路径与原始摘要相同时共享资源，TOC 分别重建。

临时目录属于当前单文件进程；正常结束自清理。强制杀死引导进程或断电可能留有临时文件，不能据此声称任何退出方式都零残留。

## 玩家步骤的来源

Xenia Canary 的 [官方快速入门](https://github.com/xenia-canary/xenia-canary/wiki/Quickstart) 和 [菜单实现](https://github.com/xenia-canary/xenia-canary/blob/canary_experimental/src/xenia/app/emulator_window.cc) 支持通过 Install Content 安装内容；现版本入口位于 Content 菜单。换碟由 [XamSwapDisc](https://github.com/xenia-canary/xenia-canary/blob/canary_experimental/src/xenia/kernel/xam/xam_content.cc) 请求文件选择，不虚构独立的“Change Disc”菜单。不同分支的具体行为及本作完整换碟流程另行实测。
