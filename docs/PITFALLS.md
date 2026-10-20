## 源基线需求与普通字形生成布局门禁（2026-10-20）

Verified / offline：累计2451码点以三族原始基线核算，可绘制新增2389/2388/2389；未映射U+3000单列布局需求，不删除或伪画。SmallFont空remap实际是受支持的256-glyph identity conversion，不能当零覆盖。透明字修复1/0/5纳入新增集合，不重复计数。
通用prepare_text_sample.classify_font_demand提前区分可绘制/布局控制/BMP外；普通生成明确遇到U+3000即停止，无资源或计划目录输出。原glyph_limit2048和单atlas高度2048合同未放宽；三族当前宽度与模板在最大高度也分配失败，非引擎上限证明。详见PHASE_121_FONT_DEMAND_GATES。

## 跨容器同payload与补零尺寸反证（2026-10-20）

Verified / 仓库工具静态字节：extraction-profile八份源hash均匹配。两盘INT/MC2Game.int和JPN/MC2Game.jpn的去终止符宽payload均390字节/hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7，11候选相对偏移相同；JPN内容头偏移801126，INT895017。另四份INI/KOR零候选，不借JPN同key当修复原稿。
给每个0D 0A 00候选增加一个零字节的统一假设导致390+11=401奇数；这不是完整UTF16字节长度。只读工具只报告尺寸，不生成修复字节；偶数也不代表语义/边界正确。统一UTF16BE虽能解码，所获四个键仍有乱码前缀、section均空，不能认定端序翻转修复。原生产提取ID/值和所有held不变。
原名扫描仅覆盖selected中不大于32MiB的文件，发现两份INT容器自出现；不是压缩/完整包的引用分析，不证明孤立笑声不存在运行引用。详见PHASE_118_BOUNDARY_COMPARISON。

## MC2Game.int宽字符串边界只读观察（2026-10-20）

Verified / bytes：源INT容器179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c双盘相同；MC2Game.int宽内容长度字段偏移895017，payload895021，去终止符390字节，hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7。
通用审计报告11处0D 0A 00候选，payload相对偏移28/59/92/143/146/165/194/235/264/269/288，奇偶交替。容器按现行解析/序列化仍逐字节往返；这不证明内部INI语义正确。
Unverified：是否源生成器漏字节、不同换行序列混接、运行时如何读取；不能仅凭模式断言整段改用另一端序。模式亦可能来自合法U+0A0D，工具只观察，不修复/改ID/重划section。原三条提取值保持源hash不变；详见PHASE_117_REMAINDER_AUDIT。

## 第113批支援源形态（2026-10-20）

Verified：MC2_com_Celestin.int/Argo/Overheat_ch3_01实际有两个不同源值的occurrence，稳定ID分别以50cd57ee与f7b2b3b4开头；不能以document/section/key建字典覆盖，两个值独立回填。
MC2_com_Zephi.int/Celestin/Abnormal_bad_ch3_01源含未知反斜线\じっと，整条held，不猜缺n；同表Rue/Abnormal_bad_ch3_01最后停在私がすぐに，未完句完整held，不由动作key补治疗承诺。
长音ー/ぉ不自动变成全角～；只保留源已有63处～。四处U+3000、两处tab、485个字面\n及阿尔戈呼唤中ASCII空格按源保留。不同状态key下源相同仍保留独立ID，不按状态修台词。
com/communi名称不能证明表之间对应关系；下一阶段communi_Argo实际韩文，Crocell混有日文/空白，Zephi与Zephie双表分别保留。运行触发/配音字幕用途与新术语官方身份均未验证。

## 邮件主题、菜单标签和支援反斜线不能按规律猜改（2026-10-20）

Verified / source：E02_002的key沿用E02_001_Sub/Con，section/稳定ID区分，不按数字修；E02_016省略号主题和Test더미原值held，正文单独翻译。初期化须核对既有UI译名初始化，不凭常用说法新造重置。
Argo全角１保留，HP_30等key不能替代源对白补数值。后续Zephi的セレスティン\じっと未知反斜线不因其余行分段规律就补n，完整源值/hash待查。E09壁/B02门及Q02_004爆裂拳/锤的词面差异各依源，不用印象纠错。见BATCH_112_MAIL_SUPPORT.md。

## 相似尾声状态和祭坛key不能代替源值比较（2026-10-20）

Verified / source：五角色Ch12_00_14与Ch13_00_05逐字源相同，但塞蕾丝汀两句不同，必须比较原值后复用，不以同结构key复制。两个状态的稳定ID仍独立保留。
King_token_water名홍련与说明水祭坛分开，fire名파계有限参考JPN破戒而非按效果猜破界；JPN紅煉不能认定INT的홍련已核汉字。北部军/南部军和英文物品key均不可用来静默纠错实际源。见BATCH_111_LATE_COMMENTS.md。

## 场景进度超出分母也不能静默纠错（2026-10-20）

Verified / source：开篇绷带治疗计数存在4 / 3与5 / 3，不能按常见任务上限改成3 / 3；数值、斜线两侧空格和对应稳定ID各自保持。香水提示的左右/相邻/两端关系不因直觉改成解答。
Chapter00–03的29纯省略号完整held，不把标点替换算新增；PartyTalk同key跨角色用section/ID区分。阿巴泽特须查既有共享候选，不凭熟悉拼写新译为阿巴杰特；本批只改尚未提交的新草稿，旧译保持，初次术语审读证据保留。见BATCH_110_OPENING_COMMENTS.md。

## 类别与功能尾换行也可能无需翻译变化（2026-10-20）

Verified / source：606_katana_S为刀加功能尾换行，候选完全相同；格式检查拒绝unchanged source。保留原值并held，不加空格或改太刀绕过，不从邻近武器补属性。第109批162候选新增155，另六缺防御值字段也完整held。
已知类别+空行的韩文源仍可按实际词面翻译并保留空行；中文兼容源仅未变化不计新增。两种情况分别核对，不按英文key把短刀/刀统一。初次失败计划与日志保留研究证据，见BATCH_109_CELESTIN_RUE_EQUIPMENT.md。

## 无需变化的装备源名不应伪造译文差异（2026-10-20）

