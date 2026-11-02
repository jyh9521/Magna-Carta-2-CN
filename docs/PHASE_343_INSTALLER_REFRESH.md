# 阶段343：v1.0安装器累计修复刷新

## 已核实的问题与改动

截图中的文件虽然名为`MC2-CN-v1.0.exe`，实际外层文件版本仍是`1.0.0.1`；
内置GUI的版本字符串是`1.0.0+1`，两层PE数字版本均为`1.0.0.1`。
读取实际EXE而非旁边的旧bundle后，发现Disc1有131项、Disc2有156项输出摘要
落后于当前源锁，共287项。两项DLC保持最新。

- 当前`references/installer-inputs.lock.json`已绑定阶段342追加v16，接续此前的
  全部布局、动态字库、按钮/信息标签、文字暗带及“世界地图/商店/购买”修正。
- 从该源锁重新准备442/543项资源，与阶段342最终recipe的985项路径/摘要全部相同；
  未重新排字、改字号/位置、改翻译或修改游戏内容。
- 从原盘只读构建并独立应用每个MCD1差异，611份唯一差异去重；保留两盘独立身份与DLC。
- 外层PyInstaller版本资源及内置GUI的文件/产品显示均改成`v1.0`；
  必需的PE四段数字版本统一为`1.0.0.0`，Flutter构建号显式设为0。
- 新增`tools.audit_installer_release`，核验实际嵌入的完整文件集合、大小、摘要，
  清单身份、两盘覆盖项、DLC身份，以及外层/内层PE版本。不是仅检查文件名或源配置。

## 成品身份

| 项目 | 旧版 | 本轮 |
|---|---|---|
| 单文件字节数 | 303487534 | 303499945 |
| 单文件SHA256 | `199481971f8e7b7f21a5ebaaa17bce3023668e1c839882ba152035f353d6f302` | `1a9b0a17c6a93b62d86caeb060b46c4a6f5646f680c299cda6635ab658acf924` |
| 嵌入bundle清单SHA256 | `90633fe2a9bab0b7aa8b12d23c3cd6e64be49491d3425828264fa1e31315ddee` | `e26004a497f4188fc7eacbef71438603b0752046ce8ac5e4f0118d302d5c0645` |

入口保持`dist/MC2-CN-v1.0.exe`。旧版先复制到本轮证据目录并核对摘要，
新单文件在全新目录完成核验后才替换入口。Windows实际VersionInfo读回为`v1.0`，
固定数字字段为1/0/0/0。完整716项内置payload逐项通过。

## 复现与三态验证

构建步骤见[INSTALLER](INSTALLER.md)；工具链仍沿用现有锁，不升级依赖。
必须使用新输出/报告路径。`--reuse-bundle`只节省已有差异计算，不跳过原盘身份、
目标读回及独立应用验证；复用前需核对**从实际旧EXE提取的**清单摘要。
本轮旧工作目录里的bundle并非实际旧EXE的清单，不将二者混用。

```powershell
$e='build/phase-343-installer-refresh'
$recipe="$e/prepared/recipe.json"
$h='24559b8324d3f025bd78cc3532e1e4d879aaba23a1cb11470526f9fdeb3c62b7'
python -B -X utf8 -m tools.audit_installer_release `
  --installer "$e/ORIGINAL_INSTALLER.exe" --recipe $recipe --recipe-sha256 $h `
  --report "$e/baseline-recheck.json"
# RESOURCES=985 DLC=2 FAILURES=289 RESULT=FAIL ; exit 1（287项资源和两层版本）
python -B -X utf8 -m tools.audit_installer_release `
  --installer dist/MC2-CN-v1.0.exe --recipe $recipe --recipe-sha256 $h `
  --report "$e/modified-recheck.json"
# RESOURCES=985 DLC=2 FAILURES=0 RESULT=PASS ; exit 0
& 'C:/Program Files/Git/bin/bash.exe' "$e/ROLLBACK.sh" "$e/rollback-new"
# RESTORED=1 HASHES=PASS
# RESOURCES=985 DLC=2 FAILURES=289 RESULT=FAIL
# ROLLBACK=PASS ORIGINAL_INSTALLER_RESTORED MODIFIED_FILE=UNCHANGED ; exit 0
```

回滚在另一份副本上恢复原安装器的完整摘要、原版本和原287项旧资源，
并再次运行其`--verify-only`确认自身完整性/临时目录清理；当前入口保持修改版。
旧版、修改版、发布后入口各自的原生自检均通过，未启动游戏。
Flutter analyze无问题，6项widget测试通过；安装器源码回归从8项增至12项。
本地完整2794项测试通过（跳过2项）；推送前干净检出与同提交四组Actions结果
以本轮收尾证据为准。

## 清理与保留

只选择两轮打包工作目录、已被保留EXE完整覆盖的便携展开目录、旧EXE差异展开缓存，
以及4轮已成功CI的source/venv。删除前逐文件核验便携树与EXE、CI源码与保存的
source-sha256清单，并核对Git提交仍存在；清单外只允许已知CI生成文件。
删除使用已解析绝对路径边界、重解析点拒绝、文件集合/大小/摘要的二次检查。
CI receipt/日志/源身份、打包日志/清单、旧EXE及独立回滚副本均保留。
推送前实际删除19个目录、61,692个文件，逻辑长度3,248,600,783字节；
C盘同期可用空间增加3,321,729,024字节，二者口径不同，不相加。
本轮推送前检查新生成的source/venv在验证完成后也按相同规则处理，结果另记本地清单。

当前两盘原件、DLC、现有测试目录、runs/配置/存档、活动packet/journal、native工具、
toolchain与本轮release-bundle/prepared均保留。清理后重新准备源锁并核对985项身份，
不以单文件存在替代资源依赖验证。不生成ISO/完整游戏副本，不进行游戏内验收。

本地证据：`build/phase-343-installer-refresh/`中的`MODIFIED_FILE.json`、
`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行`ROLLBACK.sh`，以及命令、日志、
清理计划/结果和哈希表。完整资源不进入Git。
