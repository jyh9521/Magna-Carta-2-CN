# 首个 Logo 停滞：资源包装与光盘目录修正（2026-10-27）

## 现场与证据分级

- **Verified（保留的运行日志）**：用户加载阶段323第一盘测试 ISO 后停在
  BANDAI NAMCO 画面。`xenia.log` 记录主线程 guest `6` 在 `0x82488884`
  发生读取访问违例，地址为 `0x000000013e6ac588`。不是凭截图推断仍在加载。
  日志 SHA256 为 `5018da7d23c0358d5fe07f302965aafd0cd32a418f5867a794794e52529f7ab3`。
- **用户对照结果**：同一 Xenia 打开原版第一盘可以正常进入。此结果由用户报告，
  开发过程没有重新启动模拟器。版本、分辨率、画质、输入与存档配置均未调整。
- **Verified（本地历史运行证据）**：[此前的压缩对照](RUNTIME_TEXT_BINDING.md)
  中，原始包只重编码首块、解压逻辑字节完全不变的 stored-LZX 对照也在
  `0x82488884` 崩溃；同时清除包压缩位、压缩算法和块数量的 raw 外包能够进入
  标题及交互警告。该历史结论不能被第三方解码器的成功往返覆盖。
- **高置信推断**：本轮纹理工具又输出了这类 generated stored-LZX 外包，
  是当前启动故障的主要嫌疑。读取指令是名称映射索引乘8后的解引用；现场
  `r6=be9b53b1` 在候选包中匹配 TitleMap_MSPT 导出表的 GUID 字节，而非合法
  名称索引。尚无调用栈/完整访存轨迹，不能把这一关联当作已定位的全部因果链。
- **Verified（独立布局审计）**：旧 ISO 移动了资源，但 Xbox360TOC 第三列仍
  保存原盘 sector。第一盘403项、第二盘501项不一致，包含 TOC 本身。旧 verifier
  能报告成功，说明验证缺失；是否因此触发本次名称读取异常尚未证明。

REA 拒绝此 PowerPCBE PE 分析映像（unsupported PE architecture）；指令核对
使用本地 Capstone 和既有 SHA 锁定虚拟映像，不冒充 REA 反编译或动态执行。
原始 XEX、翻译值、图片视觉内容均未修改。

## 修正

### 可复用资源归一化

`tools.runtime_package.normalize_package` 仅把与本项目
`wrap_ue3_chunk(decoded_bytes)` **完全相等**的 generated stored-LZX 流作为
修改目标。不能根据 `.xxx` 后缀或单个 magic 猜测压缩内容。

1. 外包出现此类流时，复用 `decompress_copy`，同步清除
   `package_flags & 0x02000000`、`compression_flags` 和 compressed chunk count。
2. 已支持的单 mip BC1/BC3 纹理若包含此类 bulk，改用 raw flag `0`，保留全部
   native tiled bytes，不重新压缩颜色、不重新绘制图片。新导出追加到逻辑 EOF，
   只更新对应 export 的 serial size/offset 和显式 inline bulk 地址。
3. 保留原生压缩流；未知纹理布局不猜测。如果未知布局包含已确认的 generated
   stored 流，则明确失败，不把该资源算成修复成功。
4. 名称/导入表、未选导出及其负载逐字节保持；所有转换对象重新解析并核对
   native tiles。输出再次归一化必须保持原字节。

### ISO/TOC 与事务

`tools.build_disc_image` 新报告 schema 2 采用两阶段布局，最后放置 TOC；第三列
随真实目录 sector 更新，TOC 自身第一列特殊值 `0` 保留。非本盘行、其他列、
原始空格和换行不变。旧 schema 1 的回滚仍可使用，但验证会拒绝陈旧 TOC。

`tools.repair_disc_image` 是已有测试镜像的增量事务：

- `prepare` 锁定上一份完整 ISO 哈希、旧报告哈希及每个候选资源，先生成局部
  修复资源和不可变计划；不写 ISO。
- `apply` 再核完整输入哈希，追加修复资源，刷盘后才改8字节目录字段。
  原有全部载荷保留；不复制整盘、不创建新的完整游戏目录。
- `verify` 独立重读所有文件、TOC 大小/sector 和完整输出哈希；虚拟逆向整段
  旧前缀必须等于上一份 ISO 的完整 SHA256。
- `restore` 只写调用者显式指定的另一个新文件，精确恢复**修复前测试镜像**，
  不是把旧的启动故障宣称为正常运行。原版 ISO 一直保留。
- `recover` 处理追加中断/目录字段部分写入：先验证追加部分是计划字节的前缀、
  目录字节只含已知 before/after 值、逆向旧前缀完整哈希匹配，再还原字段并截断。
  任何第三态冲突均零写拒绝。Python 进程内异常也有自动回退。

## 复现与入口

从仓库根目录执行。每盘用自己的旧报告哈希；输出计划目录必须全新。

```powershell
python -X utf8 -m unittest discover -s tests -q
python -X utf8 -m tools.repair_disc_image prepare --image dist/MC2-test-iso-v6/MC2-Disc-1-zh-Hans-test-v6.iso --previous-report dist/MC2-test-iso-v6/disc1-manifest.json --previous-report-sha256 ea15edd3374f8328b6d29adde76734b1415880b9d27d1e4efd3c7f53c83215d2 --output-dir build/NEW_STARTUP_DISC1 --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -X utf8 -m tools.repair_disc_image apply --image dist/MC2-test-iso-v6/MC2-Disc-1-zh-Hans-test-v6.iso --plan build/NEW_STARTUP_DISC1/plan.json --plan-sha256 TRUSTED_PLAN_SHA256
```

完整实际命令、锁定哈希、字面输出及退出码收录于
`build/phase-324-startup-crash/VERIFICATION.txt`，该记录优先于示例。
第二盘使用自己的 ISO 和清单；不把第一盘的资源身份套到第二盘。
应用后对同一命令把 `apply` 换为 `verify`。显式导出旧镜像使用 `restore` 并加
`--output NEW_ABSOLUTE_PATH`；中断恢复使用 `recover`，不需要额外整盘复制。

以后重新制作测试 ISO，先构建中间镜像，再执行此归一化/TOC检查链路；不要再把
仅通过 libmspack 往返的 stored-LZX 候选直接当作已通过启动的交付。

## 验证与人工测试

聚焦回归覆盖旧 TOC 错误成功、数字位数变化、自身0大小、错盘/哈希/字段冲突、
raw三字段一致性、纹理原生字节保持、幂等、追加异常、掉电中间态恢复及另副本
精确回滚。完整三态和干净源码测试记录保存在上述本地证据目录。

用户继续使用原来的两个 `dist/MC2-test-iso-v6/MC2-Disc-*-zh-Hans-test-v6.iso`
路径。旧 `disc*-manifest.json` 留作上一版身份/逆向证据；当前交付身份以目录内
`MODIFIED_FILE.json`、`SHA256SUMS.txt` 和 `VERIFICATION.txt` 为准。

**尚待用户实测**：第一盘能否越过 Logo、进入主菜单和新游戏；字体/图片显示、
长时间流程、存档和换盘。离线结构/哈希通过不等于这些运行结果已通过。
