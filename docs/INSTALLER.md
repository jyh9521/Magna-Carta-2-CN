# 《真名法典2》简体中文汉化补丁（v1.0）

## 当前交付

Windows 10/11 x64 离线单文件图形安装器，Flutter Material Design 3。
直接运行 `MC2-CN-v1.0.exe`；无需另装 Python、Flutter、VC++ 或 ZArchive，也不请求管理员权限。
运行时临时展开内置组件，正常关闭后清理；详细构建、自检和 UI 契约见
[v1.0 发布整理](PHASE_335_RELEASE_POLISH.md)。旧版便携目录仍可作为开发构建输出，不再作为玩家交付入口。
只包含差异补丁和工具，不包含完整原盘、XEX 或 DLC。
新版 LOGO 原样嵌入，保持透明度与比例；所有页面最右下角的「伯翎飞云」
打开 <https://blog.blfy.cc/>。深浅主题、格式分段选择、阶段切换、实际进度、取消、
错误重试、日志、磁盘估算和中断恢复均接入真实后端。
Windows 文件选择和外部链接通过窄 MethodChannel 实现，不依赖额外 Flutter 插件。
版本号不代替游戏全流程验收，模拟器换碟及实机兼容仍按后文逐项确认。

## 输入

| 输入 | 字节数 | SHA256 |
|---|---:|---|
| 韩版 Disc 1 | 7838695424 | `23e96219aa8b2116239c35e6f65013329bfd298d46a726edffa5224498028ac5` |
| 韩版 Disc 2 | 7838695424 | `9497b336d37529fd8ed1d0d64b560b130354fa1d6168fad1dd428e51e8f6bea2` |

Title ID `4E4D0811`；Media ID 分别 `4C23BE53` / `4D4C6B53`；盘号1/2，Disc Count2。
预检查读取 XDVDFS、完整文件目录和 default.xex Execution ID；开始生成前和最终发布前
分别核验完整 ISO SHA256。颠倒、修改过的镜像、未知版本、既有输出、空间不足均中止。
默认包含 DLC，需选择两份原包所在的 `00000002` 目录；也可明确关闭 DLC。
两包原始名字和身份见[阶段331](PHASE_331_DLC_LOCALIZATION.md)。

## 输出与使用

ZAR 输出 `MagnaCarta2_CN_Disc1.zar`、`MagnaCarta2_CN_Disc2.zar`，XEX 输出 `Disc1/default.xex`、
`Disc2/default.xex` 及各自完整目录。均另附按本次格式/DLC选择生成的 `使用说明.txt`、`安装结果.json`，
DLC 输出在 `Content/0000000000000000/4E4D0811/00000002/`。

ZAR 是真实 ZArchive 容器，不是改后缀的 ISO/ZIP；以每盘 XEX 文件树为根。
原 default.xex、盘号、Media ID 和独有资源均保留，不合盘。
压缩器流式读取只读 ISO 区段与改动资源组成的虚拟文件树，不提取第二份完整游戏。
使用 Exzap 原版 writer/reader，验证容器尾部完整性以及所有成员读回摘要。
面向支持 ZArchive 的 Xenia Canary / Edge；具体版本仍需启动实测。
XEX 可在 Xenia 中打开，或复制到 RGH/JTAG 存储；Aurora/Freestyle Dash 应扫描两盘。
本工具不移动存档、不修改配置、不改写原始可执行文件。