Verified / source：424_fireball源名毒炎球与中文候选字面相同，初次格式验证按既有规则拒绝unchanged source is not a translation；改为保留原值并独立held，不追加空格或换字凑已译量。其空白S也保留，D有意义则单独draft。
第108批194候选因此新增184而非185；另8个缺数值字段完整held，不部分翻译或从日文猜补。初次失败计划/日志保存在本地研究证据；309斧全述加号后空格与简述不同，不自动修齐。见BATCH_108_ARGO_CROCELL_EQUIPMENT.md。

## 装备防御+缺数值不是可补齐的规律（2026-10-20）

Verified / source：朱特148/151肩甲D/S以방어+结束，四字段完整保留held；名称可解释不表示残缺说明可部分翻译，不按邻近装备数列补数。其他已知类别的尾空行/单空格保持，不从JPN或英文key补属性。
150_pauldron源为青铜护手/副装备且S末尾有制表符；129_sword源为暫魂剣而非斬魂剣。不按资源key或常见命名纠正源名，翻译候选及实际机制置信度分开记录。见BATCH_107_JUTO_ZEPHIE_EQUIPMENT.md。

## 饰品数字相同的旧式key不是同一源值（2026-10-20）

Verified / source：1233_Accessory_D/S防御+30%与1233_acc_D/S+10%不同；1263_Accessory_D/S攻击+30速度+10与1263_acc_D/S睡眠免疫不同；1337两种key也分别保留，未经验证不删旧式资源。
不可按数字或同名将ID归并，不按配方排序推定对应饰品。短/长描述的功能换行、技能点数条件、免疫范围和冻疮/寒冷/冻伤词面差异不自动修齐。资源差异不证明实际使用情况，见BATCH_105_ACCESSORIES.md。

## 配方反斜线不是可猜补的换行（2026-10-20）

Verified / source：INT MC2Item/Recipe/1458_recipe_D包含`\공격`，没有已知的字面`\n`转义；稳定ID以bd69e92a开头，源SHA256为d5f4c0687af9e30bc270768e9d203eec9782e23a369a0d3e517a6a90131fa765。
不因其他配方D字段分两行就补n，或借机把攻击/抗性材料改成简述的攻击/速度；原值保持，未知格式独立留待研究。
第104批只给名称/简述有源依据的draft，D字段held不计已译；全角ＬＶ/（）及各字段数值/空白继续锁定。详见BATCH_104_CRAFTING.md。

## 研究所钥匙与通行卡同key的两个occurrence（2026-10-20）

Verified / source：INT/MC2Item/Valuables的key_laboratory及key_laboratory_D各有两次。第一次是研究所钥匙名/描述（名末尾一空格），第二次是研究室通行卡/描述，不是同一词面。
第79批只增加occurrence1：稳定ID分别以22f361b7、22a4a7a8开头；第47批已译occurrence2卡片两字段保持。不能按section/key字典覆盖或只取最后一条。
79批之后四字段均已译；后续验证不能沿用历史“仅occurrence2在merged”或本批“occurrence1属于新增”的断言，应保留两组旧值。此为源记录/回填验证，不证明引擎查找策略，也不证明钥匙Item就是Rue_1赠物。

## 未译导出不是整个场景前缀的总量（2026-10-20）

Verified / source：第75批回查完整INT catalog，CSMBQ06为117字段；040节已有2条历史draft，前次导出115条只是当时未译子集。
第74批新增27后实际29/117，第75批再新增29后实际58/117，余59。不能把pending文件长度当全量分母，或将040旧2条重复计入新批。
第75批验证先以错误115/56断言失败，改由完整catalog核对117/58；旧plan/review不改，纠正74批文档并记录当前review。
来源和ID/hash未变；这只是覆盖统计修正，不是发现新文本或更改游戏资源格式。

## 任务空白字段不是应补写的奖励（2026-10-19）

Verified / source：MC2Quest/Ch02_296_00/pay原值为空白；保留源hash与完整空白，不填0、SID或猜测奖励。
batch-015.review.json记录held ID/hash，不把原文照抄或空白占位计入已译。字段语义尚未另外验证。

## 第三章对白的另一处未知反斜线（2026-10-19）

Verified / source：INT MC2CSMB/CSMB03_20/voc_csmb_0320_50除正常硬换行外，还包含未知反斜线序列。
本批保留该条完整原值，见batch-010.review.json的held ID/hash；不将所有反斜线机械改成换行或删除。
与Ch00旧异常分别记录，未证明两者含义相同。

## 同名剧情key不保证跨容器同一句（2026-10-19）

本作INT/JPN的CSMB00_15同名key位置有错位，0015_31在两容器不是同一语义句。
不得把section/key相同当作已证明的多语对齐；先核对整场上下文、邻句和源值hash。
技能表同字段的名称线索也不能扩大为剧情表已经对齐。证据见 BATCH_003_OPENING.md。
此外Ch00_1/00_101_00含未知反斜线序列，保留待查，不自动修成标准换行。

## 内容hash不能单独作为译库资源身份（2026-10-19）

新增合成测试发现：两个不同resource具有相同容器字节时，旧导出器虽然按
resource+hash分组，却使用hash/嵌入路径hash落盘，第二份发生FileExistsError。
已在这种条件下额外以resource hash命名空间分离，不合并不同资源ID；
正常双盘同resource+hash仍只导出一份，当前真实80份目录路径保持兼容。
回归同时检查不同hash不共享、不同resource不自动翻译及同词面不同ID不丢失。

## 字距与非剧情标点修订（2026-10-19）

最新规则、字体参数、重建/刷新流程和测试清单见 [TEXT_READABILITY](TEXT_READABILITY.md)。宽字符最小 advance 为字号+5，字形左右最小留白2/3；所有非剧情无内部标点单句均不加句末句号。已离线验证，游戏画面待用户验收；同一测试入口刷新，保留原文对照、runs、存档和配置。

## remap 正宽高仍可能是完全透明的字形（2026-10-19）

旧静态覆盖漏掉 Subtitle 的透明问号、省略号和中点；这类字形占宽却不显示，造成丢标点与空隙。
不能再用“文字里有标点”和“存在 remap”代替图像检查；新 route 对所有七别名的每个字面字符解码查 alpha。
用户第二句的提前换行由保留的韩文硬断行造成，不应首先归因于自动换行算法。
动画字幕位于 Movies 的独立 txt，单查 Coalesced 会漏译；详见 DIALOGUE_DISPLAY_REPAIR.md。

## 大批次不能继续靠改译文绕过字体高度（2026-10-19）

