# 双盘第六版测试 ISO（2026-10-27）

## 用户确认与本轮交付

用户在对话中明确确认“这次图片没问题了，全部通过了！”，随后要求制作第一盘、
第二盘测试 ISO。因此，第六版832张审查图片的**人工图片复审已通过**；这不是
从空白 CSV 推断的通过，也不等同于游戏内验收。本轮不改变任何图片或译文。

本次是用户明确要求的双盘 ISO 交付，覆盖普通迭代不重复制作镜像的默认约定。
原有 `dist/MC2-display-repair-disc1` 测试目录、配置、存档、运行记录与原盘保留。
两盘都从各自原始 ISO 和各自候选资源包构建，不把第一盘内容冒作第二盘。

当前图片计划仍为 `locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json`，
SHA256 `b7407629b4542d48e44a4da25ddeab6181599b2ae5e64ae96a0527d610a358e0`。
纹理原生构建及文本、字体、字幕、TOC 的组合过程沿用阶段322及其上游文档。
候选包是完整 `candidate` 相，而非 `raw-controls` 原文对照相。

| 输入 | 原盘完整 SHA256 | 候选资源清单 SHA256 |
|---|---|---|
| 第一盘 | `23e96219aa8b2116239c35e6f65013329bfd298d46a726edffa5224498028ac5` | `bd1a612858ab1512d86b3242fadaf495069b60bc6ec5006b8f607a5847e0ff2f` |
| 第二盘 | `9497b336d37529fd8ed1d0d64b560b130354fa1d6168fad1dd428e51e8f6bea2` | `afce2b33fc64e7b8d1b91d5950ac7e998ead7fc81edd898576dc0d982da20457` |

两个原盘都为7838695424字节。完整资源清单分别位于
`build/phase-322-review-v6/disc1-comparison-final/manifest.json` 和
`build/phase-322-review-v6/disc2-comparison-final/manifest.json`。

## 可复用构建器与镜像形式

新增通用工具 `tools.build_disc_image`，使用标准库，不硬编码中文数据：

1. 全量核对原盘 SHA256、对应盘号、候选清单 SHA256、每项原始与候选资源身份。
2. 先让既有严格 XDVDFS 读取器验证目录树，再定位目录项的扇区与大小字段。
3. 新建一份 ISO，保留原盘全部字节；候选资源按2048字节对齐追加到原始 EOF 后。
4. 仅改动对应目录项 `+4..+7 sector:u32le`、`+8..+11 size:u32le`。
   不改目录树指针、文件名、卷描述符、XEX 或盘身份；拒绝包中 XEX 替换。
5. 独立重新解析输出，逐文件核对全部内容，包括未改文件；将原始长度内的目录
   字段虚拟还原后计算 SHA256，证明原盘前缀没有其他改动。
6. 生成按字节锁定的清单，包含可逆字段、完整输出 SHA256 和逐文件验证结果。

这是供现有 **Xenia 环境** 使用的测试镜像，保留原盘载荷再追加替换资源，因而
大于原盘；不是重新压缩资源，也没有额外生成整套提取游戏目录。

### 格式依据与证明强度

- **Verified**：本地两盘 XDVDFS 目录结构、所有候选及未改文件的字节身份，
  原盘前缀的精确逆变换，独立回滚输出与原盘的完整 SHA256 一致。
