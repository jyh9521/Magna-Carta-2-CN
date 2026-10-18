# 文件映射（2026-10-18，实际韩版双盘）

本页仅记录经只读解析/完整 SHA-256 验证的文件元数据；不包含游戏载荷。
偏移均为 **ISO 绝对字节偏移（十进制）**，非 XEX RVA。

| 路径 | Disc 1 偏移 | Disc 2 偏移 | 大小 D1/D2（字节） | 对比 |
|---|---:|---:|---:|---|
| `default.xex` | 3899768832 | 3899768832 | 19611648/19611648 | 不同 |
| `MC2Game/Config/Xenon/Cooked/Coalesced.ini` | 3889137664 | 3889135616 | 131794/131794 | 不同 |
| `MC2Game/Localization/Coalesced.int` | 3886239744 | 3886237696 | 1495972/1495972 | 相同 |
| `MC2Game/Localization/Coalesced.jpn` | 3887736832 | 3887734784 | 1393315/1393315 | 相同 |
| `MC2Game/Localization/Coalesced.kor` | 3889131520 | 3889129472 | 3200/3200 | 相同 |
| `MC2Game/CookedXenon/EngineFonts.xxx` | 3775977472 | 3110195200 | 229376/229376 | 相同 |
| `MC2Game/CookedXenon/font.xxx` | 3774502912 | 3108720640 | 1343488/1343488 | 相同 |
| `MC2Game/CookedXenon/font_ui.xxx` | 3773814784 | 3108032512 | 688128/688128 | 相同 |
| `MC2Game/CookedXenon/Startup_int.xxx` | 3751696384 | 3085914112 | 1769472/1769472 | 相同 |
| `MC2Game/CookedXenon/UI_Title.xxx` | 3976167424 | 4076503040 | 655360/655360 | 相同 |
| `MC2Game/CookedXenon/UI_Title_Jpn.xxx` | 3976822784 | 4077158400 | 655360/655360 | 相同 |
| `MC2Game/Xbox360TOC.txt` | 3889276928 | 3889274880 | 197989/199817 | 不同 |

## SHA-256

- `default.xex`
  - D1: `26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f`
  - D2: `44976b6bf9f978312f14387ea4e60bbdfffd1a8aa72f31841f7a58ab2ebef586`
- `MC2Game/Config/Xenon/Cooked/Coalesced.ini`
  - D1: `6648650d0058f14c4e71a3a97216feb87b9eeee1dda5474fd0b4c415fe2340d3`
  - D2: `8aa52c4af0ef4688ad4978f59af26fae5bade17e18d116871b6011054e6f7257`
- `MC2Game/Localization/Coalesced.int`
  - D1: `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`
  - D2: 与 D1 相同。
- `MC2Game/Localization/Coalesced.jpn`
  - D1: `fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`
  - D2: 与 D1 相同。
- `MC2Game/Localization/Coalesced.kor`
  - D1: `fb51da8543516deb68c728c6da0509073fdebc791a18fa310fdcdf9f9ea9374a`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/EngineFonts.xxx`
  - D1: `49e89e6c91ae4ead4297e10e44c3634e164a651f214c1a6eb3e161e3dd9ae5bc`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/font.xxx`
  - D1: `b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/font_ui.xxx`
  - D1: `5c0629a587b87fa54db57fdd3822fbab33315cc34e747545101505fb9dc1592f`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/Startup_int.xxx`
  - D1: `be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/UI_Title.xxx`
  - D1: `b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4`
  - D2: 与 D1 相同。
- `MC2Game/CookedXenon/UI_Title_Jpn.xxx`
  - D1: `f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595`
  - D2: 与 D1 相同。
- `MC2Game/Xbox360TOC.txt`
  - D1: `04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab`
  - D2: `65a79c3005fa344e4cf5a3c292e92fce73458813ce50ac039ffbd368f5f880f6`

## 候选用途与证据级别

- **Verified**：3 个 Localization/Coalesced 文件存在且两盘完全相同。格式与文本分析见 `docs/COALESCED_SURVEY.md`。
- **Verified**：上述 `.xxx` 开头为 `9e2a83c1`，其后版本字为 `001901be`。
- **High-confidence deduction**：该包头对应大端 UE3 cooked package；低 16 位 446、高 16 位 25 的具体引擎/授权版本语义仍待独立验证。
- **High-confidence deduction**：`font.xxx`、`font_ui.xxx`、`EngineFonts.xxx` 为字体调查优先候选；文件名和包头不证明中文覆盖、字形映射或可重建能力。
- **High-confidence deduction**：`UI_Title.xxx` / `UI_Title_Jpn.xxx` 和 `Startup_int.xxx` 值得用于主菜单最小 PoC 定位；文件名不证明运行时实际加载哪个包。
- **Unverified hypothesis**：标题菜单是低风险首个可见文本切入点；必须先验证实际语言选择、对应条目及字体覆盖，不能仅据 `.kor` 扩展名选择文本来源。
- **Verified**：`Xbox360TOC.txt` 两盘不同；替换资源时必须调查其大小/路径元数据关系，当前工具只读，不负责重建。

完整树和全部文件哈希在本地忽略输出 `build/disc1-hashed.json` / `build/disc2-hashed.json`，可从原盘重建。
