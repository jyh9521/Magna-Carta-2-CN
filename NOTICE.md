# 来源与许可

## Cooked Font 命名空间研究

EF_ForcedExport 与 uncooked package 名解析参考 Konstantin Nosov 的 MIT UEViewer 固定提交 `a0bfb468d42be831b126632fd8a0ae6b3614f981`；两文件 URL/SHA256 在 references/font-namespace-research.lock.json。与已锁定 Unreal-Library ExportFlags enum 相互核对。Python 审计为独立实现，仅验证命名空间候选与数据等价，不移植游戏 loader，也不声称证明实际加载优先级。

## UI 组件格式研究

组件模板/ClassDefault 路由、版本条件及 LO/HO 标志含义参考 Eliot van Uytfanghe 的 Unreal-Library，固定 MIT 提交 `8236c39b79e30887a487ecf9b018204e430a5ebc`。来源 URL 与六文件 SHA256 见 references/ui-style-research.lock.json，许可原文见 licenses/Unreal-Library-MIT.txt。仅参考格式事实并在当前原始字节上独立验证；本项目 Python 图读取器为独立实现，未集成上游源码、反编译器或运行时。嵌套样式、StateMap 与本作告警链以实际结构验证为准，见 docs/UI_STYLE_GRAPH.md。

## 独立迁移的工具