- **源代码支持的高置信推断**：Xenia Canary 将整个镜像映射，文件起点来自
  `game_offset + sector * 2048`，其中 sector/length 使用 `size_t`。
  因而这种保留分区基址、在实际文件范围内重新定位资源的布局符合其读取路径。
  参照 [Xenia Canary DiscImageDevice](https://github.com/xenia-canary/xenia-canary/blob/72c2afa3ba2b1b232f89de71577251d6edafb1bd/src/xenia/vfs/devices/disc_image_device.cc)，
  上游作者为 Xenia Project contributors；上游许可证 BSD-3-Clause。
  本工具为独立实现，没有复制上游源码；源码只用于核对读取契约。
- **尚未实测**：游戏启动、实际画面、剧情推进、存档与换盘行为。本轮不启动游戏，
  不把源代码推断和离线读回升级为游戏验收，也不声明实体主机/刻录盘适配。

## 复现命令

在项目根目录执行。输出文件必须不存在；已有镜像不会被覆盖。
候选包缺失时先按阶段322及对应 locale composition/comparison 计划重建。
文件名变化时可调整路径，但原盘和清单 SHA256 必须仍匹配。

```powershell
python -X utf8 -m unittest discover -s tests -q
python -X utf8 -m tools.compact_outputs --root build --check-space-only
New-Item -ItemType Directory -Path dist/MC2-test-iso-v6
python -X utf8 -m tools.build_disc_image build --image 'MagnaCarta II (Korea) (Disc 1).iso' --image-sha256 23e96219aa8b2116239c35e6f65013329bfd298d46a726edffa5224498028ac5 --packet build/phase-322-review-v6/disc1-comparison-final --packet-sha256 bd1a612858ab1512d86b3242fadaf495069b60bc6ec5006b8f607a5847e0ff2f --disc 1 --output dist/MC2-test-iso-v6/MC2-Disc-1-zh-Hans-test-v6.iso --report dist/MC2-test-iso-v6/disc1-manifest.json
python -X utf8 -m tools.build_disc_image build --image 'MagnaCarta II (Korea) (Disc 2).iso' --image-sha256 9497b336d37529fd8ed1d0d64b560b130354fa1d6168fad1dd428e51e8f6bea2 --packet build/phase-322-review-v6/disc2-comparison-final --packet-sha256 afce2b33fc64e7b8d1b91d5950ac7e998ead7fc81edd898576dc0d982da20457 --disc 2 --output dist/MC2-test-iso-v6/MC2-Disc-2-zh-Hans-test-v6.iso --report dist/MC2-test-iso-v6/disc2-manifest.json
```

独立验证使用相同输入参数，将 `build` 换为 `verify`，并加
`--report-sha256` 和发布时记录的**已信任清单哈希**。不要在怀疑文件被改动时
重新计算新哈希作为信任依据。命令会同时核对原盘、候选资源、输出 ISO、目录
变化和输出清单；状态成功仍保持 `game_started:false` 与
`game_rendering_verified:false`。

回滚只写入显式指定的**另一个新文件**，保留测试 ISO；使用清单中精确的逆向
8字节字段并恢复原始文件长度，最终完整哈希必须等于原盘：

```powershell
python -X utf8 -m tools.build_disc_image restore --modified dist/MC2-test-iso-v6/MC2-Disc-1-zh-Hans-test-v6.iso --report dist/MC2-test-iso-v6/disc1-manifest.json --report-sha256 TRUSTED_REPORT_SHA256 --output build/NEW-disc1-restored.iso
```

本地交付目录另有绑定实际清单哈希的 `ROLLBACK.sh`，参数为盘号和新输出的绝对
路径。该脚本调用本仓库 Python 工具，不是启动器；正常测试只需打开对应 ISO。
两盘原始输入和生成 ISO 均不进入 Git；只提交工具、合成测试和文档。

## 实际交付与验收

输出目录：`dist/MC2-test-iso-v6/`。

- `MC2-Disc-1-zh-Hans-test-v6.iso`：第一盘，2016个文件、12目录，403个替换资源。
- `MC2-Disc-2-zh-Hans-test-v6.iso`：第二盘，2340个文件、12目录，501个替换资源。
- `disc1-manifest.json` / `disc2-manifest.json`：各盘原始/输出身份与每个目录字段。
- `MODIFIED_FILE.json`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`：
  汇总身份、源码差异、三态命令/输出/退出码与可执行回滚入口。

完整本地证据在 `build/phase-323-test-isos/`，交付身份与验证摘要在上述
`VERIFICATION.txt`。本轮隔离回滚的两份原盘一致镜像、干净源码测试目录及源码
ZIP保留在验证目录，清理未执行；它们不混入交付目录。交付目录仅有两个测试
ISO，原盘、既有测试入口及可复现回滚证据均保留。

人工测试时在现有 Xenia 环境中分别打开两盘 ISO，重点检查主菜单/流派树、地图
地名、两张小游戏奖品、教程/字幕以及游戏要求换盘时的衔接。不要以改名方式
替代真实第二盘；两盘各自的 `default.xex`、TOC 与盘身份保持独立。
