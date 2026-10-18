# 可选 LZX 解码与 Startup_int 元数据（2026-10-18）

## 范围

本轮只增加可选 native LZX 解码器的本地构建和只读 Startup header/table 验证。Python 工具/CI 主测试仍只需标准库，不自动下载或编译 native 库；未引入 ReXGlue、PowerPC 重编译或游戏运行时代码。未改 ISO、XEX 或包，未实现 LZX 压缩/回写，也未声称已完成中文运行或合盘。

## 固定来源与许可

- bridge 来源：jyh9521，[MagnaCarta2-Recompiled 的 lzx_bridge.c](https://github.com/jyh9521/MagnaCarta2-Recompiled/blob/bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47/tools/formats/lzx_bridge.c)，固定 `bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47`，MIT。本项目迁入 bridge 并增加空指针/输出上限检查；构建脚本独立编写，旧 build_lzx.py 仅供构建命令参考。
- 解码器：Stuart Caie，[kyz/libmspack](https://github.com/kyz/libmspack/tree/55d501976171397ccd5d5a7a1ca7da065b1d9a06)，固定 `55d501976171397ccd5d5a7a1ca7da065b1d9a06`。`libmspack/mspack/lzxd.c` 声明 LGPL 2.1，版权 (C) 2003–2023 Stuart Caie；以其 `libmspack/COPYING.LIB` 为准。没有把 LGPL 源码改为 MIT。
- 本地 DLL 由本项目 MIT bridge 与 LGPL libmspack 编译链接，属于含 LGPL 组件的可选产物。第三方代码和二进制仅存忽略的 build/；构建目录保留 COPYING.LIB、固定源码 checkout、构建命令、compiler.log 和 manifest。公开仓库不提交 DLL、OBJ、LIB 或游戏包。未来如发布 adapter 二进制，需另外完成对应源码、修改及可替换/重新链接等适用许可交付；当前不发布 native 二进制。

## 构建与防护

```powershell
python tools/build_lzx.py --output-dir build/lzx/native-verified
```

构建前需要 Git、网络及 MSVC x64 Build Tools（Windows，使用 vswhere/vcvars64）；其他系统使用 `--cc cc` 的 shared-library 路线，该路线尚未在本机实测。源码目录固定为 `build/upstream/libmspack-<commit>`。新目录独占创建后只拉取固定 commit，不 clone 旧重编译仓库；现有目录只读验证 origin、HEAD、clean status 和必要源码，不执行 fetch/reset/checkout。任何不一致明确失败，不覆盖旧树。构建输出必须为本仓库 build/ 内新目录，已有目录直接失败，重试指定新路径。

MSVC batch 对路径中的控制符/命令 metacharacters 拒绝；命令日志使用 UTF-8。首次尝试 native/ 中编译已生成 DLL，但原先 subprocess 默认 CP932 读取中文编译输出发生 UnicodeDecodeError；修正 UTF-8 捕获并在 native-verified/ 全新重建成功。残留的第一次构建不作为验收产物。

**Verified（本机）**：

```text
library: build/lzx/native-verified/ue3_lzx.dll
size: 117760 bytes
sha256: f16a0ef5dcac1f7ee8a9461f0cb02b7c0db06d48482d956a4317b9e285c0ffa1
build exit: 0
```

MSVC 输出不保证不同时间/机器 DLL hash 相同；source/bridge、编译参数、manifest 可复现，不将这个单次 hash 当作跨机器确定性构建承诺。DLL 通过已有 `LzxDecoder` 的 `ue3_lzx(input_ptr,input_size,output_ptr,output_size)` C ABI 读取。窗口位数17，重置间隔0，输入buffer262144，输出长度需精确匹配；Xbox frame stripping 仍由 Python 执行。

## 实际 Startup_int 结果

```powershell
python tools/ue3_package.py build/disc1-font-study/MC2Game/CookedXenon/Startup_int.xxx --sha256 be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3 --output build/startup-research/Startup_int.tables.json --lzx-library build/lzx/native-verified/ue3_lzx.dll
```

**Verified**：命令 exit 0，literal stdout：

```json
{"exports": 4374, "imports": 288, "names": 2593, "sha256": "be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3", "status": "tables-validated"}
```

此前未配置 adapter 时只到 summary-only；现在恢复 409071 字节逻辑 header，并通过现有表、引用、offset、class/path 校验。包 summary 为 flags4、14 chunks；header 恢复仅需覆盖 header 的块，不声称14块全部已解压或对象正文已验证。生成报告只包含元数据，保留本地 build/startup-research/。

选定类型数量：Engine.Font **10**、Engine.Texture2D **130**、Engine.UIStyle_Text **209**、Engine.UIStyle **109**、Engine.UIStyle_Combo **147**、Engine.UIStyle_Image **526**、Engine.UISkin **3**。

Font exports：

- EngineFonts.LargeFont / MediumFont / SmallFont / TinyFont
- Font.EngineMedium_Subtitle / General_15
- font_ui.ItemIconFont_0 / MC2StyleFont_0 / RedNumber / StyleTree_Number_Font

Font imports：font_ui.NormalDamage_font、font_ui.NormalNumber。这些是表中的类和引用，并非已确认某个启动提示使用这些 Font。UIStyle 存在不等于 UIStyle 正文 Font 属性绑定已解析；未解析用户界面本地化正文/字符串定位，未在本任务添加对象 payload 解码。

## 测试与下一步

```powershell
python -m unittest discover -s tests -p test_lzx_build.py -v
```

8 项合成测试覆盖 pin、输出目录边界、Windows shell 字符拒绝、两种 compiler plan、已有 checkout 的只读身份校验、modified/foreign checkout 拒绝、缺失源码、已有输出在下载前拒绝；无网络/native CI 依赖。实际 DLL/header 解码为本机独立验收，不由这些合成测试代替。

下一步可在原件只读前提下研究 Font/UIStyle 对象字段、配置对应关系、Unicode 字形覆盖，以及小规模 UI 实机绑定。游戏内显示/读档/换盘验收仍待进行。
