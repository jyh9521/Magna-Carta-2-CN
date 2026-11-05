# Xenia 补丁中文说明与后处理启用（阶段359）

2026-11-05（Asia/Tokyo）。用户反馈 **60帧已经有效**；这是用户实测反馈，
不是本轮自动测得的帧率。本轮只更新补丁文本、保留现有开关并启用实验后处理项，
不启动游戏或模拟器，不重建 ISO、完整游戏副本或安装器。

## 玩家当前使用状态

现有 `xenia/patches/4E4D0811 - Magna Carta II KOR Graphics Candidates.patch.toml`
已增量更新，不需要另行复制同名补丁。三项分别为：

| 中文名称 | 当前开关 | 含义与验收状态 |
|---|---|---|
| 60帧 | `true`，保留用户设置 | 双刷新间隔变为单刷新间隔；用户已反馈有效，长时间时序／稳定性仍需实测 |
| 光照／阴影异常修复 | `true`，保留用户设置 | **兼容性修复，不是画质增强**；绕过上游指出的 UE3 MSAA 分块渲染异常路径，韩版实际画面待验 |
| 关闭后处理链（实验） | `false → true` | 使用韩版独立实验分支，跳过每视图的后处理代理构建；不是新增后处理，也未证明关闭所有 GPU 效果 |

光照项的上游作者 boma 在 [PR #169](https://github.com/xenia-canary/game-patches/pull/169)
描述的是光照环境下人物／几何出现的错误黑影或着色，采用非分块 MSAA 路径规避，
其中列有 Magnacarta2。因此不能把补丁名称理解为提高阴影分辨率或增强光照。
韩版两个变量及消费者的独立验证见 [阶段358](XENIA_GRAPHICS_OFFLINE_VALIDATION.md)。

后处理使用 `0x8249B3C4: 419A01BC → 480001BC`，走原有空链出口。
该分支已有离线控制流和消费者验证；与美版原补丁的同源／等效关系仍未证明，
实际亮度、色调及其他画面变化应由用户复测，不能从“跳过代理链”推断具体视觉效果。
若要对照，只将第三项 `is_enabled` 改回 `false`，前两项保持原值。
用户下次关闭并重新启动 Xenia、重新加载游戏时读取新补丁；本轮没有代为启动。

## 文本与机器字段的边界

补丁的三个名称、说明、署名说明和 **9行 `#` 注释**均为可读 UTF-8 中文；
`title_name`、`title_id=4E4D0811`、`hash=0FAA852250B131D1`、4个 BE32 地址和值不变。
`title_name` 保持原 ASCII 值以保留既有文件名／manifest 契约。
中文文本存放在 `references/probes/mc2-graphics-offline.json`，通用生成器不硬编码语言。

`tools/runtime_patch.py` 支持计划头部及每个 `patch_sections` 的可选 `comments` 数组；
`tools/runtime_patch_metadata.py` 以版本身份和序列化后的 BE32 分组核对旧补丁，
保留用户开关，再按显式地址启用所选项。CLI 只写新的独立文件，先校验源 SHA256，
拒绝未知字段、写入类型、机器字段差异、已有输出或同路径输出。
guarded write 可以展开为多个 BE32 word，不能仅按每段起始地址匹配。

复用示例（输出必须尚不存在；此命令不部署、不运行游戏）：

```powershell
python tools/runtime_patch_metadata.py refresh build/phase-359-xenia-patch-comments/active.patch.toml --plan references/probes/mc2-graphics-offline.json --sha256 4f3a6965b9ae4a7378bccbc46de3bbc93af179ecab8bb05a3302251369c5c3ca --enable 0x8249b3c4 --output build/phase-359-xenia-patch-comments/reproduced.patch.toml
```

## 默认模板与当前活动文件

源码计划及既有阶段358 bundle 的三项默认仍为 **`false,false,false`**，避免将用户个人设置变成发布默认。
活动文件则是 **`true,true,true`**。既有 bundle 只更新中文 TOML 与 manifest 中该文件的摘要，
原始／修改原生映像和其身份不变。阶段358报告是历史检查点；本轮更新前的精确 TOML 和 manifest
保留于阶段359备份，不把旧记录静默替换为新结果。

| 文件／状态 | SHA256 |
|---|---|
| 活动文件修改前，英文、110 | `4f3a6965b9ae4a7378bccbc46de3bbc93af179ecab8bb05a3302251369c5c3ca` |
| 活动文件修改后，中文、111 | `76e083c2f2f9ffb986fc8c14d99f3bd5a1b5f42286438c76fb4b24357067ddfc` |
| bundle 修改前，英文、000 | `d2bb22f623e575bf61a28ae8fed7fb868393e2316211bad879cd54ed3622e011` |
| bundle 修改后，中文、000 | `f6f1a7817e9a5c179ba132c49336314454abd88711207221d34174527ebee3e5` |

原版 XEX、原生输入、模拟器 EXE、游戏资源、存档及安装器没有被修改。
本轮没有写入模拟器配置；工作期间观察到用户配置的分辨率、后端和窗口尺寸变化，
保留其新状态，不拿早先快照覆盖。起始／当前摘要见 `config-preservation.json`。

## 三态验证与回滚

证据目录为 `build/phase-359-xenia-patch-comments/`。从仓库根目录执行：

```powershell
python build/phase-359-xenia-patch-comments/verify_profile.py build/phase-359-xenia-patch-comments/active.patch.toml
python build/phase-359-xenia-patch-comments/verify_profile.py build/phase-359-xenia-patch-comments/MODIFIED_FILE.patch.toml
& 'C:/Program Files/Git/bin/bash.exe' build/phase-359-xenia-patch-comments/ROLLBACK.sh build/phase-359-xenia-patch-comments/rollback-copy.patch.toml
```

最后一条在隔离修改副本上测试过；目标已恢复原版时再次执行会因摘要不符退出，
需要先以 `MODIFIED_FILE.patch.toml` 重建独立副本才可重测。回滚脚本也仅接受已知活动路径，
不接受任意文件或硬链接。它恢复本轮前的英文110，而不是关闭原先已启用的60帧／光照修复。

| 状态 | 主要字面输出 | 后处理路径 | 退出状态 |
|---|---|---|---:|
| BASELINE | `enabled=110; literal_utf8=false; comments=0; writes=4` | `post=original` | 0 |
| MODIFIED | `enabled=111; literal_utf8=true; comments=9; writes=4` | `post=bypassed` | 0 |
| ROLLBACK（隔离副本） | `enabled=110; literal_utf8=false; comments=0; writes=4` | `post=original`，原SHA恢复 | 0 |

每态214个有界 PPC 片段通过；前两项的 `interval=1; tiling=0/0` 不变。
这些片段在限定解释模型中运行，不是游戏／GPU执行，不替代实际画面验收。
79项相关回归通过，既有 ASCII AF／强制折行 TOML 字节不变；全量干净源码门禁及提交／远端身份见本地收尾记录。

四件交付为 `MODIFIED_FILE.patch.toml`、`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行 `ROLLBACK.sh`。
后两者依赖同目录保留的原始 TOML、`rollback_patch.py`／`verify_profile.py` 及既有原生研究输入，不能单独删除。
`VERIFICATION.txt` 与 `exact-results.json` 保存精确命令、输入路径、字面输出和退出状态；
`native-profile-replays.json` 保存三态片段输入／轨迹，`deployment.json` 保存实际部署身份。
修改文件及活动文件保持中文111，只有隔离副本执行了回滚。
