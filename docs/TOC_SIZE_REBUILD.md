# Xbox360TOC 首大小字段更新（隔离目录原型）

## 实测范围

**Verified，2026-10-18**：Disc 1 原始 `MC2Game/Xbox360TOC.txt` 大小 197989 字节，SHA-256 为 `04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab`。隔离目录源位于本地忽略输出 `build/poc-game/disc1/MC2Game/Xbox360TOC.txt`。全部 3063 行为 ASCII，行尾均 CRLF；每行匹配：

```text
^(\d+) (\d+) (\d+) (.+) (\d+)$
```

字段依次记为 `size_1 unknown_2 sector_3 path unknown_5`，不为未知字段编造语义。
`MC2Game/Xbox360TOC.txt` 自身的首字段是特殊值 0，不等于文件实际长度；此工具禁止更新所有首字段为 0 的条目，包括该自记录。它不会把自记录“修正”为实际长度。

**Verified**：只在内存中将 `MC2Game/CookedXenon/font.xxx` 的首字段 `1343488` 改成诊断值 `1343489`，仅第 1129 行的首数字跨度发生改变；行余下的 `0 1713195 ..\MC2Game\CookedXenon\font.xxx 0\r\n` 完全保持原样。原始文件重新读取后逐字节未变。该内存诊断输出 SHA-256 为 `f057838a5482b7fce7dcf06e0fdc373229e759c988efd881f8edd018e762895b`；诊断值不是实际字体大小或发布值。

## 工具接口

`tools/update_resource_sizes.py` 使用 Python 标准库。输入是现有 TOC 和完整 SHA-256；变更清单只允许显式列出的资源：

```json
[
  {
    "path": "MC2Game/CookedXenon/font.xxx",
    "expected_size": 1343488,
    "new_size": 1343489
  }
]
```

上述 JSON 同样只是首跨度诊断示例。实际操作必须将 `new_size` 替换为已生成包的真实字节数，并同时核对原包大小。

```powershell
python tools/update_resource_sizes.py build/poc-game/disc1/MC2Game/Xbox360TOC.txt --sha256 04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab --changes build/font-size-changes.json --output build/toc-size-prototype/Xbox360TOC.txt
python -m unittest discover -s tests -p test_update_resource_sizes.py -v
```

工具先校验整个输入哈希和全部行格式，再校验全部目标；全部检查通过才写新输出。不覆盖原 TOC、已存在输出、符号链接或硬链接别名。`--output` 也不得等于变更清单。失败 exit=2；成功打印更新数、输出字节数与 SHA-256，exit=0。

路径只将 `\` 转成 `/`，并去除至多一个开头 `../`；不猜测路径、不改变大小写、不删除其他组件。规范化后按精确路径匹配。任何重复/大小写冲突路径、重复目标、缺失目标、非 ASCII 路径、控制字符、盘符、空组件或中途 `..` 均报错。清单必须是非空数组，各条目恰含 `path`、`expected_size`、`new_size`；大小必须是 1 至 4294967295 的整数，布尔值无效，无变化项报错。`expected_size` 必须等于对应原始首字段。

更新仅替换目标行的首数字跨度。其余数字、空格、路径拼写、行顺序、非目标行、CRLF/LF 及文件尾是否带换行均保留；不自动更新任何未列出的资源。12 项合成测试覆盖首跨度不变式、多目标、哈希、源大小、路径、重复、异常行、零值特殊项、整数类型/范围与覆盖/别名防护；测试不包含游戏载荷。

## 尚未证明的部分

- 此工具是**隔离目录的大小字段原型**，不是 ISO writer；它不写扇区、不重建 XDVDFS、不修改 XEX、不修改字体包。
- `sector_3` 被原样保留；新资源变长时，原 ISO 内扇区布局并不会因此自动变得有效。此输出不能直接当作重建光盘的证据。
- 首字段变化不证明所有次级清单、包内表、缓存、读取上限或校验都已更新；未知字段不动，也不代表未知字段与资源大小无关。
- 原型 TOC 仍需连同生成字体包，在隔离游戏目录中进行实际加载、菜单/字幕显示与字体覆盖验证；尚无运行时或实机验收结论。
- 删除派生输出即可撤销本工具操作；输入原件保持不变。任何后续部署应由另一个明确的复制/备份/回滚步骤负责，本工具不隐式部署。

只提交工具、合成测试和本页；原始/派生 TOC 与游戏包保留在忽略的 `build/` 下。