15px Noto 在本批的共同 bbox 并集为 18px，“箭”单字已需 17px；
旧 SmallFont 16px 即使逐字移动基线也容不下。22px 字形并集需 25px。
本批显式增长新字指标并按 BC3 对齐扩大 cell，不裁切、不缩字号、不更改正式译文；
原有字形和旧样本不变。新最大高度可能影响引擎行距，必须单独做游戏内 QA。

公开 JSON 的源 hash 必须按仓库 LF 字节计算；Windows text write 的 CRLF 经 Git
规范化后会使 route 依赖 hash 失配。本批按 LF 重建并从暂存树导出干净副本复核。

## 块对齐 cell 的空白不属于可见字形高度（2026-10-19）

Subtitle 用 32px 高 BC3 cell、29px glyph metric。旧 raster 从 cell 底部选共享基线，
即使字形并集能容下 29px，也因底部 padding 错报 union overflow。
新回归先在原代码复现错误，再只在需要时上移整组 baseline 到 metric 下沿；
实际 bbox 并集超过 metric 仍拒绝，不缩放、不裁切、不抬高旧字体上限，旧已可用基线不变。
这修复生成器误拒绝，不等于确认游戏正文空白根因。

## 样本扩展不能绕过共享基线检查（2026-10-19）

首版剧情 draft 在 SmallFont 15px 收字时，字符“真”的 bbox 顶端 -14 与其他字最大
下伸 3 的并集需 17px，超过原字体允许 16px。生成器在写任何计划前正确拒绝；
没有把字体缩小、裁去像素或提高原字体高度上限。最终将 여차하면 按其条件含义译为
“万一出了事”而非“真出事了”，终稿九句在既有指标内验证通过。
这不等于字体支持任意后续译文；后续收字出现相同冲突时仍应报错并研究独立字体方案，
不自动改译文、缩字或放宽保护。正式翻译不应被当前小样本字体上限绑死。

# Pitfalls

## 2026-10-19: opaque Map declarations and Next boundaries are real evidence

Font.CharRemap stores null key/value type references and raw flags1002; the
metric code's u16 entries do not justify inventing reflected Map types. Font's
property Next run ends at its own FontCharacter ScriptStruct, so a Class is not
validated by requiring every Next target to be another property. Declaration
support also must not silently accept undecoded Array/Map default values. See
FONT_DECLARATIONS.md.

## 2026-10-19: metric mode branches do not establish a serialized Font bridge

The checked metric window uses a20-byte native record stride, while stored Font
glyph records remain17 bytes. Its direct/remapped-looking branches and7F
substitution are code facts, not a live IsRemapped value or a rendering result.
Font.Characters/Textures/CharRemap declaration-reader failures are unsupported
Array/Map metadata, not absent fields. Keep the bridge and draw-path equality
unverified; see TEXT_MEASUREMENT_PATH.md.

## 2026-10-19: initialized native pointers are not cold descriptor rows

Font/MultiFont/Canvas store name/code pairs eight bytes apart, while the earlier
UI component profile has cold12-byte descriptors. Preserve the initialized
code words and indexed native tokens464/470 instead of zeroing or relabelling
metadata to satisfy the cold reader. Canvas's complete header inventory must
retain12 omitted scripted functions; partial successful native parsing is not
whole-scope evidence. See INITIALIZED_NATIVE_TABLES.md.

## 2026-10-19: a local Font Class is not an unresolved imported Engine.Font

Engine's SmallFont uses an exact local Font Class definition. A reader that
requires only the imported display path Engine.Font rejects it before coverage
analysis. Resolve the class reference, not an arbitrary *.Font suffix. Both
SmallFont aliases are non-remapped: the39 warning literals remain explicitly
mode-unverified, not missing-remap or passed direct-index coverage. The
supplementer must retain its explicit-remap guard. See STYLE_REFERENCE_HELPER.md.

## 2026-10-19: fallback names and output-zero stores do not prove font defaults

The style-reference helper associates three native class-name operand chains
with default text/image/combo tag literals. Its two cleared output words and
optional flag stores are not Font initialization. A registration window does
not establish its function's returned runtime class; repeated parent+3C loads
do not establish termination. Preserve external-call and serialized/native
layout unknowns; see STYLE_REFERENCE_HELPER.md.

## 2026-10-19: a conditional selector is not a constant default-style route

All four supplied component tables share slot124's actual36-word predicate.
Its entry+104 gate, four-word OR and helper-result gates prevent interpreting
the getter's alternate-owner route as unconditional. Static offset equality
between the predicate and getter does not assign serialized fields to native
memory. Preserve the SmallFont CDO and General_15 component observations until
the identities/values are proved; see STYLE_SELECTION_PREDICATE.md.

## 2026-10-19: component StringStyle does not exhaust label style candidates

The two warning labels omit their own PrimaryStyle, while the independent CDO
plane contains a DefaultComboStyle tag. Six nested text objects omit StyleFont;
their separate class-default plane observes EngineFonts.SmallFont. Retaining
those observations must not merge defaults or identify the native alternate
owner pointer by assumption. The original twelve General_15 component paths
remain unchanged; neither route proves effective font selection. See
OWNER_PRIMARY_STYLE.md.

## 2026-10-19: physical Font copies need not have different runtime identities

**Verified:** standalone font.xxx and forced-export Font roots in MC2Game/Startup
share canonical Font.General_15 and the original Font package GUID. Whole raw
payload hashes differ, while complete normalized glyph/remap/decoded-atlas data
is equal. A one-package probe can therefore leave another same-namespace copy
untouched; source metadata does not prove which copy wins. The new diagnostic
marks all three planned copies together. A null archetype/missing override field
also does not establish false/zero native defaults. See FONT_BINDING_AUDIT.md.

## 2026-10-18: component prefix and nested-ID pitfalls resolved

**Verified for 446/25:** the extra component header precedes NetIndex; it is not
a universal twelve-byte skip. Ordinary instances use 8-byte prefixes, templates
under class-default outers 16, and class-default objects themselves 4. Raw flags
are two LO/HO words. STYLE_ID is tagged A/B/C/D, not native GUID bytes. All these
branches have synthetic regression tests and original-package verification;
see UI_STYLE_GRAPH.md. The earlier no-guessing entry below remains valid history.

## 2026-10-18: a failed component prefix is not an absent Font reference

