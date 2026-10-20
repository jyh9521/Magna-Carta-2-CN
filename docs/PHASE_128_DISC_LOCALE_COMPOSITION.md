# 第128阶段：累计INT/字体/字幕的分盘离线合成

2026-10-20，先核对HEAD 9cd4c1c、远端一致、干净状态及每轮收尾。最后翻译批次仍116，14,082 INT draft、1104 candidate和315字幕draft不增加。本阶段把已有译文编译进局部候选，不重复翻译或标成人工定稿。

## 源与组件

新locale-compositions/disc1.json、disc2.json分别锁定本盘subtitle plan/组件manifest、125字体route/组件manifest、复现的完整INT plan及126控制保留ledger。两原ISO整体hash/size再验证，按本盘XDVDFS inventory只读取四字体包、INT、本盘字幕与TOC；原资源字节逐个匹配已锁source SHA。两盘四字体包原始hash确实相同（三个外层LZX包、一个非外层压缩包），但TOC与字幕来源不共用。

组件manifest/所有成员hash、精确文件集合、源版本、字体原/候选完整semantic、subtitle plan及独立字幕重放均检查。只选择字体组件中的四个candidate包，不带入其旧262条INT、四份字幕或TOC；字幕组件只取本盘21/23份文本，也不取其局部TOC。任何角色重叠/额外盘文件、候选hash漂移、来源或semantic不匹配都拒绝。输入在输出前后重新hash，ISO size/mtime受保护。

新tools.compose_locale_resources是独立offline-disc-locale-composition模式，输出必须新建且位于project内，无安装/启动动作。旧font-route16字幕上限、普通font coverage分类和现有刷新器资源集合检查不改；不是把新对象伪装成旧font-route manifest。

## INT、控制、像素与既有换行策略

完整workspace从已提交workflow复现，14082项与最后116工作区逐字节一致。普通Coalesced rebuild、重提取及逆重建证明原18176值中只应用计划变更，旧译/held与未改字段保持。占位符、非布局控制/格式码仍走原检查；没有新字符串替换或新重排。

四项实际尾TAB必须通过源/完整计划/单项源译文hash、序列[9]及尾部shape验证。七字体逐个对比原与候选的这些控制符glyph index和StartU/StartV/USize/VSize/TextureIndex，均保持；SmallFont原256直索引只接受既有显式identity-256合同。未新增TAB remap、未栅格化TAB，也不解释其运行语义。

对本盘INT+字幕实际需求，七字体均无非控制映射缺口，并直接重解码像素：第一盘每字体2447个非布局字形有ink，第二盘2444个；SPACE/U+3000两项为Zs且实际alpha全零，布局宽保持候选27/20/32。空glyph、可见空格、矩形越界或非Zs布局字面量拒绝。不是仅检查remap存在。

原font coverage报告完整保留，all_literal_coverage_verified=false，未知控制语义仍false；offline命令exit0表示组合/源保留验证，不代表原coverage exit1变绿或游戏验收。累计INT中已有5191条显式line_break_policy（dialogue5066、narrative125）按原值继承，未新增/删除；因此原报告protected_token_sequences_preserved=false，而non_layout_protected_tokens_preserved=true。该存量布局策略不被本阶段重新批准，后续上下文/游戏复核仍需保留，不能宣称所有源换行数均相同。

## 统一TOC与真实结果

update_resource_sizes新增update_sizes_reversible，原update_sizes分支不改。组合器从本盘原TOC对字体+完整INT+本盘字幕的实际size差异一次更新第一个数值，然后反向恢复原字节，保留未请求字段及零自引用；不把两个局部TOC最后写入者当胜者。

第一盘27资源（四字体+INT+21字幕+TOC），152字幕cue；25项size变化，TOC197989→197992。第二盘29资源（四字体+INT+23字幕+TOC），163cue；28项变化，TOC199817→199819。两盘INT候选字节相同，但各自source/controls/TOC与字幕不合盘。

build/phase-128-verification/disc1-composition和disc2-composition各有controls/candidate/rollback-check及四类报告。七字体各自原/候选语义、全需求像素、控制保留、INT逆重建与组合TOC报告保存；56个retained-original回滚资源逐字节恢复，主candidate保持。独立verify从controls重做全部组合/字体像素/报告/manifest，精确逐文件相同，不需要整盘副本或重新提取ISO。

## 从干净源码复现

原资产与Noto/LZX依赖按BUILDING既有流程提供，以下所有输出须新建。组件路径是可再生的已记录构建输出，不是隐藏私有依赖：

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/cumulative-locale-workspace
python -m tools.build_font_route_probe --plan locales/zh-Hans/cumulative-font-route/route.json --game-root build/poc-game/disc1 --font-file build/font-source/NotoSansCJKsc-Regular.otf --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/phase-125-verification/route-probe
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc1.json --output-dir build/phase-127-verification/disc1-bundle
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc2.json --output-dir build/phase-127-verification/disc2-bundle
python -m tools.compose_locale_resources --plan locales/zh-Hans/locale-compositions/disc1.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/locale-disc1-rebuild
python -m tools.compose_locale_resources --plan locales/zh-Hans/locale-compositions/disc1.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/locale-disc1-rebuild
python -m tools.compose_locale_resources --plan locales/zh-Hans/locale-compositions/disc2.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/locale-disc2-rebuild
python -m tools.compose_locale_resources --plan locales/zh-Hans/locale-compositions/disc2.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/locale-disc2-rebuild
python -m unittest discover -s tests -p test_resource_composition.py -q
python -m unittest discover -s tests -q
```

组件候选hash、plan canonical及源/译文hash受保护，依赖/栅格输出漂移会拒绝，不静默换字库。完整游戏原件、完整资源包、ISO/XEX/字库均不提交Git。

## 验证、清理与接续

基线1549，新增13项后修改/索引导出干净源码1562测试均OK(skipped=1)。覆盖坏schema/运行标记前置拒绝、统一更新、角色冲突/局部TOC覆盖拒绝、跨盘原件拒绝、无ledger/源/计划/TOC漂移、no-op仍验hash/ASCII、解码ink、空glyph拒绝、空格严格零alpha/类别及矩形越界。真实双盘27/29资源、七字体/全部INT/315字幕和56资源回滚另行验证，不以合成测试代替。

同一自造TOC的两size变更，旧模块无组合逆证明API、exit2；新helper正逆字节/零自引用/其他字段保持、exit0。隔离模块副本hash保护回滚恢复旧updater、exit0，重跑恢复exit2；主MODIFIED_FILE.py保留新helper。四件证据/精确命令/输入/字面输出/状态见build/phase-128-verification/VERIFICATION.txt，错hash回滚拒写。

八源hash、双盘原INT/旧译、24剩余分类、164文件复现、64当前入口依赖/配置/XEX及candidate/raw只读核对保持，125字体/127字幕组件不改，workflow/terms/subtitle-profile不改。仅清理核实绝对路径的隔离源码可再生成pyc，保留原盘/配置/存档/runs/当前包与全部所需组件/候选/控制/回滚/研究；无ISO/整盘副本/模拟器启动或现有测试目录刷新。

下一阶段先处理新kind、raw-controls和显式资源清单适配：当前inspector只接受旧font-route kind，当前refresh要求资源集合相同；新第一盘从10扩为27，新增17份源字幕在现有candidate/raw-controls根均匹配原hash，十项原raw对照仍与已知基线相同。但本组合尚无raw-controls阶段，不能直接交给旧refresh。保留这些门禁，先做有界适配、源/回滚与存量换行策略复核，再按既有增量流程处理，不新建整盘测试副本，不把离线组合当作运行验收。
