# 韩版双盘只读资源调查

日期：2026-10-18。状态：实际 ISO 静态调查完成；未修改原盘、未修改 XEX、未进行游戏内验证。

## 原盘身份（Verified）

| 文件 | 字节数 | 完整 SHA-256 |
|---|---:|---|
| `MagnaCarta II (Korea) (Disc 1).iso` | 7838695424 | `23e96219aa8b2116239c35e6f65013329bfd298d46a726edffa5224498028ac5` |
| `MagnaCarta II (Korea) (Disc 2).iso` | 7838695424 | `9497b336d37529fd8ed1d0d64b560b130354fa1d6168fad1dd428e51e8f6bea2` |

两次独立流式读取所得完整镜像 SHA-256 一致。区域名称来自输入文件名，不据此推断全部实际文本语言。

## 文件系统布局（Verified）

- 分区基址 `0x0FD90000`；卷描述符 ISO 绝对位置 `0x0FDA0000`。
- 扇区为 `0x800` 字节；描述符头、尾各 20 字节为 ASCII `MICROSOFT*XBOX*MEDIA`。
- 描述符相对 `+0x14` 为小端 root sector，`+0x18` 为 root table 长度，两盘分别同为 `1774358` / `2048`。
- 描述符相对 `+0x1C..+0x23` 原始时间戳 D1=`d015fdcf5611ca01`、D2=`50a6efd65611ca01`，保留原始值，不作为版本号。
- 目录项：`left:u16le, right:u16le, sector:u32le, size:u32le, attributes:u8, name_length:u8, name:bytes`。
- 左右树指针以 4 字节为单位，相对本目录表起点；0 表示无子树。根节点相对偏移 0。
- 文件/子目录绝对偏移公式：`partition_base + sector * 2048`。目录属性位 `0x10`。
- 两盘顶层均为 `$SystemUpdate`、`default.xex`、`Engine`、`MC2Game`、`nxeart`。
- 完整树 D1：2016 文件 + 12 目录；D2：2340 文件 + 12 目录。

## 双盘实测对比（Verified）

按完整相同路径比较 1634 个文件，每个文件均读取全部载荷后计算 SHA-256：

- 1631 个完全相同；D1 独有 382 个，D2 独有 706 个。
- 唯一 3 个共享但哈希不同的路径是 `default.xex`、`MC2Game/Config/Xenon/Cooked/Coalesced.ini`、`MC2Game/Xbox360TOC.txt`。
- `.xxx` 包 D1=1912、D2=2233；`.bik` 文件 D1=69、D2=70。
- Localization 中 `.int/.jpn/.kor` 表、全部共享字体/标题包均字节相同。不能因此把两盘 XEX 或配置文件视为可互换。

具体候选资源的绝对偏移、大小、哈希见 `docs/FILEMAP.md`。包内结构、压缩、字体图集与字符覆盖尚未验证；此阶段不声称 `.xxx` 可重建。

## XEX2 只读元数据（Verified）

两盘 `default.xex` 位于 ISO 绝对偏移 `3899768832`，大小 `19611648`；魔数 `XEX2`。
头部数值按大端读取：module flags=`1`，PE data offset=`0x4000`，security info offset=`0xA0`，optional header count=`17`。
optional header key `0x00040006` 指向 XEX 相对 `0x2020` 的 24 字节 execution ID：

| 字段 | D1 | D2 |
|---|---|---|
| Media ID | `4C23BE53` | `4D4C6B53` |
| Title ID | `4E4D0811` | `4E4D0811` |
| Version raw / Base version raw | `00000001` / `00000001` | `00000001` / `00000001` |
| Platform / Executable type | `0` / `0` | `0` / `0` |
| Disc number / Count | `1` / `2` | `2` / `2` |
| Savegame ID | `00000000` | `00000000` |

数值来自头字段，而非已解密/执行后的代码分析；没有修改签名、认证、可执行代码或入口点。

## 可复现工具

Python 3 标准库，无第三方依赖：

```powershell
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --output build/disc1-hashed.json --hash-image --hash-files
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 2).iso" --output build/disc2-hashed.json --hash-image --hash-files
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --output build/disc1-extraction.json --extract MC2Game/Localization/Coalesced.int --extract-dir build/disc1-selected
python -m unittest discover -s tests -p test_disc_inventory.py -v
```

成功清单输出分别是 `files=2016 directories=12 base=0xfd90000` 与 `files=2340 directories=12 base=0xfd90000`，exit=0。选定提取只接受完整清单路径，不做隐含批量提取。所有输出使用新文件创建模式；命令重复运行需选新输出名。已存在的输出不会被覆盖。

工具只以 `rb` 打开输入；校验两端 magic、目录/文件界限、记录长度、重叠记录、重复路径、循环目录/树指针、输出目录逃逸。工具拒绝路径分隔符、冒号、控制字符和点路径。目录表限制 64 MiB、总条目限制 100 万以控制异常输入。当前只支持 ASCII 文件名；未知/非 ASCII 变体报错而非猜编码。该工具不挂载、不执行、不重建或写回镜像。

默认探测基址 `0`、`0xFD90000`、`0x2080000`、`0x18300000`；其他布局可显式传 `--base 0x...`，仍须通过完整描述符校验。多个候选均有效则报错，要求显式选择。

测试夹具完全合成，覆盖读取/提取/哈希、原文件不变、已有输出拒绝、路径逃逸、循环、截断、magic 与边界。原始游戏数据不进入测试或 Git。删除忽略的 `build/` 输出即可撤销只读调查的派生结果，原盘无恢复步骤。