**Verified:** the current NetIndex-plus-tags consumer reader cannot parse 9703
MC2Game exports, including 954 UIComp_DrawString objects. The earlier narrow
UIStyle scan returned no direct links in that package, while the broadened
reader finds 16 on custom defaults. Neither result covers component native
prefixes or nested style structures. See FONT_CONSUMERS.md for exact counts.

Do not infer no font use from an empty result, search for arbitrary plausible
tags, or guess a universal 12-byte skip from a few component samples. Preserve
coverage, object indices, failure reasons and logical offsets. A malformed later
ObjectProperty must discard earlier candidate links from the same object.
The new synthetic consumer tests lock this object-level atomicity.

This document records failed approaches, misleading assumptions, fragile workflows, compatibility traps, and other technical mistakes discovered during development of the localization project.

The purpose is to preserve negative knowledge.

A failed approach can be as valuable as a successful one if it prevents future contributors from repeating the same work.

---

# 1. How to Use This Document

Add an entry whenever a problem meets one or more of these conditions:

- it consumed significant investigation time
- the obvious solution turned out to be wrong
- the failure can corrupt data or crash the game
- the issue is easy to reproduce accidentally
- the cause is not obvious from the symptoms
- the workaround has important side effects
- the problem is version-specific
- the problem is tool-specific
- future contributors are likely to repeat the same mistake

Do not use this file for ordinary TODO items.

Use `docs/KNOWN_ISSUES.md` for unresolved player-visible limitations.

Use this file for technical traps and lessons learned.

---

# 2. Entry Template

Use the following structure for each pitfall.

```markdown
## Short descriptive title

**Status:** Verified / High-confidence / Unverified

**Affected area:**
- resource format
- font
- executable patch
- archive
- build system
- translation
- runtime hook
- toolchain

**Symptoms:**
Describe what happens.

**Initial assumption:**
Describe what seemed likely at first.

**Actual cause:**
Describe the verified or suspected root cause.

**Failed approach:**
Describe what was tried and why it failed.

**Working solution:**
Describe the correct workaround or fix.

**How to detect it:**
List checks, hashes, logs, or behaviors that reveal the problem.

**Regression test:**
Describe how to make sure the problem does not return.

**Related files:**
List relevant source files, scripts, resources, or documentation.
```

---

# 3. Preserve Failed Approaches

Do not delete a failed experiment merely because a better solution was found.

Useful failed approaches include:

- replacing only a font texture
- changing encoding without changing the decoder
- rebuilding an archive without updating secondary metadata
- patching only one copy of a linked string
- increasing a buffer without updating a length check
- converting all text files to UTF-8
- using system locale as a hidden runtime dependency
- copying generated files from an old project directory
- manually editing binary data without reproducible tooling

Record what failed and why.

---

# 4. Binary Patch Pitfalls

Typical risks include:

- patch offsets differ between game versions
- executable packing changes file offsets
- RVA and file offset are confused
- expected bytes are not verified
- patch writes cross instruction boundaries
- branch displacement is calculated incorrectly
- patched code assumes the wrong calling convention
- stack cleanup differs between versions
- instruction cache or loader behavior differs by platform

For every binary patch problem, record:

- target version
- target hash
- address or offset
- original bytes
- patched bytes
- exact failure behavior

Never record only "the patch crashed."

---

# 5. Encoding Pitfalls

Common mistakes include:

- assuming visible Korean, Japanese, or Chinese text implies a standard code page
- treating byte length as character length
- treating character length as glyph count
- converting runtime files to UTF-8 without verifying parser support
- trimming bytes that are actually part of a multibyte sequence
- interpreting control codes as text
- applying Unicode normalization that changes expected byte sequences
- confusing encoded text with direct glyph indexes

When an encoding issue is found, record:

- sample source bytes
- expected display
- actual display
- decoding rule
- terminator behavior
- control-code interaction

---

# 6. Font Pitfalls

Common failures include:

- replacing the atlas without replacing the character map
- replacing glyphs without updating width metrics
- using a font that does not cover all translated characters
- exceeding texture size limits
- exceeding glyph count limits
- using the wrong baseline
- changing line height unintentionally
- assuming monospaced behavior in a proportional system
- generating glyphs in a different order than the runtime expects
- using proprietary fonts that cannot be redistributed

Record both visual symptoms and technical cause.

---

# 7. UI Layout Pitfalls

Typical symptoms include:

- clipping
- overlapping labels
- buttons expanding incorrectly
- subtitles leaving the visible area
- menu rows colliding
- dialog boxes becoming too small
- text scaling differently at high resolution

Possible causes include:

- logical resolution differs from physical resolution
- text measurement uses physical pixels
- UI layout uses fixed coordinates
- font scale and layout scale are independent
- string width is calculated before localization replacement
- line wrapping occurs before runtime substitution

Record which coordinate system each relevant component uses.

---

# 8. Archive Rebuild Pitfalls

Common mistakes include:

- updating the archive TOC but not a secondary manifest
- ignoring alignment
- changing entry order
- recompressing with incompatible settings
- forgetting checksums
- using a generic packer that does not match the game's variant
- failing to update filename indexes
- producing correct-looking archives that crash only at runtime

When documenting an archive problem, include:

- archive type
- tool used
- original structure
- rebuilt structure
- relevant offsets
- alignment requirements
- secondary metadata

---

# 9. Linked Resource Pitfalls

Some text may appear in multiple locations.

Failure to update all copies may cause:

- invisible items
- missing documents
- broken quest progression
- crashes
- wrong labels
- broken resource lookup

Record linked groups explicitly.

Where possible, replace manual duplication with one source-of-truth translation entry.

---

# 10. Translation Data Pitfalls

Common problems include:

- duplicate IDs
- source and target columns swapped
- spreadsheet software changing encoding
- CSV delimiter corruption
- automatic quote escaping
- line endings altered unexpectedly
- placeholders removed by machine translation
- tabs inserted into TSV fields
- leading zeros removed from IDs
- formulas evaluated by spreadsheet software
- strings normalized unintentionally

Document safe editing tools and unsafe workflows.

---

# 11. Spreadsheet Pitfalls

If translation data is edited in spreadsheet software, watch for:

- automatic date conversion
- numeric ID conversion
- scientific notation
- encoding changes on CSV export
- dropped leading zeros
- escaped quotes
- line break conversion
- formulas replacing literal text