作者：jyh9521；上游：[MagnaCarta2-Recompiled](https://github.com/jyh9521/MagnaCarta2-Recompiled/tree/bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47)。
固定提交：`bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47`，MIT，版权声明见根目录 LICENSE。

- `tools/coalesced.py` ← `tools/formats/coalesced.py`
- `tools/validate_catalog.py` ← `tools/validators/validate_catalog.py`，扩展保护标记及顺序检查。
- `tests/test_coalesced.py`、`tests/test_catalog.py` ← 上游对应测试，去掉无关双盘比较依赖。

只迁移 Python 标准库工具及合成测试；没有引入 ReXGlue、SDK、PowerPC 生成代码、宿主运行时或游戏资源。
上游 Coalesced 与双盘研究仅作参考，当前资源结果以 docs/RESOURCE_SURVEY.md 和 docs/COALESCED_SURVEY.md 为准。

系列术语只读来源、固定版本与审核边界见 references/series.lock.json、docs/SERIES_TERMS.md。
原版游戏文本与资源不适用工具 MIT 许可；本地解析报告不进入公开仓库。

## UE3 包表工具迁移

`tools/ue3_package.py` 从同一固定上游提交的 `tools/formats/ue3.py` 窄范围迁移；`tests/test_ue3_package.py` 改编自 `tests/test_ue3.py`。保留项目 MIT 版权声明（LICENSE）。移除旧 inventory 协议，增加独立包 SHA256 校验、独占原子输出、解码长度检查和 CLI 测试。

`tools/ue3_fonts.py` 与 `tools/build_coalesced.py` 是本项目新增代码。字体解析参考实际原始字节；现代 Epic UFont 文档只作术语核对，不复制实现。没有分发 LZX 库、字体、纹理或原始游戏数据。

## LZX 与 Xbox 字体纹理

`tools/build_lzx.py`、`tools/lzx_bridge.c` 从上述旧研究 MIT 提交迁移/加固；实际解码代码来自独立固定 `kyz/libmspack` 提交 `55d501976171397ccd5d5a7a1ca7da065b1d9a06`，LGPL-2.1。源码、许可副本、编译日志和动态库均只在本地 build，未把其源码或二进制改称本项目 MIT。`tools/lzx_stored.py` 是独立的格式存储块写入实现，不复制解码器代码。

`tools/ue3_textures.py` 的 Xbox tiling 地址计算改编自 UEViewer，作者 Konstantin Nosov，MIT，固定提交 `a0bfb468d42be831b126632fd8a0ae6b3614f981` 的 Unreal/UnrealMaterial/UnTexture.cpp；完整版权与许可保留在工具文件中。其他纹理布局由实际字节核验，详见 TEXTURE_RESEARCH.md。

最小补字原字体源：Noto Sans CJK SC Regular，notofonts/noto-cjk，Sans2.004 / `523d033d6cb47f4a80c58a35753646f5c3608a78`，SIL OFL 1.1。固定路径/hash 见 references/font-sources.lock.json，完整许可见 licenses/Noto-Sans-CJK-OFL.txt。原始字体只下载到本地 build，不提交字体二进制。生成像素及其衍生字体数据遵循该许可，不覆盖原游戏字体或游戏资源的版权边界。


Additional UE3 metadata format research: Eliot van Uytfanghe / Unreal-Library,
MIT, commit8236c39b79e30887a487ecf9b018204e430a5ebc. UField/UStruct/UScriptStruct/
UProperty/UInterfaceProperty/UEnum source identities are preserved in
references/struct-default-research.lock.json. Independent Python readers only;
no upstream runtime or game assets are integrated.

Additional native-function format research from the same Eliot van Uytfanghe / Unreal-Library MIT commit: UFunction.cs, FieldTokens.cs and OtherTokens.cs; exact identities in references/function-metadata-research.lock.json. Existing locks preserve token/flag maps. Independent Python implementation only; no upstream runtime/source integrated.

Additional scripted-UI token format research from the same Eliot van Uytfanghe / Unreal-Library MIT commit: LetTokens, ContextTokens, JumpTokens, ArrayTokens, FunctionTokens, CastTokens and UnrealTokens. Exact URLs/hashes are in references/scripted-ui-research.lock.json. Independent Python grammar/reference analysis only; no upstream runtime/source integrated.


XEX image format research/public platform key constant: Ben Vanik and Xenia contributors, xenia-project/xenia, BSD-3-Clause, commit95a5c3ee250f80c3b9d139658649d9ffb6db3eec; xex2_info.h and xex_module.cc. Exact source identities are locked in references/xex-image-research.lock.json and upstream license retained in licenses/Xenia-BSD-3-Clause.txt. Independent Python implementation, no emulator/runtime/SDK integrated. Optional PyCryptodome/cryptography backends are external dependencies, not vendored binaries.


PPC native-binding analysis is independently implemented from bounded instruction/profile observations and versioned IBM AIX instruction documentation (URLs in references/native-binding-research.json). No IBM instruction prose, Capstone implementation or emulator runtime is integrated; Capstone5.0.8 was an independent local research cross-check only.

CE/PPC .pdata format research: hedge-dev and contributors / XenonRecomp,
MIT, commitddd128bcca99fe8bfbb99bea583c972351fa6ace, XenonUtils/xbox.h and
XenonRecomp/recompiler.cpp. Exact URLs/hashes are in references/pdata-research.lock.json;
upstream license retained in licenses/XenonRecomp-MIT.md. Independent Python
format reader only; no upstream runtime/SDK or game asset is integrated.

Object-initialization follow-up independently checks counted-branch/zero-fill
patterns and arithmetic interval geometry. Versioned IBM instruction URLs and
their observed availability are retained in references/object-initialization-research.json;
no vendor prose, runtime or Capstone code is integrated. Target reports stay local.

Runtime patch format research: Ben Vanik and Xenia contributors,
xenia-canary/xenia-canary, BSD-3-Clause, commit50e9c715d. PatchDB/Patcher storage-root
lookup, module-hash matching and executable-page mapping were read to validate
the independent runtime bundle/launcher implementation. Exact source identities
are in references/runtime-patch-research.lock.json; no upstream implementation or
emulator binary is committed. The existing Xenia BSD license is retained.

Xbox packed BC texture origin adaptation: Copyright 2022 Ben Vanik / Xenia, BSD-3-Clause, commit28b69c21becd785364bb7c13dfe5b4dd757a8bb3, texture_util.cc GetPackedMipOffset. Source identities in references/texture-layout-research.lock.json; full license in licenses/Xenia-BSD-3-Clause.txt. Existing attributed UEViewer tiled addressing/BC3 codec reused; UEViewer EPixelFormat/DXT1 research corroborates Format5. Only bounded inline single-mip BC1/BC3 production profile integrated; multi-mip/Format2 fixture research is not enabled for patching. No emulator or game asset integrated.