DLC 不属于本体树，不嵌入游戏 ZAR。Xenia Canary 可用 **Install Content** 导入
这两包；支持直接 STFS 的构建也可将 `Content` 下的用户子目录合并到配置的
`content_root`。不要替换整个 content_root。RGH/JTAG 合并到 HDD1:/Content/。
STFS 哈希树、Title ID、Content Type、大小和输出摘要均检查；保留原发布方签名字节
不等于重新签名。原版零售主机不作为本次交付目标。
来源：[Canary Quickstart](https://github.com/xenia-canary/xenia-canary/wiki/Quickstart/a34d8c7659bb726c5f5e3450fa84ab120f689ed5)、
[固定内容读取源码](https://github.com/xenia-canary/xenia-canary/blob/48b318a2ad7c36f8f3901a94e290ba70ae0ffec5/src/xenia/emulator.cc)。

## 构建数据流

1. 由原盘与版本化译文/配置构建 comparison packets。当前 Disc1 接续
   [阶段333](PHASE_333_VOICE_LOADING.md)，DLC 接续阶段331；Disc2 接续 v6 packet
   与阶段324/325/328/329/330的哈希绑定资源 journal。中间资源不进入公开源码库。
2. `tools.prepare_installer_sources` 验证所有来源清单和资源摘要，重放 Disc2 journal，
   仅在**原始路径及摘要相同**时采用最新 Disc1 共享资源。每盘独立更新 TOC；
   改动 `.xxx` 经过阶段332 raw runtime-envelope 门禁。本次覆盖441/542项。
3. `tools.build_installer_bundle` 读取完整原盘、变换源、产生 MCD1 差异，逐份独立
   应用核验；相同差异按摘要去重，完整清单列出两盘全部成员。
4. `tools.package_installer` 编译 Flutter、冻结 Python 后端、嵌入可信清单 SHA256、
   带上工具和许可，逐文件校验 ZIP 读回。发布后端不接受运行时替换信任摘要。

准备工具接受 `--spec / --spec-sha256`；差异构建接受 `--recipe / --recipe-sha256`。
本次来源身份见 `references/installer-inputs.lock.json`。重建历史中间结果依照对应阶段
文档；也可直接提供两盘全部候选覆盖项的 recipe，绕过旧 journal 组装。
所有路径由调用者明确传入，不把本机绝对路径硬编码进后端或发布清单。

工具链锁定在 `references/installer-toolchain.lock.json`：Flutter3.47.9、Python3.14.2、
PyInstaller6.22.3、MSVC2022 x64、ZArchive0.1.3、Zstandard1.5.7，libmspack 沿用
`tools.build_lzx` 固定源码。`pubspec.lock` 锁定 Dart 依赖。
ZIP 排序/时间戳固定；PE 时间戳等因素意味着未宣称重编译逐字节相同。

```powershell
# 上游 checkout 必须匹配工具链 lock 的完整提交。
./tools/build_installer_native.ps1 -ZArchiveSource build/upstream/ZArchive-installer `
  -ZstdSource build/upstream/zstd-installer -Output build/installer-native
python -m tools.build_installer_bundle --recipe build/release/recipe.json `
  --recipe-sha256 <已确认的recipe摘要> --output build/release/bundle
python -m tools.package_installer --bundle build/release/bundle `
  --manifest-sha256 <上一步输出摘要> --flutter build/toolchain/flutter `
  --libmspack build/upstream/libmspack-55d501976171397ccd5d5a7a1ca7da065b1d9a06 `
  --zarchive build/upstream/ZArchive-installer --zstd build/upstream/zstd-installer `
  --output dist/MC2-CN-Installer-0.1.0-rc.1-win64 --work build/release/package
```

Recipe 顶层包括 version/title_id/output_name/usage、tools、discs、dlc。
tools 每项包括 file/sha256；discs 两项各含 iso/sha256/resources，resources 每项含
path/file/sha256；dlc 每项含 name/label/source/candidate/sha256/output_sha256。
生产 recipe 必须列出全部改动，不把一项样例误当完整汉化。路径可自行调整，
修改后需确认并重算外层摘要；成员及原件的锁定摘要仍须一致。

`THIRD-PARTY` 保留 Flutter 引擎 notices、Python/PyInstaller、ZArchive/Zstd 许可，
libmspack LGPL 许可及对应完整源码ZIP、桥接源码和替换方法。VC CRT 采用
[应用目录部署](https://learn.microsoft.com/en-us/cpp/windows/choosing-a-deployment-method?view=msvc-170)，不修改全局运行库。

## 事务与恢复

独占 `.install-lock`，在同级 `.mc2-<token>.partial` 中工作。最终输出必须是新目录；
全部读回和输入复核通过后才无覆盖原子发布。取消/异常只清理本任务临时目录，
路径边界、链接和身份检查防止误删。强杀/断电后，在输出页填写同一路径，点
「清理上次中断任务」：只有相同 release/token/output 且旧进程已结束才清理。
日志保存于输出上级 `MC2-Installer-Logs`，预检查诊断另存
`%LOCALAPPDATA%/MC2Installer/logs`；日志可能包含个人路径。
原件始终只读；撤销使用只需处理用户自己生成的输出。之后自行复制到模拟器/主机的
内容不由安装器自动撤回，合并前请保留旧内容备份。

## 验证与待验收

```powershell
python -X utf8 -m unittest discover -s tests -p test_installer.py -q
cd src/installer
../../build/toolchain/flutter/bin/flutter.bat analyze
../../build/toolchain/flutter/bin/flutter.bat test
```

合成双盘/STFS 覆盖 XEX 完整事务、原件只读、DLC、取消、错误版本/顺序/摘要、
空间/冲突、中断恢复、进程保护与发布前输入变化。提供 `MC2_ZAR_TOOL` 时再验证
真实原生 ZAR 往返和损坏拒绝；无原生工具的源码 CI 明确 skip，不冒充游戏实测。
真实输入验收记录双盘 ZAR 全成员读回与两个 DLC 身份；XEX 事务使用合成输入，
现有 Disc1 测试目录保持不变，不另生成 ISO 或完整 XEX 测试副本。

**待人工验收**：新 ZAR 启动、DLC 枚举/三段短剧/武器解锁、实际换碟、旧存档继承、
Edge、RGH/JTAG、Aurora/Freestyle Dash。已有目录版启动记录不能代替这些项目。

复用提示词：
```text
先核对 release-files.json、清单摘要、原盘身份与日志，只修复报告的问题。
保持双盘/DLC独立，不改原件、配置、存档或现有测试副本。增加合成回归，验证
修改、隔离回滚和ZIP身份；游戏实测单列。提交推送并确认远端及全部CI成功后收尾。
```