Prefer TSV, JSON, PO, or other formats that preserve text predictably.

If spreadsheet software is supported, document the exact import/export procedure.

---

# 12. Build System Pitfalls

Common problems include:

- build scripts assuming absolute local paths
- hidden dependencies on old output directories
- stale generated files masking failures
- release builds using untracked local resources
- tools found through PATH on one machine but not another
- case-sensitive paths working on Windows but failing on Linux
- different Python versions changing output
- different compiler architectures producing incompatible binaries

Record clean-build failures and their causes.

---

# 13. Dependency Pitfalls

Document external tools that:

- changed behavior between versions
- are no longer downloadable
- have incompatible licenses
- require GUI interaction
- depend on system locale
- produce non-deterministic output
- silently overwrite files
- do not support long paths
- do not support Unicode paths

Where possible, pin known-good versions.

---

# 14. Runtime Hook Pitfalls

Common problems include:

- hook runs before the target module is loaded
- hook runs too late
- thread-safety problems
- recursive hook calls
- hook conflicts with other mods
- proxy DLL name conflicts
- function signature mismatch
- renderer-specific assumptions
- anti-cheat or integrity systems blocking injection

Document initialization order and compatibility limitations.

---

# 15. Emulator Pitfalls

When testing console games, distinguish:

- game bugs
- patch bugs
- emulator bugs
- renderer bugs
- timing bugs

Record:

- emulator version
- backend
- settings
- whether the issue reproduces on hardware or another emulator

Do not diagnose emulator-specific behavior as a game-format fact without evidence.

---

# 16. Save Data Pitfalls

Localization changes can sometimes affect save compatibility.

Possible causes include:

- translated identifiers
- changed resource indexes
- string length changes in serialized structures
- locale-specific save paths
- checksum differences
- version tags

Never assume visible text is safe to translate if it is also used as an internal key.

---

# 17. Subtitle Pitfalls

Common problems include:

- subtitle text exceeds safe width
- hard line breaks conflict with automatic wrapping
- subtitle timing shifts after video re-encoding
- subtitle renderer does not support target glyphs
- pre-rendered subtitles use the wrong font
- line count exceeds engine limits

Record exact timing and rendering constraints.

---

# 18. Media Re-Encoding Pitfalls

If video or audio must be regenerated, document:

- codec
- encoder
- version
- bitrate
- dimensions
- frame rate
- audio format
- muxing requirements

Generated media may differ across tool versions.

Do not assume functional equivalence implies byte-identical output.

---

# 19. Path and Filesystem Pitfalls

Common problems include:

- Unicode paths
- spaces in paths
- very long paths
- case sensitivity
- slash direction
- reserved Windows filenames
- read-only installation directories
- Steam or launcher auto-repair
- antivirus quarantine

Build tools should quote paths correctly and avoid unnecessary path assumptions.

---

# 20. Git Pitfalls

Common repository mistakes include:

- committing generated output
- committing proprietary game files
- committing local-only instructions unintentionally
- tracking files that should remain ignored
- losing executable bits
- line-ending conversion
- Git LFS pointer mistakes
- renaming only by case on case-insensitive filesystems

Document project-specific Git requirements if needed.

---

# 21. Release Pitfalls

Before release, verify that the package does not accidentally include:

- original game binaries
- private paths
- debug logs
- temporary files
- proprietary fonts
- test assets
- developer-only configuration
- untranslated debug strings
- stale build output

A release should be built from a clean output directory.

---

# 22. Regression Prevention

Whenever a significant pitfall is fixed, add a regression check where practical.

Possible checks include:

- unit tests
- hash verification
- expected-byte checks
- translation validation
- font coverage checks
- archive parser checks
- clean-build CI
- smoke-test scripts

A documented pitfall is useful.

A documented pitfall plus an automated regression test is better.

---

# 23. Project-Specific Pitfalls

Add project-specific entries below this line.

Remove unused template text when adapting this document to a real project.

---

# 24. Final Pitfall Standard

This file should make it possible for a future contributor to answer:

- what looked correct but was actually wrong
- what caused crashes or corruption
- which tools or versions were unsafe
- which assumptions were disproven
- which resources must be changed together
- how to detect recurring failures
- how to avoid repeating previous research

Negative knowledge should be preserved as carefully as successful implementation details.


## 2026-10-18 已验证的项目陷阱

- Coalesced 长度大端但宽载荷 UTF-16LE；单凭 Xbox 字节序整体按 BE 解码会得到错误文本。回归测试 test_utf16_roundtrip_and_code_units。
- INT 后缀不是英语证明；当前 MC2UI.int 实际存在韩文。
- 候选中有 UnrealEd 编辑器字段，NewGame 命中不是启动菜单可见证据。
- 只加 gitignore 不会移除既有索引；本目录原无 .git，本轮新建索引并运行 check_repository，原件保留。
- 本机控制台默认 cp932，打印中文研究内容发生 UnicodeEncodeError；设置 PYTHONIOENCODING=utf-8，磁盘文件始终 UTF-8。原始读取记录不改成成功。

- 首次 git diff --check 发现 CRLF 与模板硬换行/TSV 空字段。索引通过 .gitattributes 归一 LF，Markdown 仅豁免 blank-at-eol，保留原有硬换行和空列；Python 文件尾多余空行已修复。默认 diff 检查随后重跑。

## 2026-10-18 字体推进中的已验证陷阱

- MCARTA bulk flag0x40对应LZX，不直接套通用UE3标志语义；原版resident Startup同一图集是raw0，独立font是LZX0x40。原始平铺字节hash一致，仍分别保留存储模式。
- Startup驻留Font.General_15，单改外部font.xxx不是完整补字方案。
- 24×24 BC3存储格不要求glyph指标高度24；本次保持23，避免改变字体全局最大高度。原字符/填充不得为了补字删除。
- 标题待机演示可进入村庄，看见HUD或启动进程不是受控游戏输入与资源绑定证明。未见KCK的尝试按未建立结果保留。
- 物理Esc会中止当前窗口控制工具，但用户明确它只表示退出游戏，不暂停工程；不把工具事件冒充用户暂停项目。
# Xenia launcher CI: Windows short TEMP paths (2026-10-18)

