# UE3 446/25 包表调查（2026-10-18）

## 范围与证据等级

**Verified**：本页仅指本地 Korea Disc 1 提取的五个包的结构解析。工具不改写包、XEX 或 ISO，不读取对象正文作为本报告的内容，不据此宣称中文显示、字体覆盖或换盘成功。四个未压缩包的 names/imports/exports 完整解析；压缩包仅验证 summary，未解压或验证其对象表。

独立工具 `tools/ue3_package.py` 从 MIT 上游 jyh9521/MagnaCarta2-Recompiled 的 `bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47` 中 `tools/formats/ue3.py` 窄范围迁移，保留版权及 NOTICE。未迁入旧 inventory/ISO 调用协议、ReXGlue 或重编译运行时。没有复制其他无许可仓库代码。

## 实际样本

所有包的 serialization profile 均为 **446/25**、大端整数字段。下列 counts 对压缩包只代表 summary 声明值。

| 包 | 文件字节 | header_size | names | imports | exports | 压缩 flags/chunks | 实际解析结果与类 |
|---|---:|---:|---:|---:|---:|---|---|
| EngineFonts.xxx | 229376 | 1454 | 29 | 3 | 9 | 0/0 | tables-validated；Engine.Font 4，Engine.Texture2D 5 |
| font.xxx | 1343488 | 1635 | 27 | 3 | 12 | 0/0 | tables-validated；Engine.Font 2，Engine.Texture2D 10 |
| font_ui.xxx | 688128 | 4168 | 45 | 3 | 40 | 0/0 | tables-validated；Engine.Font 20，Engine.Texture2D 20 |
| Startup_int.xxx | 1769472 | 409071 | 2593 | 288 | 4374 | 4/14 | summary-only；未配置 LZX adapter；类未解析 |
| UI_Title.xxx | 655360 | 8060 | 95 | 4 | 74 | 0/0 | tables-validated；Core.Package 9，Engine.Texture2D 65 |

SHA-256（每次执行必须明确输入，不自动信任文件名）：

```text
EngineFonts.xxx 49e89e6c91ae4ead4297e10e44c3634e164a651f214c1a6eb3e161e3dd9ae5bc
font.xxx        b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6
font_ui.xxx     5c0629a587b87fa54db57fdd3822fbab33315cc34e747545101505fb9dc1592f
Startup_int.xxx be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3
UI_Title.xxx    b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4
```

**Verified**：UI_Title 的 export 表出现 Chapter01 等分组与 Texture2D；这些不是已确认的启动标题菜单或启动登录提示绑定。名字与路径不能代替场景运行证明。上述 Font 类只证明对象类型，不证明字符映射、glyph coverage、实际渲染或 fallback。

## 格式与验证规则

- magic 支持两种端序，版本严格限于 446/25；无静默支持其他 profile。
- summary 包含表数量/逻辑偏移、GUID、generation、engine/cooker version、压缩 flags 与物理/逻辑 chunk 范围。
- name 表 FString 后保留 8 字节 flags 的位置；Xbox 包表 Unicode FString 正文按 UTF-16LE 解读，长度及索引使用包端序。合成测试同时覆盖两种整数端序。
- imports 解析 class_package/class_name/outer/object_name；exports 解析 class/super/outer/archetype、flags、serial_size/offset、components、net counts、GUID。
- 检查字符串终止、引用范围、outer 环、表重叠、header 界限、export serial 范围和压缩块物理范围。输出对象路径、类型路径及表引用边，不推断运行时依赖闭包。
- `package_header(data, summary, decoder)` 仅恢复逻辑 header。flags=4 接受可选 callable decoder；缺失时 CLI 显式输出 summary-only。DLL adapter 必须导出 `int ue3_lzx(input_ptr, input_size, output_ptr, output_size)`，返回 0 表示成功；仅加载用户明确指定的本地可信库，项目不附带该库。本轮未使用或验证该 native adapter。

## 重现

```powershell
python -m unittest discover -s tests -p test_ue3_package.py -v
python tools/ue3_package.py build/disc1-font-study/MC2Game/CookedXenon/EngineFonts.xxx --sha256 49e89e6c91ae4ead4297e10e44c3634e164a651f214c1a6eb3e161e3dd9ae5bc --output build/package-research/EngineFonts.xxx.json
```

其余四包使用同表散列和不同输出路径。CLI 对 hash 不符、输出等于输入、已有输出（含 hardlink/symlink）、结构不匹配报错并返回 1。新 JSON 先写同目录临时文件，再以 exclusive hardlink 原子发布；原件只读，输出已存在时应指定新报告路径，不覆盖。metadata JSON 包含完整 names/imports/export 元数据而不包含对象正文；仍仅留本地忽略的 build/，公开仓库只保留本页摘要与合成测试。

实际五个新报告位于 `build/package-research/<包名>.json`。四个未压缩报告生成成功并校验表；Startup_int 生成 summary-only 报告，CLI 返回 0 仅代表该级别报告生成成功，不代表 tables-validated。

## 待验证

1. 核实可重建的许可合规 LZX adapter 来源，再验证 Startup_int 完整表；当前未将外部工具结果冒充本工具结果。
2. 对 Font 正文独立分析字形映射、metrics、atlas 与字体使用位置；不以表名确认覆盖。
3. 隔离游戏副本内建立启动提示最小变更和原版/修改/回退游戏流程证据；本页解析不代替该验收。
4. 资源回写前研究包偏移、压缩、TOC 与文件大小约束，尚未提供包重封装或安装器。

## 压缩偏移陷阱（本次实测）

**Verified**：Startup_int 的物理 summary_end 为 325；首块物理 offset 为 325，但逻辑 uncompressed_offset 为 101、uncompressed_size 为 786393、compressed_size 为 62798。压缩块目录是物理 summary 的附加表，不应要求逻辑首块 offset ≥ 物理 summary_end；这种混用两套坐标的检查会错误拒绝本次真实样本。工具分别检查物理 compressed_offset 对 summary 的边界、逻辑表/serial 对逻辑长度的边界。该区别仍不构成已解压成功的证据。
