# 阶段331：DLC 的 STFS 容器

## 已核实输入

用户提供的 `4E4D0811/00000002` 有两个 LIVE 内容包。原文件保持不变；容器工具生成新文件，不原位写入。

| 文件 | 字节数 | SHA256 | 成员 | 数据块 |
| --- | ---: | --- | ---: | ---: |
| `18B8C8A148D63B0BAFE42CF63E203D482BE029C24E` | 76615680 | `059b3f9b2a844f765eab34c4ce886bcbf6e954ab78e6ac5abfeef929d175ec9e` | 7 | 18583 |
| `A6075CF4FC20724B15DA064AB2FCAB16B1CCC3FD4E` | 13340672 | `0a6ca3c0bdd9e5dffa2789a4d60eff216a1f82d0ea7273bf5b97ed9a2658f43f` | 13 | 3226 |

前者是三集短剧包：3个 `Data_ExtraDrama_*.xxx`、3个 `Live_Drama_*.xxx` 和 `spa.bin`。后者是12种特殊武器包：12个角色武器 `.DLC` 和 `spa.bin`。文件名只用于成员身份，文本采用情况另见本阶段汉化记录。

两包均为 title ID `4E4D0811`、content type `2`、metadata version `2`、STFS descriptor version `0`、flags `1`、free block count `0`。所有数据块都由文件表或文件链唯一占有，无重叠或孤立块。完整 SHA1 树、文件链和目录由字节重新核算，而非仅检查魔数。

## 格式与验证

`tools/stfs_package.py` 是独立编写的 Python 读取与重建实现。格式交叉依据为 Xenia 的结构定义及块寻址；上游作者、版本、源码 URL 和 SHA256 固定在 [研究锁](../references/dlc-stfs-research.lock.json)。未将下载的上游源码或完整原游戏数据收入仓库。

| 字段 | 已验证含义 |
| --- | --- |
| `0x32C..0x340` | SHA1，覆盖 `0x344..align_up(header_size,4096)` |
| `0x340` | 大端 header size；实际输入为 `0xAD0E` |
| `0x34C` | 大端 content size，即容器长度减对齐头长度 |
| `0x379` | 36字节 STFS volume descriptor |
| `0x37C` / `0x37E` | 小端文件表块数 / 24位起始逻辑块 |
| `0x381..0x395` | 根哈希表的 SHA1 |
| `0x395` / `0x399` | 大端总逻辑数据块数 / 空闲块数 |
| 对齐头结束 | 两个输入均为 `0xB000`，此处开始存储哈希表和数据块 |

逻辑块为4096字节，每个 L0 表含170条24字节记录；记录保存20字节 SHA1、分配状态及24位后继块。文件表记录为64字节，名称上限40字节，父目录索引大端，分配块数字段小端，文件长度大端。L1 表保存各 L0 表哈希，尾部记录覆盖的数据块数。

**陷阱：** 输入的 header size 为 `0xAD0E`，头摘要却覆盖到 `0xB000`；仅对未对齐头计算摘要会失败。文件名与哈希表包含不同端序，不能一概按大端处理。

首包核验18583个数据摘要、110个 L0 表、1个 L1 表；次包核验3226个数据摘要、19个 L0 表、1个 L1 表。两个根摘要和头摘要全部一致。

## 容器语言槽

原头只有韩文名称/简介槽非空。工具按显式字段编辑，不更改控制台语言：

- `display_name:0` / `description:0`：English 槽，用中文填充以服务当前回退路由。
- `display_name:6` / `description:6`：Korean 槽，替换实际原韩文标题和简介。
- `title_name`：可单独修改的128字节 UTF-16BE 游戏标题槽。

**Verified：** 当前 Xenia Canary 源版本 `48b318a2ad7c36f8f3901a94e290ba70ae0ffec5` 的 `XLanguage::kSChinese` 为17，但 `XContentMetadata` 仍仅有12个语言槽。`display_name`/`description` 将 language-1 得到16，再因超出范围而回退 English 槽0。因此不是写不存在的“槽16”，也不修改用户配置。原始9槽在 `0x411` / `0xD11`，每槽256字节；metadata v2 的3个额外槽位于 `0x541A` / `0x941A`，不能由“简中17”推断它们的绑定。

## 重建约束

- 支持 LIVE/PIRS、metadata2、单哈希表、完整分配的 L0/L1 族，上限28900逻辑数据块。CON、SVOD、双表、空闲/孤立块、L2及未知形态明确报错。
- 修改前必须匹配原容器 SHA256。CLI 的每个替换成员另校验源成员和新成员 SHA256。
- 等长成员修改保留原链、目录及未触及 padding；仅改 metadata 时整个内容区保持逐字节相同。
- 成员长度变化时按原目录顺序重新分配，保留路径、目录关系、标志、时间、未选成员 payload；只更新长度、块号、链、分配计数及摘要。
- 标题 ID、许可证描述符、签名字节、缩略图和未选 metadata 保持。工具不生成发布方 RSA 签名；保留的旧签名不代表对修改内容仍有效。
- 输出重新解析全部摘要和每个成员，与预期值逐字节比较。路径穿越、Windows设备名、重复路径、链环、越界、共享数据块、未知版本及输出覆盖均有防御检查。

```python
from pathlib import Path
from tools.stfs_package import StfsPackage

source = Path("4E4D0811/00000002/18B8C8A148D63B0BAFE42CF63E203D482BE029C24E")
expected = "059b3f9b2a844f765eab34c4ce886bcbf6e954ab78e6ac5abfeef929d175ec9e"
package = StfsPackage.from_path(source, expected)
new_bytes, receipt = package.rebuild(
    {"spa.bin": Path("build/phase-331-dlc/translated-spa.bin").read_bytes()},
    expected_sha256=expected,
    metadata_updates={"display_name:0": "短剧包（全3集）"},
)
# 调用者将 new_bytes 写到新候选路径；原文件不变。
```

示例路径是输入槽，不是已经存在的最终候选；完整本轮构建命令和交付位置以阶段331主记录为准。

## 验证边界

`python -B -X utf8 -m unittest discover -s tests -p test_stfs_package.py -v`：13个测试通过。合成夹具独立顺序构造物理布局，覆盖169/170/171/28900边界、增长/缩短、目录、空文件、多文件表块和防御检查。

实际两包分别进行了等长 `spa.bin` 字节修改，再通过结构重建反向恢复：整容器字节和原 SHA256 精确一致；另验证成员增长和缩短。20个已提取成员与严格解析器读出内容全部一致。证据位于 `build/phase-331-dlc/container/container-acceptance.json`。这些是容器测试夹具，不是汉化内容质量验收；本轮最终译文验证由主构建记录负责。

上述结论是离线容器完整性和重建证据，不代表原主机授权验收或模拟器游戏流程已经运行。