The initial launcher tests passed locally and on Linux but failed two path-string
assertions on Windows hosted runners. TEMP used `RUNNER~1`, while `Path.resolve()`
correctly recorded the long `runneradmin` path. The launcher behavior was correct;
the fixture compared noncanonical spellings. Canonicalize the fixture root before
constructing expectations. Keep full configuration and no-tuning checks unchanged.
Failed run: 39109395945, commit 6bd840d; do not report it as successful.

## Runtime controls: LZX, raw packages and font selection (2026-10-18)

Native decoder roundtrip is not game compatibility: original first-chunk no-op
stored/CAB re-encodes guest-faulted too. Alignment alone did not fix them. A raw
outer package needs package bit 0x02000000 cleared as well as compression flags
and chunk count. Derive the header field; do not blind-patch offset 21 on other
builds. General_15 and Subtitle append tests still omit Chinese, so do not assume
these are the warning's live font. See RUNTIME_TEXT_BINDING.md for controls and
remaining hypotheses. Movie playback after a guest fault is not a passing boot.

## Do not discard editor-named packages by filename

Default__Engine Tiny/Small FontName fields refer to MC2EditorResources, whose
three Korean Fonts were absent from the earlier three-package study. Cooked
MC2Engine.ini and Xe-MC2Engine.ini disagree on Tiny/Small; serialized defaults
are not proof of runtime priority. See FONT_REFERENCES.md.

## Fonts can be embedded in the main game script package

Do not limit a font search to font.xxx, Startup or editor resources. The actual
MC2Game.xxx class table also contains Font.General_15 plus 12 font_ui.Font
exports. Earlier geometry candidates did not cover this copy. Use the guarded
class inventory described in FONT_REFERENCES.md. NtCreateFile debug requests
identify candidates, not successful loads or actual draw selection. A raw
MC2Game control reached title/movie only; its warning compatibility is pending,
so the MC2Game geometry candidate was not deployed in that trial.

### Core.Component is not the root of the class hierarchy

A class walker may stop at Component when Core is absent, but must continue to
Object when Core is supplied. Otherwise the real Component CDO's Object
archetype fails a false class-compatibility check. Keep optional boundaries
explicit; reject malformed supplied definitions. Closing the CDO chain still
does not establish native initialization or the font selected during drawing.

### Multi-alias supplement restoration and raster drift

Controls in the supplement bundle retain original physical compressed bytes;
geometry probe controls are decompressed/raw. Do not interchange these meanings.
Backup-restoration equality does not demonstrate recovering an original compressed
first header chunk from the candidate alone. Raster dependency changes can alter
atlas pixels despite unchanged glyph count; the full expected supplemented
fingerprint is a deliberate guard. Never silently refresh it on mismatch.

### Windows short temp names can make a fault injector miss its target

The first multi-alias builder CI passed both Linux jobs but failed the Windows
readback-injection test: the builder canonicalized its output root, while the
injector compared an unresolved TemporaryDirectory name. RUNNER~1 versus
runneradmin identified the same directory with unequal path spellings. Compare
resolved identities in the injector and assert that exactly one read was
corrupted. An isolated junction-temp reproduction fails with the original test
and passes with the corrected test; production readback guards are not relaxed.

### Literal remap coverage is not a widget binding or display proof

A placeholder's characters are not its expanded runtime content. Exclude only
exact protected TOKEN matches, retain unknown syntax, and report dynamic coverage
as unverified. Explicitly mapped whitespace may have no pixels, but an empty
visible glyph is not sufficient coverage. Do not guess no-remap/direct-index,
non-BMP or fallback behavior. Keep every supplied font's failures, not just one
passing alias. A source-value UTF-8 hash is not a serialized UTF-16 range hash;
retain the separate whole-container hash and reject unknown source modes.

### Packaging must validate actual dependencies, not a producer's success flag

A font-bundle manifest can be stale, omitted or forged. Derive confined payload
paths from a trusted exact-hash plan, verify every candidate's complete bytes,
then independently check original/new Font identity/semantics and text coverage.
Recompute TOC changes from actual lengths, including text when variable-length;
do not reuse a font-only TOC blindly. Keep original compressed controls distinct
from raw geometry controls, and never call an incomplete candidate tree a game.

### Python JSON object equality is weaker than a typed metadata contract

False==0 and 1==1.0 make ordinary dict equality accept altered metadata types.
Independent candidate replay rejects duplicate JSON keys/non-finite constants
and uses strict canonical JSON,
while computing every resource/report value from trusted plans and actual bytes.
A self-consistent forged report hash is still not report truth. Historical
producer extra-input hashes are only declarations unless separately reopened;
without a trusted original manifest anchor, do not claim their original byte
identity. Candidate descendants must remain a closed regular-file set, not
junction/symlink shortcuts that happen to point at currently matching bytes.


### Do not skip editor-shaped fields just because a package is cooked for Xenon

The inspected 446/25 data-only ScriptStructs retain ScriptText/CppText/Line/TextPos
zero fields before script size/flags/defaults. A guessed console omission shifts
all later data. Also distinguish persistent ScriptStruct default records from
C++ initialization and effective instance memory. STYLE_ID has no own default
records but inherits Guid declarations/explicit parent defaults; missing is not
zero. Bool size0 means a header value, not a four-byte payload: the former
flattened bool offset was four bytes late and is now corrected. REA's general
binary opener did not admit UE3.xxx; repeated renaming/provider setup is not a
format decoder. Use the version/hash-locked reader and retain this boundary.


### Native parameter stubs are not the font-selection algorithm

UIComp_DrawString.SetFont/DisableCustomFont and the two style getters are declared native; their stored scripts only name parameters and terminate. NativeToken=0 does not identify a C++ implementation or prove no native behavior. Do not claim setters/flags/call order from names or these stubs. Functions also retain nonzero Line/TextPos and FriendlyName, unlike zero-valued data-only ScriptStruct fields. Five sibling non-native methods remain explicit unparsed records, not empty successful functions; do not silently extend native-stub size rules to general v446 bytecode.


### Preserve bytecode boundaries without inventing native behavior

The5 scripted siblings are now fully decoded only with explicit --include-scripted and hash-locked Core input. In these bodies short-circuit Skip spans include the enclosing EndFunctionParms, while default-value spans include EndParmValue; an off-by-one shifts the following statement. Core operator FriendlyName aliases differ from export leaves when the operator flag is set. Preserve Context raw skip/property-type fields without assigning an unverified VM meaning. Enum-typed Orientation does not prove runtime index bounds; source-like expressions and syntactic control edges are not executions. See SCRIPTED_UI_LAYOUT.md.


