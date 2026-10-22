# 第285阶段：章节术语独立一手核查

核查日期：2026-10-23。结论：支持 Chapter12_37 以 **High-confidence deduction** 采用“王之灵庙”；本次未取得足以判定 Chapter11_27 的 성쇄 为专名或 성쇠 误字的新一手证据。此报告不将研究判断代替游戏内验收。

## Verified

- 独立用 `tools/coalesced.py` 只读解析两盘 `build/disc{1,2}-selected/MC2Game/Localization/Coalesced.{int,jpn,kor}`；两盘各语言容器分别同 hash：INT `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`，JPN `fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`，KOR `fb51da8543516deb68c728c6da0509073fdebc791a18fa310fdcdf9f9ea9374a`。这是双盘镜像一致的来源，不是两份独立创作证词。
- INT `MC2Compose.int` 第882物理行、`Chapter11/Chapter11_27` 确实写作 성쇄；JPN `MC2Compose.jpn` 第880行同键写作 隆盛。两盘所有已解析文本中，성쇄 只见该字段，성쇠 未见。来源：上述原容器的嵌入文档；完整语境见忽略目录 `build/phase-285-verification/full-source-context.json`。
- 两语言相邻碑文并非逐句等值：`Chapter11_26` 的JPN增加异种族/凶星叙述，`Chapter11_28` 的INT写 마성，JPN写 王都。故同键的 隆盛 只能证明日文版本采用该措辞，不能单凭它证明韩文词形的成因。来源：两盘 `MC2Compose.{int,jpn}` 的 `Chapter11_25` 至 `Chapter11_29`。
- INT `MC2Compose.int` 第935行 `Chapter12_37` 的四证明条件，对应JPN第933行同键的王の霊廟目的地。INT `MC2CSMB.int` 第4713行 `CSMB12_131/voc_csmb_12131_07` 写拉斯特拉达中心；JPN第4732行 **12131_08** 明写王の霊廟、中心。这里必须按完整场景对齐而非同键替换。JPN第4738行 **12131_14** 又将最终对手定位于该处。来源：两盘上述嵌入文档。
- 独立UI `MC2UI.int` 第386行 `information/lastrada_sch` 为拉斯特拉达最深处；JPN第385行同键为王の霊廟。该UI地名与前述目的地叙述相互印证。来源：两盘 `MC2UI.{int,jpn}`。

## High-confidence deduction

- “王之灵庙”采用门槛合理：说明条件、完整场景中的目的地和独立UI名称形成三路关联，不依赖 영병 的假定字典释义；对应的JPN续句也定位同一最终对手。它支持**目的地翻译**，不证明韩文原字应改成何字。来源：上节 Chapter12_37、CSMB12_131 和 lastrada_sch；采用记录为 `locales/zh-Hans/candidate-decisions/chapter-term-adoption.json`。

## Unverified hypothesis

- 성쇄 是 성쇠 误字、或是尚未释明的专名，均未被本次游戏一手证据区分。隆盛/兴盛与盛衰并不等义；即使一般语言资料支持 성쇠 对应盛衰，也不能自动套回游戏词形。原字段应继续完整保留，不以“兴盛”或“盛衰”抢填。来源：上节 Chapter11_27 和相邻碑文的实质差异。
- 外部精确检索包括 `"마그나카르타2" "성쇄"`、`"성쇄의 영혼"`、`"성쇄" "마그나카르타"`、`"マグナカルタ2" "隆盛の魂"`，未取得开发/发行方的词义解释。英文查询命中[玩家攻略](https://gamefaqs.gamespot.com/xbox360/930253-magna-carta-2/faqs/58206)，属于二手转录，未用作采用证据，也未当作英文本资源的直接证明。搜索无命中不证明不存在。国立国语院PDF本次抓取超时，未据未读材料新增实证主张。

本次仅新增本报告；原容器、现有翻译、计划、候选记录及暂存区均未由此核查改动；未启动游戏或生成ISO。
