# Material 3 Expressive 安装器：独立设计预览

## 本轮问题

先观察安装器采用 Material 3 Expressive 后的实际桌面效果，再决定是否采用。
这是独立、可丢弃的 UI 原型，不替换原安装器，也不接入安装后端。
源码保存在 `codex/installer-expressive-preview` 预览分支，尚无用户选定的方案。

## 体验入口

构建后运行 `dist/MC2-M3E-Preview/MC2ExpressivePreview.exe`，或解压同名 ZIP 后运行。
保留旁边的 `data`、DLL 与第三方 notices。该包没有游戏资源、差异包或 Python 后端。

- **A · 紫藤分栏**：不对称品牌画布、竖向阶段导航、独立任务面板；默认方案。
- **B · 赤陶向导**：大字刊头、横向步骤、宽幅表单；不使用侧栏。
- **C · 青瓷工作台**：紧凑图标导航、中心操作区、持续可见的右侧清单。

底部胶囊箭头和键盘左右键循环切换布局；输入框编辑时左右键保留光标行为。
右上角切换深浅主题。布局与主题切换保留路径、阶段、DLC 和输出格式选择。
命令行 `--variant=A|B|C` 选择启动布局，`--dark` 启动深色主题。
桌面原型用启动参数代替浏览器查询参数，不引入新的网页依赖。

点击「填入演示文件」→「继续」→选择 ZAR / XEX→「预览安装」，可观察进度及完成页面。
处理中可取消，也可查看异常样式、重新演示。所有进度、校验及完成状态都明确标为演示。
文件选择器只返回路径，不读取 ISO / DLC；预览不计算真实空间、不创建输出目录。
「伯翎飞云」保留原项目博客入口。原品牌 LOGO 文件原样使用。

## 设计实现与来源

以 Flutter Material 3 色彩角色为基础，另外设计强调字级、异形花瓣标记、
不对称容器、较大按钮、圆角选择态及阶段切换的 `SpringSimulation` 弹簧动画。
系统要求减少动效时禁用阶段弹簧和过渡。不将 `useMaterial3: true` 本身当作完整 Expressive 实现。

- Google：[Material 3 Expressive 概览](https://m3.material.io/get-started)
- Google Design：[Expressive design research](https://design.google/library/expressive-material-design-google-research)
- Google：[Motion](https://m3.material.io/styles/motion)
- Flutter：[Material 3 migration](https://docs.flutter.dev/release/breaking-changes/material-3-migration)

## 可复现构建

使用 `references/installer-toolchain.lock.json` 固定的 Flutter 提交与原有 Windows 工具链：

```powershell
python -m tools.build_installer_preview `
  --work build/expressive-preview-20261108/package `
  --output dist/MC2-M3E-Preview
```

构建器只复制版本化的安装器源码和独立预览入口到全新工作目录，
只在该副本内更换窗口标题、二进制名和 PE 版本，然后分析、测试并构建。
已有工作目录、输出目录或 ZIP 一律报错，不覆盖。
复制应用目录 MSVC CRT，附带 Flutter / Dart / Material Icons 与项目 notices。
ZIP 固定排序与时间戳、逐项摘要读回；未声称 PE 重编译逐字节相同。
原始 `dist/MC2-CN-v1.0.exe` 在构建前后均核对 SHA256。

开发时也可运行独立入口，不修改 `main.dart`：

```powershell
cd src/installer
../../build/toolchain/flutter/bin/flutter.bat run -d windows -t lib/expressive_preview.dart
../../build/toolchain/flutter/bin/flutter.bat test
```

正式交付请使用上面的隔离构建器，避免复用原安装器的 GUI 构建输出。

## 验证与回滚

已验证的证据由本轮 `build/expressive-preview-20261108/VERIFICATION.txt` 记录；
原安装器源码、LOGO、后端与原 EXE 的基线摘要保存在 `original-hashes.json`。
`DIFF_FILE.diff` 比较原入口与独立入口；`ROLLBACK.sh` 只接受名称及摘要吻合的预览入口副本。
回滚测试在独立源码副本恢复原入口，并执行原安装器六项 widget 测试；交付预览保留新界面。
撤回预览应用只需停止使用独立目录，不涉及现有安装器、配置、存档或测试游戏目录。

本轮没有游戏资源变动，不刷新已有测试资源，不重建 ISO 或完整游戏副本，也不启动游戏。
原型离线测试与桌面截图仅证明界面行为；未视为真实安装、游戏或最终视觉采用验收。

## 清理与提交收尾（2026-11-08）

用户要求清理本地可再生成产物，并推送尚未提交的工作。
清理采用逐目录明确清单，不按整个 `build` 或历史阶段名称删除。
可删除项限于已结束 CI 的源码快照／虚拟环境、两轮已核对成品的 PyInstaller
打包暂存区、独立预览及回滚演练的编译缓存、Flutter widget 测试缓存。
每个 CI 快照先与其 `source-sha256.json` 逐项复核；安装器暂存 EXE 与保留的
`MODIFIED_FILE.exe`、冻结后端与保留的 portable 后端分别核对摘要。

发布安装器、独立预览目录及 ZIP、原盘／DLC、原测试目录、配置／存档／runs、
活动 recipe 的两盘 471／573 项资源及工具依赖、原始基线、回滚脚本和检查日志保留。
删除前检查解析后的绝对路径、重解析点、活动程序和保留资源交叉引用。
本地原版 DLC 目录加入精确的根目录忽略规则，不删除也不加入源码提交。

完整清单、删除日志和保留文件前后摘要放在
`build/cleanup-push-20261108/`。主清单已删除29个缓存目录、123,580个文件，
逻辑大小8,351,148,064字节（7.78 GiB）。统计包含硬链接，不等同于实际释放的磁盘簇；
不把同时运行的其他任务所改变的 C 盘可用空间归因于本次清理。
已删缓存可根据保留的 Git commit、固定工具链、recipe、构建命令与收据重建。

预览源码及说明只提交到 `codex/installer-expressive-preview`，不合并到 `main`。
推送执行原有干净源码／新虚拟环境检查，并独立核对同一提交的四组 GitHub Actions；
具体提交及实际运行结果见本地收尾报告，不提前将待运行的检查写为通过。