### XEX virtual images are not ordinary raw PE files or authenticated signatures

A XEX basic image retains PE raw pointers/size that do not describe its virtual bytes: .text raw0x2c8c00 is not code RVA0x2d0000; .reloc is partly absent. Do not feed those raw offsets into native-address claims. CBC chaining continues across stored basic extents; inserted zero bytes do not enter ciphertext or reset the IV. Exact inverse re-encryption and dual AES agreement do not verify RSA or stored digest semantics: direct plaintext-page SHA1 matched0/307 digest fields, so that hypothesis stays rejected. REA rejected the XEX format and the genuinely reconstructed PE architecture; no provider/architecture spoofing or native session was used.

Wide name searches also need actual NUL boundaries and big-endian alignment. A one-byte-shifted UTF16LE ASCII match is not a second string encoding. The full native-registration leads start with intUUIComp_, not the interior UIComp_ substring; four unique data pointers were found only after using full names. They are not yet verified native entry points. See NATIVE_IMAGE.md.


### Static native descriptor reconstruction is not runtime registration or defaults

The intUUIComp_DrawStringexec* cold rows contain zero descriptors until initialization; those zeros are not UI component defaults. Constant values must be traced through reused symbolic stack slots and sign-extended lis/addi address materialization, not the last textual register assignment. Reject unknown reads/calls/interior branches, DS update forms, duplicate/incomplete writes and nonzero adjustors in this profile. The lookup comparator-zero and row+4/stride12 shape is checked separately; its helper is not executed or assumed to compare strings a particular way.

Object-relative font words0xd8/0xe4 and PPC packed bit0x20000000 do not replace logical package tag offsets/BoolProperty0-or-1 headers. Paired setter/disable instruction chains support field-name deductions but do not prove constructor values, caller order, active font, complete struct layout or Chinese pixels. See NATIVE_BINDINGS.md.

### An override flag alone does not select a font; next-start is not an end

The checked overlay tests both bit0x20000000 and a nonzero pointer word before
writing output+0x20. Null bypass preserves the existing output even with the bit
set. Do not infer an effective Font from a setter/flag without this second guard.
Similarly, CE .pdata packed length—not the next listed start—declares function
extent. Real gaps occur after the initializer and getter helper. The overlay leaf
has no covering record; that absence neither removes its code nor extends the
preceding record over it. See NATIVE_STYLE_SELECTION.md for confidence levels.

### Keep class-name prefixes, initializer phases and object contexts distinct

The checked native registrations pass full-U-name address+2; do not generalize
that one code-unit adjustment into a resource-name normalization rule. A table
write with surrounding cleanup calls is not enough to name a default constructor.
The actual selected leaf callback windows do not write component font wordsD8/E4;
their silence is not zero-initialization evidence. Registration helper writes at
its own object-relativeD8/E4 belong to another object, not the component instance.
Pointer scans also find code addresses inside .pdata: restrict table candidates
to typed read-only .rdata rather than scoring isolated aligned matches. See
NATIVE_CLASS_TABLES.md for the separate static/semantic/runtime evidence planes.


### Git EOL rules do not canonicalize an already-written working file

Windows Path.write_text may create CRLF even when Git stores LF. A local plan
SHA can then pass local CLI checks but fail the documented command in a clean
checkout. Pin the exact shipped LF source bytes, write hash-bearing JSON with
write_bytes or explicit newline='\n', and test doc hashes against repository
plan bytes. Do not normalize arbitrary inputs inside a verifier or weaken exact
hash guards. Old raw-plan identity remains different; reports may legitimately
change only their plan_sha256 when the semantic plan is unchanged. See the
native probe byte-contract regressions and canonical CLI proof in build/.

### Do not promote a clear call or a Class metadata zero to an instance default

The same fill helper clears both a stack buffer and an allocation destination;
its target register/context matters. At the allocation destination call, r4 is
zero and r5 comes from metadata slot120, but additional initialization calls
occur before allocation returns. An intermediate zero does not establish a
callback-entry or rendered font value. Metadata result+11C is a direct callback
field, not the unrelated virtual slot11C in every table. Metadata's ownD8/E4
zeros belong to a different object. See OBJECT_INITIALIZATION.md; do not extend
zero runs over nonzero metadata fields such as14C=8.

### Coverage of a marker is not coverage of the investigated UI experiment

The retained Kick marker had valid byte/inverse/remap proofs but targeted another
record than the LogIn_NewGame warning's known MarkupString. Correct the active
source selector before extending engine research or calling the packet a warning
probe. A prefix edit can preserve the guarded original suffix without publishing
its full text. Do not count Unicode codepoints as UTF-16 units for astral text,
split recognized control tokens, or audit only inserted glyphs while ignoring
the retained body. Current Login prefix packets audit all39 literal codepoints;
old successful Kick manifests still fail against the newer trusted plans.
# Operand-anchored Font literals (2026-10-19)

A preceding-NUL UTF16 scan missed UFont at821AE46C because pointer data ends
immediately before the literal. An exact registration operand plus terminated
readonly literal is a stronger local anchor. Use the separate Font profile;
do not relax old style-profile boundaries or drop full native U prefixes.
See FONT_SERIALIZATION.md. The six static serialization templates do not
establish archive virtual-call semantics or authorize runtime-font claims.
## 窄框触发折行，不等于所有宽框都会失败

用户补充标题弹窗窄、剧情框宽；必须分别验收。原生强制分割分支多计 origin 的错误，
会使居中左偏 origin/2，而框小只提高触发频率。不要加手动换行、改左对齐或扩大框体冒充测宽修复。
运行时 patch 查找路径也须核对实际 Xenia 版本：50e9c715d 使用 storage_root/patches，
既有 launcher 每次更换 storage_root，所以往全局 xenia/patches 放文件不会进入该隔离路径。
见 WRAP_WIDTH_FIX.md。

## 扩展样本不等于继续向原 atlas 任意塞字

General_15 最后一图 512×64 仅有三个 24×24 空位，45 字样本必须明确扩高。
宽度不变的 tiled 高度扩展仍须校验原行像素、批量 glyph 的 block 避让和 bulk/mip/SizeY 一致性。
SmallFont 旧两字基线不保证更大字符集：共享 bbox 可能恰需用掉原有一像素底边留白。
保留三个显式换行不构成自动断行证明；最后无空格段落必须在游戏中观察。
见 TEXT_LAYOUT_PROBE.md，原始小样本与新样本分开保留。

