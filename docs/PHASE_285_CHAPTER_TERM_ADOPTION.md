# 第285阶段：王之灵庙实际回填，성쇄仍保留

## 本轮交付

新增batch-118的一条完整说明Chapter12_37，接入正式workflow、双盘资源及既有测试入口。INT草稿14094→14095，旧14094条逐值保持；未改原值4082→4081。没有为了凑批量填入另一条尚未裁决的术语。

译文：`[王之试炼]\n*没有王之证明的人必须在各个房间接受试炼\n*集齐4个王之证明后，通往[王之灵庙]的道路就会开启`。

保留原说明的两个功能换行、两个星号、两对方括号和数字4，不导入日文额外的命令措辞，不改王之证明/王之关卡的既有译文，不修改源容器。44份语境profile与1502条功能换行保护随合并计划重锁；新增U+5E99（庙）在七Font均缺失；三家庭各在既有最后格之后追加一格，原字形位置/留白不变，七别名字库重新构建并验证可见墨迹。

## 证据分级与采用门槛

**Verified**：两盘分别读取并锁定INT/JPN/KOR容器。完整Chapter11、Chapter12、CSMB12_131及lastrada系列UI字段独立核对。KOR仅83个其他字段，不存在这两段的第三份韩文校订来源。INT四证明、四房间、回到关卡、通向中心的说明链条，与JPN同一完整场景相符；INT131_07的中心目的地对应JPN131_08的王の霊廟，而非同键。独立UI键information/lastrada_sch在INT为拉斯特拉达最深处、JPN为王の霊廟；JPN续句指向同一最终对手。

**High-confidence deduction**：Chapter12_37的[왕의 영병]指向上述王之灵庙。此处采用的是完整条件链和独立地名相互印证后的目的地裁决，不是证明영병的字典本义为灵庙，更不是证明原韩文应当如何改字。译文仍为draft；运行触发和画面由用户验收。

**Unverified hypothesis**：Chapter11_27的성쇄可能是성쇠误字，也可能有未查明专名背景。国立国语院材料可核对[성쇠与盛衰的字形对应](https://www.korean.go.kr/nkview/nklife/2012_1/22_01.pdf)，但这不证明游戏里的성쇄就是它。JPN隆盛只支持兴盛读法，不能消除盛衰/兴盛或专名的差异；相邻四方碑文的内容在两语言间确有改写。外部精确检索未取得游戏特定的一手释义。故整条保持原值，未部分填译；不把无结果检索当不存在的证明。

## 可复现资料与收尾

`locales/zh-Hans/candidate-decisions/chapter-term-adoption.json`保存源容器身份、关键对白/UI的精确源值hash、错位对应、采用记录及保留理由；既有63/68/280阶段held记录作为历史快照保留，通过显式采用记录核对后续状态。

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/NEW-workspace-batch118
python -m tools.build_font_route_probe --plan locales/zh-Hans/cumulative-font-route/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/phase-285-verification/route-probe
python -m unittest discover -s tests -q
python tools/check_repository.py
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
```

实际基线、修改、隔离回滚、双盘独立重放、hash保护增量刷新及四实物路径见`build/phase-285-verification/VERIFICATION.txt`。只刷新现有测试目录的文本/TOC及入口元数据；配置、存档、runs、原文对照及315字幕保持；四字体包因追加庙字刷新，不生成ISO/整盘副本，不启动游戏。
