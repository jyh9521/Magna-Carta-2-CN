# 来源与许可

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
