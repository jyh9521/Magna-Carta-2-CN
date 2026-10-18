# LZX stored-block 编码 PoC（2026-10-18）

## 范围与来源

`tools/lzx_stored.py` 为本项目独立编写的 MIT Python stored-block writer；没有复制 libmspack 的 LGPL 实现代码，也没有 Huffman 压缩器。格式字段依据本地固定 libmspack `55d501976171397ccd5d5a7a1ca7da065b1d9a06` 的 `libmspack/mspack/lzxd.c`（header/block/对齐读取规则）与 `readbits.h`（MSB bit 顺序）核对。可选 native adapter 的源码、构建、许可边界见 `docs/LZX_RESEARCH.md`。libmspack 仍为 LGPL 2.1，不因本项目独立 writer 而变更许可。

用途仅为本地资源最小修改试验：生成可由现有 LZX reader 恢复的流和 UE3 chunk。不是通用压缩器，不处理原游戏完整包的重排，不更新 export serial offsets、package summary、TOC 或资源索引，不改原始输入。不得以此宣称字体替换、Startup 重建或游戏内显示已经成功。

## 字节布局

**Verified（合成流 + pinned native decoder）**：

- LZX stream 首 bit 为 Intel transform flag=0，不做 E8 地址变换；此 bit 只出现在第一帧，后续帧延续同一 stream。
- 每帧一个 type=3（3 bits）未压缩块，接24-bit输出长度。字段按 MSB-first bit 顺序写入 little-endian 16-bit words。
- 首帧 header 共28bits，补4个零到16bit word边界；后续 frame 的 header 共27bits，补5个零。然后是 R0/R1/R2 三个 u32le，均为1。
- raw bytes 原样写入；奇数长度块后补一个零字节，不计入输出长度。
- 每帧输出1..32768 bytes；Xbox frame wrapper 使用 `FF / u16be output_size / u16be input_size`。一帧输入为 raw+16bytes header/R值+可选odd pad，始终小于65536。
- 同一 stream 最多131072 bytes（四帧）；一个 UE3 block 为一个独立 stream，decoder 在 block 之间重新初始化。

最小 golden case：`encode_framed(b'A')`：

```text
ff00010012003010000100000001000000010000004100
```

首 Xbox frame声明 output=1、input=18；总物理23bytes。

## API

```python
from tools.lzx_stored import encode_framed, wrap_ue3_chunk

framed_stream = encode_framed(source_bytes)  # bytes only, length1..131072
physical_chunk = wrap_ue3_chunk(source_bytes)  # bytes only, length1..134217728
```

`wrap_ue3_chunk` 使用 u32be magic `0x9E2A83C1`、block_size `0x20000`、total_compressed、total_uncompressed；其后每个 block 的 u32be compressed/uncompressed 对，最后连接相应 framed streams。末块可短于128KiB；总compressed仅计算各 framed streams，不包含16byte summary及block table。

函数不进行文件写入，输入 immutable bytes 保持不变，重复调用输出一致。空输入、超过上限、非 bytes 输入明确报错；无需 native library 即可生成和运行标准库结构测试。

## 本机 native 验证

使用本地 `build/lzx/native-verified/ue3_lzx.dll`，SHA-256 `f16a0ef5dcac1f7ee8a9461f0cb02b7c0db06d48482d956a4317b9e285c0ffa1`。通过现有 `tools.ue3_package.LzxDecoder` 先去 Xbox frame 再调用 pinned libmspack。每个源为 `bytes((i*131+17)%256 for i in range(size))`。

| 输入字节 | framed物理字节 | native结果 |
|---:|---:|---|
| 1 | 23 | exact match |
| 2 | 23 | exact match |
| 32767 | 32789 | exact match |
| 32768 | 32789 | exact match |
| 32769 | 32812 | exact match |
| 131072 | 131156 | exact match |

另外131073、262145字节经过 `wrap_ue3_chunk` 后逐block native解码，连接输出与源逐字节一致。报告 `build/lzx-stored-research/roundtrip.json` 仅含合成源大小、散列及match结果；没有游戏数据或原版资产。

重现：

```powershell
python -m unittest discover -s tests -p test_lzx_stored.py -v
$env:MC2_LZX_LIBRARY = (Resolve-Path build/lzx/native-verified/ue3_lzx.dll).Path
python -m unittest discover -s tests -p test_lzx_stored.py -v
Remove-Item Env:MC2_LZX_LIBRARY
```

第一组输出 `Ran 7 tests ... OK (skipped=1)`，exit0；第二组 `Ran 7 tests ... OK`，exit0。6项标准库测试使用独立test-only stored parser核对字段和还原内容，包含golden、帧边界、奇偶对齐、多个UE3blocks、输入保护和确定性；native测试显式opt-in，不作为默认CI依赖。纯Python parser测试不单独冒充第三方decoder兼容证据。

## 风险与后续

**Verified**：stored输出比原文更大，而不是压缩收益；原始资源slot很可能放不下，需要由独立包布局工具处理大小/偏移/文件结构变化，禁止盲目覆盖原slot。

**Unverified hypothesis**：Xbox 360 游戏的LZX解码路径可能接受该合法stored子集；本轮只在 pinned libmspack 中验证，尚未通过Xenia加载或原生Xbox运行。游戏对帧、chunk大小、压缩标记、内存占用和资源载入时序可能存在额外约束。

因此下阶段必须先做隔离副本、包结构再解析、原件hash保护、回退验证，再进入游戏场景验收。Font atlas/字符映射改变与Startup压缩块再封装分别验证，未取得游戏内证据前不宣称显示成功。
