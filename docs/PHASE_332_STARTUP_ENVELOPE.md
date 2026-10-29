# 阶段332：目录版 Logo 后黑屏与最终资源外包检查

## 现场与判断边界

- **已验证（用户运行日志）**：中文入口及中文无DLC入口均在 guest PC
  `0x82DF5E90` 发生读取违例，地址 `0x0000000100000034`。
  原文对照由用户确认可以进入标题及游戏。缺少档案并不是独立充分解释：
  有、无档案的失败日志具有相同PC。配置、可执行文件、存档未作为修复目标。
- **已验证（源映像静态核对）**：指令为 `lwz r4,0x34(r30)`，日志中r30为0。
  前序对象查找结果传到r30，随后读取对象的类字段。
  包装函数指针 `0x823191D0` 对应原映像注册名
  `intAMC2GameInfoexecSpawnArchetypeActor`，通过虚表槽0x38C调用该实现。
  日志没有保存模板字符串或完整调用栈，不声称知道失败的具体角色名。
- **已验证（实际目录资源）**：403个修改UE3包、835,879个导出与原文对照相比，
  没有Actor、模板、脚本载荷、名称表或对象引用变更。Coalesced没有修改资源路径。
  所有实际存在的TOC条目尺寸正确。逻辑字节检查本身没有覆盖物理压缩兼容性。
- **已验证（缺失的交付步骤）**：350个包包含本项目写出的700个stored-LZX外包块；
  另19个包包含590个同类纹理bulk。目录比较/增量刷新没有调用阶段324的既有归一化器。
  部分包在阶段325后的packet中已存在，并非这次DLC翻译引入。
  `raw_package_outputs`旧字段描述raw-controls阶段，不应误读为所有candidate已归一化。
- **高置信解释**：恢复曾经实测兼容的raw资源外包，避免动态加载模板包失败。
  既有stored-LZX首块对照历史见[阶段324](PHASE_324_STARTUP_CRASH.md)。
  当前四份失败日志与旧PC不同；未证明每一个压缩块都必然导致崩溃。

## 修正与可复用流程

`tools.normalize_runtime_comparison` 从可信manifest摘要读取现有comparison packet。
仅处理与原始摘要不同的UE3 `.xxx`，使用原有 `runtime_package.normalize_package`：

1. 仅识别与本项目writer完全一致的stored-LZX流；原生压缩流不凭magic猜测。
2. 生成raw外包，同时清除package压缩位、算法与块表；纹理bulk改为raw，
   原生tile字节、对象身份及所有未选载荷保持。不是重绘图片或重新编码颜色。
3. 已经raw但末尾未对齐的包仅追加零字节，保留整个输入前缀。
   当前4个为Engine、MC2Game、Startup_int、font；32KiB为该Xenon交付profile，
   不是通用UE3规则，也不是已证明的唯一崩溃原因。
4. 用现有 `compose_incremental_comparison` 生成新资源视图和TOC尺寸。
   不生成ISO或完整游戏副本，不改变raw-controls、译文、字体像素、DLC或原件。
5. 对既有测试目录执行hash-guarded刷新，保存本轮逆向journal。

```powershell
python -X utf8 -m tools.normalize_runtime_comparison audit `
  --packet-root OLD_PACKET --manifest-sha256 OLD_MANIFEST_SHA256 `
  --toc-path MC2Game/Xbox360TOC.txt --output-dir NEW_AUDIT_DIRECTORY `
  --lzx-dll build/lzx/native-verified/ue3_lzx.dll
python -X utf8 -m tools.normalize_runtime_comparison build `
  --packet-root OLD_PACKET --manifest-sha256 OLD_MANIFEST_SHA256 `
  --toc-path MC2Game/Xbox360TOC.txt --output-dir NEW_BUILD_DIRECTORY `
  --lzx-dll build/lzx/native-verified/ue3_lzx.dll
```

audit退出1表示需要归一化；退出2表示输入/格式错误。build输出`packet/`，
再按BUILDING的增量刷新流程使用该packet摘要。已规范的输入返回无变化结果。
工具输出目录必须全新，输入哈希必须明确，干净源码和用户提供的锁定资源可重建。

## 最后一层交付防线

`runtime_envelope.require_raw_envelope` 是不依赖原生LZX解码器的最终profile检查：
大端446/25、raw外包三字段一致、32KiB对齐，并检查**当前活跃Texture2D导出**内
是否还包含本项目writer的精确stored-LZX流。不会把归一化后留在死区的旧载荷误报。
识别器逐块/逐帧核对长度、Intel/type/对齐位、repeat-offset初值和重新编码字节；
不是搜索单个magic就判坏。非identical原生流保持原状。

`verify_resource_phase --runtime-envelope` 分开报告“摘要一致”和“外包通过”。
匹配441个哈希但外包失败时仍返回1。中文CMD自动启用此检查；原文对照不使用
生成包profile。prepare/refresh在复制或备份前检查新候选，拒绝再次交付不合格包。
既有坏packet仍可用字节检查模式作为修复输入，不能把它当作启动通过。

## 本次数据与证据

补充I/O排查固定在Xenia Canary提交`48b318a2ad7c36f8f3901a94e290ba70ae0ffec5`，
作者为Xenia/Canary contributors，许可沿用NOTICE与保留的BSD-3-Clause文本。
[HostPathFile](https://github.com/xenia-canary/xenia-canary/blob/48b318a2ad7c36f8f3901a94e290ba70ae0ffec5/src/xenia/vfs/devices/host_path_file.cc)
及[DiscImageFile](https://github.com/xenia-canary/xenia-canary/blob/48b318a2ad7c36f8f3901a94e290ba70ae0ffec5/src/xenia/vfs/devices/disc_image_file.cc)
都不自动填充EOF后字节；普通跨EOF读取返回实际数量，Scatter循环下一页到EOF时可以
返回EOF。真实Win32合成短读试验确认123字节短读/零填充后完整32768字节的差别。
没有游戏具体读调用轨迹，**不把这项机制当作尾部对齐导致当前崩溃的证明**。
源文件逐一比对Git blob，锁见`references/startup-io-research.lock.json`；未移植上游代码。

本地证据根：`build/phase-332-startup-black/`。包含原日志快照及摘要、native反汇编、
全量资源/物理头/路径对照、Win32普通/Scatter短读试验、基线和修改测试、独立回滚、
实际命令与输出。完整日志和原游戏资源不进入Git。

当前修正为369个归一化包加4个纯尾部补齐包；新增视图仍含441项资源，TOC随尺寸更新。
字体、数字比例、换行、菜单与DLC翻译不回退。回滚试验在另一资源副本上恢复旧摘要，
其结果应重新出现外包检查失败；这不是把旧黑屏状态描述为正常运行。

**用户已确认当前中文入口可以越过Logo进入标题和游戏（2026-10-30）。**
本次入口保留DLC绑定；DLC自身内容、全游戏视觉及流程验收仍与启动分开。
