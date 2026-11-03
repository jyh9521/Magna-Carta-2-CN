# 阶段356：将截图反馈修复打入用户安装包

2026-11-03，用户明确要求更新安装包，以模拟真实用户的完整安装流程。
阶段354–355仅刷新测试目录；本轮沿用它们已经验证的资源，不重新排字或扩大改动。

## Verified：安装内容已补齐

直接读取旧 `dist/MC2-CN-v1.0.exe`，而非旁边的旧工作目录，确认两盘各有5项输出摘要
落后于当前源锁，共10项：

- `MC2Game/Localization/Coalesced.int`：91处任务通知末尾句号删除
- `MC2Game/CookedXenon/UI_Pillar.xxx`、`TitleMap_MSPT.xxx`：9处存档点的取图/控件高度16→20
- `MC2Game/CookedXenon/MC2Game.xxx`：任务完成标题X271→301、Y−11→−8.5
- `MC2Game/Xbox360TOC.txt`：各盘独立资源索引

两盘原始成员集合及身份、default.xex、DLC、原生工具均保持。
EXP/SID底框与原版相同，本轮没有将其修改成其他背景。

当前源锁重新生成独立recipe，与阶段355的442/543项资源路径及摘要逐项相同。
从实际旧EXE提取差异缓存，按原始数据、目标摘要及变换类型匹配复用；
构建器仍完整核对两个原盘，并对全部MCD1差异独立应用读回，不跳过验证。
生成611份唯一差异，保留2个DLC，单文件完整内置717项payload。

## 成品身份

| 项目 | 旧安装包 | 更新后 |
|---|---|---|
| 字节数 | 303226360 | 303224837 |
| EXE SHA256 | `3d67c6210233e5e4d24aa8e8ecaf3d54c6d94771eeae17293ee1bab801f6d20f` | `bec8a321faf303bb7b7331aa9ef89c3afc731e6f2502930d3662a319d69caea5` |
| 内置manifest SHA256 | `742cc5c552821ea2d2fa5b27789132ff446b1d9c34919a2657c731d19883b909` | `795dde50b63a87b3759a393377e1d05fcd5d8d4cd7237cdab1f399f1a83d4da1` |

入口仍为 `dist/MC2-CN-v1.0.exe`；外层与GUI的显示版本均为v1.0，PE数字版本均为1.0.0.0。
在全新目录完成打包和审计后才替换入口，原包保留独立副本。

## 三态与原生验证

同一recipe SHA256：`a42f67265396e4efccc089ed76b77c385054976a5942351db37d95ce7af98c82`。
构建入口与固定工具链见 [INSTALLER](INSTALLER.md)，本轮没有升级依赖或修改安装器代码。

```powershell
$e='build/phase-356-installer-refresh'
$recipe="$e/prepared/recipe.json"
$hash='a42f67265396e4efccc089ed76b77c385054976a5942351db37d95ce7af98c82'
python -B -X utf8 -m tools.audit_installer_release --installer "$e/ORIGINAL_INSTALLER.exe" --recipe $recipe --recipe-sha256 $hash --report "$e/baseline-recheck.json"
# RESOURCES=985 DLC=2 FAILURES=10 RESULT=FAIL ; exit 1
python -B -X utf8 -m tools.audit_installer_release --installer dist/MC2-CN-v1.0.exe --recipe $recipe --recipe-sha256 $hash --report "$e/modified-recheck.json"
# RESOURCES=985 DLC=2 FAILURES=0 RESULT=PASS ; exit 0
```

隔离副本执行可执行ROLLBACK.sh后恢复旧EXE完整摘要，重新出现同样10项陈旧资源，
且原生 `--verify-only` 自检仍通过。当前入口与MODIFIED_FILE.exe保持更新版。
旧包、新包、发布后入口及回滚副本的原生自检和临时展开目录清理分别验证。
安装器相关Python回归基线/修改后均44项通过（含本地原生ZAR往返），
Flutter analyze无问题，6项widget测试通过。

## 用户复测与保留

双击新安装包，选择原版两盘ISO、按需选择原DLC，再选择一个**新的输出目录**。
请用该次安装生成的ZAR或XEX复测；已经生成的旧游戏输出不会随EXE更新。
本轮未生成完整游戏副本或ISO，未启动游戏；完整安装和游戏内表现由用户复测，
不以资源审计、原生自检或合成事务测试代替该验收。

136项受保护文件摘要保持，涵盖现有测试目录相关资源、入口、runs、存档、配置及源锁。
四项交付证据位于忽略的 `build/phase-356-installer-refresh/`：
`MODIFIED_FILE.exe`、`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行`ROLLBACK.sh`。
原始安装包、隔离回滚副本、差异包、当前recipe与必要来源和报告保留。
仅清理逐文件验证过的本轮便携展开目录和冻结/打包缓存，清单与结果保留；
提交、推送及同提交四组云端测试结果记录在本轮VERIFICATION.txt。
