> 以下保留实际写入前的格式研究与建议；本轮已实现的有界写入、显式SHA依赖链和验证结果见 [实际纹理汉化](PHASE_289_TEXTURE_LOCALIZATION.md)。依赖链采用base SHA与已验证font candidate/original精确匹配，不以任意角色覆盖放宽保护。

# 第289阶段：章节纹理三别名的有界写入设计

## 状态与复跑

**Verified / offline**：本研究重新读取当前输入，解析 `MC2Game` export 55740（既有字体候选和先前工作输入两版本），及 `UI_Title` / `UI_Title_Jpn` export 25。三别名的完整解码 tiled BC3 数据一致。研究只执行内存中的 no-op append/repoint、stored-LZX 重封装和重解析，不写包、不运行游戏，也没有新增译文。实际汉化写入、字体语义复核、composition 集成及游戏显示属于父任务。

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python build/phase-289-format-research/probe.py
```

脚本固定四输入和 LZX DLL SHA，结尾重开所有输入检查哈希。结果为 `build/phase-289-format-research/format-probe.json`。此证据只覆盖选中单 mip / Format7 / inline bulk；不扩展到另外 789 个扫描对象。研究依据为本仓库实际源码及已验证输入，而不是泛用 UE3 flag 枚举。[纹理读取器](../tools/ue3_textures.py)、[既有补字写入器](../tools/supplement_font.py)、[stored-LZX 写入器](../tools/lzx_stored.py)、[第288阶段资产审计](PHASE_288_STATE_RECOVERY_AND_PARTY_ADOPTION.md)。

## 精确来源与字段

|输入|SHA256|物理长度|包压缩flags|目标export serial offset / size|table offset|
|---|---|---:|---:|---|---:|
|先前工作 MC2Game|13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641|11632640|4|53366174 / 65914|4548890|
|现用字体 MC2Game 候选|5595562dab1233cbbf7979fff1b9c9ca031707b40f10adf75eb97ec1e999d425|63056621|0|53366174 / 65914|4548890|
|UI_Title|b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4|655360|0|165965 / 10568|4364|
|UI_Title_Jpn|f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595|655360|0|165969 / 10568|4368|

先前工作 MC2Game 指 `build/poc-game/disc1` 中既有工作输入，**不把它称为零售 ISO 的原始资源**；现用字体候选来自 `build/phase-285-verification/route-probe/candidate`，必须在它上面叠加，否则会丢掉现有中文字体。

四输入对应纹理均 512×64，一个 mip，tiled 对齐为 512×128，解压元素数 65536。所有结构字段为 big-endian u32。所有 export 前334字节保留，含 net index 及 tagged properties；`SizeX` / `SizeY` / `Format=7` 不改。

|export相对位置|内容|resident|standalone|
|---:|---|---|---|
|334|SourceArt flags/count/disk/data|0 / 0 / 0 / serial+350|同左|
|350|mip count|1|1|
|354|mip flags|0|0x40|
|358|element count|65536|65536|
|362|size on disk|65536|10190|
|366|absolute data offset|serial+370|serial+370|
|370|payload|raw tiled bytes|UE chunk header+LZX|
|payload后|native SizeX/SizeY|512 /64|512 /64|
|export尾|精确终止|65914|10568|

standalone bulk chunk 的 magic=`0x9e2a83c1`，blocksize=131072，compressed总数10166，uncompressed总数65536，单block compressed=10166 / uncompressed=65536；chunk物理大小10190。**bulk flags0x40是本游戏 LZX 映射**，与包级 compression_flags 是独立层级。来源：[bulk_header / parse_texture_payload](../tools/ue3_textures.py)、[parse_atlas_payload](../tools/supplement_font.py)。

三别名同一像素基础：完整 tiled SHA `418937d6988ab9f586f7bce4e448e4ddba9cb85c66b9efe01a9857f3fc27c5d6`，RGBA SHA `bcc99f39678edcfa2b50fdb86202b3f785bf7c887cdeb37f0f7685730dd508d3`。这不意味着 package 相同或可整包互换。

## 可直接复用的 API 与最小写入过程

1. 对全输入字节执行预期 SHA，`parse_summary(data,len(data))`；`decode_logical(data,summary,decoder)`；`parse_tables(logical,summary,len(logical))`。固定 export 索引同时匹配完整 object path、Engine.Texture2D、payload SHA、尺寸和完整 mip 结构，避免索引漂移。现用 MC2Game 已是 raw package，`decode_logical` 原样返回。
2. `parse_atlas_payload(export_bytes,names,serial_offset)` 同时接受 flag0 /0x40、空SourceArt、单mip；比 `parse_texture_payload` 更适合本组三别名。`atlas_tiles(export_bytes,texture,decoder)` 返回相同65536字节 tiled 缓冲。
3. `untile_dxt5` 得到512×64=32768字节 linear BC3；`decode_dxt5` 得RGBA。不重编码原图的全部BC3，避免原字/装饰劣化。
4. 仅对显式 block-aligned cell 修改RGBA或BC3，用 `scatter_linear_dxt5_cell(old_tiled,width,height,x,y,cw,ch,linear_cell)` 回填。该函数**成对交换16位字节序**并按既有 UEViewer Xenos 地址计算散布；不需要调用者再次交换。所有未选16字节block及physical padding必须精确相同。原函数MIT与上游归属须保留。
5. 在保持单mip/宽高/Format/element_count不变前提下，resident继续保存raw tiled（flag0、disk65536）；standalone继续flag0x40，用 `wrap_ue3_chunk(new_tiled)`。本次相同65536字节经stored writer为65602字节，比原10190大；序列化新export变为65980字节。`compressed_chunk(stored,65536,decoder)` 必须精确返回new_tiled。不要把大小不等的LZX原位覆盖。
6. `new_serial=(len(logical)+3)&~3`，在逻辑末尾对齐append新export，保留旧export所有物理字节。重写 `bulk.size_on_disk_field_offset`（相对362）。**SourceArt即使空，也要重定位其绝对pointer**：相对346写`new_serial+350`；mip相对366写`new_serial+370`。新native宽高跟随新payload，其值保持512/64。
7. 只改目标export table的相对32、36两u32：serial_size、serial_offset。`parse_tables` 重解析必须证明每个非选export整条metadata和实际payload与当前输入相同，且整个原logical前缀除这8字节外完全相同。此条件也覆盖13个Engine.Font对象及它们所有不被选中的atlas Texture2D export。
8. `repack_append_only(data,summary,logical,new_logical)` 可复用：包未压缩则直接输出；包flags4只改第一原header chunk、保留所有其它原压缩chunk，再追加一个新stored chunk；要求export table改动位于第一chunk内，且 `new_logical[first_end:len(logical)]==logical[first_end:]`。重解包比较整个logical，唯一summary差异为chunk_count更新。不要自行把老compressed offsets当logical offsets。
9. TOC从每盘**原始TOC**一次性重算所有最终资源长度，逆操作要求字节恢复原TOC；不可拿字体component的partial TOC再覆盖纹理component TOC。来源：[update_sizes_reversible](../tools/update_resource_sizes.py)、[compose_locale_resources](../tools/compose_locale_resources.py)。

## 当前字体与composition共存

现有 `compose_locale_resources.merge_resources` 及 `prepare` 都明确拒绝resource role重叠；MC2Game同时含字体和目标图片，不应删除检查或简单dict后者覆盖前者。

建议最小通用扩展：增加显式texture component与plan，texture条目记录resource、selected exports、**base_kind和base_sha256**、原始资源SHA、overlay/source SHA、候选SHA、最终size。对共享MC2Game只允许 `base_kind=font-component-candidate` 且base SHA与当前字体component成员精确相等；在该候选上按guarded texture writer重放，产出最终package。其它新增UI_Title、UI_Title_Jpn只允许disc-original base。拒绝大小写碰撞、重复texture资源、font依赖缺失、不同base、隐藏text/subtitle/TOC覆盖。角色集合按最终资源并集建立，独立角色不再做两个随意字典覆盖。

在最终current上继续现有7个Font的 `fingerprint`、literal coverage及`pixel_proof`；更强的追加证据为font component→texture candidate每个非选export metadata/payload完全一致，因此中文字体与atlas字节都没有变化。三个图alias同一替换cell必须比较最终decoded RGBA，不只比较overlay源哈希。UI_Title新增资源要进入控制、候选、rollback、TOC、comparison及hash-guarded live-refresh资源并集；不能只处理原27条列表。

本次 no-op relocation 在字体候选上：新serial63056624，保留83391个非选exports，13个Engine.Font原payload均同hash；两standalone各保留73个非选exports。该结果证明append/repoint机制在当前字体结果上可行，不证明真实覆盖图已正确显示或composition扩展已实现。

## 精确失败门槛与回滚

拒绝未知输入SHA、非Engine.Texture2D、非Format7、非空SourceArt、非单mip、外部bulk、flags非0/0x40、重复对象路径、尺寸/元素数/inline pointer/termination不匹配、非4像素block边界、越界cell、输入overlay不一致、最终三别名像素不一致、非选块或任何非选export变化。负测覆盖每一类，不把测试夹具成功等同于实机。

可逆包恢复采用已有 `build_font_supplement.restore_copy(candidate,control,output,candidate_sha256,original_sha256)`，输出新路径且双hash锁定；在MC2Game中研究/iteration回滚的直接control应为本轮进入纹理写入前的**字体候选**，完整最终comparison回滚才是该盘原资源。两者身份要分列，不能混淆为同一个original。

## 仍未验证

本研究不声称完成中文图的视觉质量、纹理消费者最终加载、采样/缩放/alpha效果、全章节所有图片覆盖或游戏验收。主任务须实际写入并全量复验后再报告新进度；no-op只是格式和保护边界证据。
