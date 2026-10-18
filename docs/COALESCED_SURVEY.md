# Coalesced 当前镜像实测（2026-10-18）

**Verified：** 当前两张 ISO 只读提取的 8 个容器全部 parse → serialize 与输入逐字节一致。未回写镜像、未部署、未进行游戏内中文验收。

|盘|资源|大小|SHA-256|嵌入文档|候选值|opaque 文档|
|---|---|---:|---|---:|---:|---:|
|1|MC2Game/Config/Xenon/Cooked/Coalesced.ini|131794|`6648650d0058f14c4e71a3a97216feb87b9eeee1dda5474fd0b4c415fe2340d3`|12|2455|1|
|1|MC2Game/Localization/Coalesced.int|1495972|`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`|39|18176|1|
|1|MC2Game/Localization/Coalesced.jpn|1393315|`fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`|40|17642|0|
|1|MC2Game/Localization/Coalesced.kor|3200|`fb51da8543516deb68c728c6da0509073fdebc791a18fa310fdcdf9f9ea9374a`|2|83|0|
|2|MC2Game/Config/Xenon/Cooked/Coalesced.ini|131794|`8aa52c4af0ef4688ad4978f59af26fae5bade17e18d116871b6011054e6f7257`|12|2455|1|
|2|MC2Game/Localization/Coalesced.int|1495972|`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`|39|18176|1|
|2|MC2Game/Localization/Coalesced.jpn|1393315|`fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`|40|17642|0|
|2|MC2Game/Localization/Coalesced.kor|3200|`fb51da8543516deb68c728c6da0509073fdebc791a18fa310fdcdf9f9ea9374a`|2|83|0|

每盘本地化 int/jpn/kor 合计 35901 个物理行 INI 值候选；含配置 ini 合计 38356。这不是可见剧情条数：含引擎编辑器、调试、标识符、数值等。

## 格式（Verified）

- 文件头大端 signed int32 字符串数，随后 path/content 成对；计数为偶数。
- 正长度：含单 NUL 的字节数；负长度：含双 NUL 的 UTF-16 code units；宽载荷为 **UTF-16LE**，不是 UTF-16BE。
- 窄串 ASCII/严格 UTF-8；其余按 opaque-8bit 可逆保留且不进入候选目录，实际编码仍未知。
- 嵌入路径含 `..\`，提取器只输出 JSON，不将其当宿主写出路径。
- 稳定 ID 包含资源路径、嵌入路径、section/key/重复 occurrence；source hash 独立标识版本；不会合并跨盘或跨语言资源。
- 控制码、原始空白、行尾保留于 document；INI 行候选只解析物理行，不解释多行、宏或数组语义。

## 最小实验候选与边界

首选定位候选：`MC2Game/Localization/Coalesced.int` → `..\MC2Game\Localization\INT\MC2UI_TCR.int` → `[GameStart] LogIn_NewGame`。它是启动未登录提示，文本含 literal `\n`；比编辑器的 NewGame 字段更接近可重复启动路径，但运行时实际绑定尚未确认。先验证触发与字体，再决定正式试译。

备选短文本：`MC2UI.int` → `[Help] Start`（原值韩文，主菜单帮助）。它在 KOR 另有不同值，不能只改某个后缀就声称运行时会使用。

标题菜单可能来自 `UI_Title.xxx`；目前只有资源候选与头部标识，不能确认标题屏幕具体字符串。`MC2FieldName.int [Title] Title` 也不能直接当作主菜单。

字体 atlas、glyph map、metrics、覆盖与真实 UI 绑定未解析；Coalesced 的 UTF-16LE 字符串可序列化不证明中文能够显示。

## 复现

按 BUILDING.md 提取到 build/disc1-selected 后：

```powershell
python -m tools.coalesced "build/disc1-selected/MC2Game/Localization/Coalesced.int" --sha256 179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c --resource MC2Game/Localization/Coalesced.int --output build/coalesced/disc1/Coalesced.int.json
```

JSON 保存来源 hash、完整嵌入文档、原文候选与编码。它含原版文字，只留本地 build，不提交。回写 CLI / archive rebuild / Xbox360TOC 更新尚未实现；serialize 仅为内存容器实验接口。