## Preserve both Font edits in Startup_int

The warning's component and default-style candidates include different font
families in the same package. Copying separate General_15/SmallFont candidates
over the same Startup_int file discards one edit. The route builder composes
edits and then rechecks all final fingerprints. SmallFont's explicit identity-
256 conversion is only a disk candidate, not verified runtime equivalence.
The active raw control has its own TOC and is distinct from original backups.

## Do not interpret a mixed-resource test as a font result

The combined probe has six resources. Candidate font/text bytes are shared
between discs, but their TOCs are not. The read-only verify_resource_phase.py
checker requires the packet-manifest hash and phase, reports wrong/missing
resource bytes, and does not launch/install anything. A positive byte check
is not game rendering or restored-behavior acceptance. Put its report outside
both inputs so it never writes into a test-resource directory.


## 独立字幕术语与Coalesced工作区术语锁

Verified：prepare_translation_workspace当前要求terms中的每条resource/source_string_id都存在于其导出的Coalesced容器，
直接混入Movies独立字幕锚点会在发布工作区前拒绝。不要为绕过检查而伪造容器ID、改写资源来源或跳过原有验证。
第33批的一号候选采用batch-033.review.json/subtitle_term_candidates保存真实subtitle ID、cue源hash、resource、
target和candidate状态；Coalesced共享terms仍只保存其已支持的容器锚点。
未来扩展统一导入器时应增加显式锁定的字幕来源及验证，再迁移该候选，不能把独立候选自动提升为reviewed。

## 第六章护送任务的未知反斜线（batch036）

Verified / source：MC2Quest.int [06_603_0] 603_0在“몬스터를”之后含`\처`，不是已确认的`\n`。原ID/hash见batch-036.review.json；保持原值，不猜换行，不计draft。即使同值后面另有合法换行也不整体规范化。

## 实验室钥匙与通行卡同key（batch047）

Verified / source：MC2Item.int的Valuables中，key_laboratory及key_laboratory_D各有两个occurrence，第一组为钥匙，第二组为通行卡。本批仅第二组稳定ID/source hash回填；第一组保持。不要按key构建会覆盖同名项的字典，不要用不含occurrence的next取首项。完整源值仅留忽略的验证目录。

## 第九章演说源句异常（batch050）

Verified / source：MC2CSMB.int [CSMB09_20] voc_csmb_0920_06含감Ｒ异常混合字符，句段缺损。稳定ID/hash见batch-050.review.json held_entries；双盘源hash一致也不证明语义完整。保持原值，不猜补成常见韩语动词，不计draft；完整源仅留忽略的本地验证证据。

## Boss回复日志是拼接片段（batch051）

Verified / source：MC2UI.int Battle_Log/beeljebubRecover_1/2分为Boss主语和带助词的HP后缀片段。Unverified：运行时夹入数值的位置/拼接顺序尚无调用证据。两项ID/hash记录于batch-051.review.json held_entries，原值保持；不要只译Boss主语，也不要未经证据重组数值/动词顺序。

## 同key跨locale的机关文案并非逐句对齐（batch062）

Verified / source：MC2Compose的Chapter11_29在INT与JPN中内容不同；INT讲中心之门与英雄牺牲，JPN另有明确的四碑计数。该字段INT的UTF-8源值hash为591045150b284d3b73bb96aecd0cf733ca1cf4417fe8b986e99b8260f787460f，JPN的UTF-8源值hash为20f64eb471195fd60ba271e5ddae23dfec80c2bf0d1cbe6a5e2a019b9599424c。
32/33同样存在句子跨字段分配差异；相同section/key不保证逐句或数值对应。不得据JPN计数改写INT已有五碑机关，也不得直接把JPN译文按key批量填入INT。两者须保留独立resource、ID及源hash，只作明确归属的上下文旁证。
Unverified：INT11_27的성쇄词义以及32-36说话者/运行触发仍未确认；JPN同key的隆盛措辞不是原韩文拼写修复或角色绑定的证明。未把这些待查字段计入本批draft。完整原文仅保留忽略的研究证据，后续按锁定源重新提取核查。

## 第十一章支线源条件不一致与残句（batch063）

Verified / source：MC2Quest.int的11_303_0在yes_0/in_0/DES分别写4/3/5，且奇怪蘑菇与毒蘑菇的源名在不同字段间不一致；Item key Mashpoison却以奇怪蘑菇的韩文源词命名。不要按英语key、相似名称或某一说明把其他源条件统一。Unverified：运行实际检查的数量/物品尚无调用或游戏证据，译文仅忠实保留各字段。
11_302_0的302_6/7源为未完片段，显示/拼接未验证；连同Chapter11_27的未确认词义，三处ID/hash/reason记录于batch-063.review.json held_entries，原值/尾随空格保持，不补全或计draft。체액/채액与코타메레按候选alias处理，不改原拼写。

## 连携技能重key与词内空格（batch071）

Verified / source：双盘锁定INT的MC2Skill.int/Renkai_Ougi中，Skill_d_37出现两次，不能以(section,key)字典去重。occurrence1是风/雷描述，ID为coalesced:d02cca0a45466b43635aa14caa97a7a936f0c90f0f5f0dbae180097f716d8183，源值UTF-8 hash为092189de54fd4e88eeed72e9e6724cb306120ee93279a537daa9d7876fb51d40；occurrence2是冰/雷描述，ID为coalesced:dacc826ac97f366f530bdf7db67ae20723de9f871e311ff2351b8ea5bc160a68，hash为aebd919bd063cdb7e58ba4b276909b0bcfd0e9cd8219bac2bc37e110baf01f1b。55批已译1，71批只新增2；旧译与原始两个occurrence均保持。
Verified / source：同一INT的Juto_Crocell_Renkai源名노바 슬래시含内部空格，Compose12_38/39的노바슬래시无空格；精确短语搜索会漏掉前者。保留各自源ID/hash/拼写，仅在候选词库记录主词/alias，不预先规范化源文本。
Unverified：实际技能触发、属性效果与提示调用尚无本批运行证据；源码邻接和描述不替代游戏验收。초빙결뇌진폭暂译超冰结雷震爆，原汉字与官方译名仍待核。
