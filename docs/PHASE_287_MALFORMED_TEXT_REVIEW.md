# 第287阶段：异常宽串与损坏对白复核

## 裁决

- **可采用一条保守草稿**：`MC2CSMB.int [CSMB09_20] voc_csmb_0920_06`，ID `coalesced:851544b42b76237932ecb3a7596181fed5aa4c07e654a778cf5327b46def9111`。建议译文为“困扰我们的这一切灾难，\n都是因为这个世界的KAN循环出现了严重问题。”，仅译入已知主句及两种来源共同支持的世界关联，不宣称恢复损坏修饰语。
- **必须保持整文档**：`MC2Game.int` 三个目前抽出字段 `[] ItemName / Accept / Cancel`，以及其JPN同字节文档。不用三个看似可读前缀重建INI，不修长度、不插NUL、不改编码。
- **未知仍然未知**：`감Ｒ`中的具体原韩语修饰成分、损坏原因、异常宽串形成原因、这些模板的实际游戏显示路径没有得到证明。新草稿不是源数据修复，也不是游戏内验收。

## Verified：独立原始数据及两盘交叉

脚本与完整、未提交的本地来源证据位于 `build/phase-287-malformed-research/`。`source.py`分别解析两盘INT/JPN/KOR六资源，并在内存完全序列化回原字节；`boundaries.py`独立按大端有符号长度走完每一个外层字符串，不调用项目解析器来寻找内容边界。两条路径解出的目标内容一致。这证明异常存在于原资源负长度宽串负载，而不是当前解析器对正确UTF16作了错误的端序选择。

- 两盘INT资源SHA256：`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。
- 两盘JPN资源SHA256：`fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`。
- 两盘KOR资源SHA256：`fb51da8543516deb68c728c6da0509073fdebc791a18fa310fdcdf9f9ea9374a`。
- INT及JPN中的MC2Game文档四份负载完全相同；390字节（不含末尾UTF16 NUL），SHA256 `e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7`。完整原文、字节、记录偏移仅保存于忽略目录，不提交完整专有资源。
- 原始文档有11处`0d 0a 00`三字节图案，偏移28、59、92、143、146、165、194、235、264、269、288。它们跨奇偶位置，不是正常一致UTF16LE的CRLF序列。以这些图案实验分割能读到部分ASCII键和韩文按钮标签，但最后一段99字节为奇数，严格UTF16LE解码失败。
- 统一给每处图案补一个NUL会使390字节负载变成401字节（奇数），因此连最小宽串长度条件也不满足。该实验不是修复方案；修复不能由“补零后几个词变可读”来证明。
- KOR的MC2Game文档是独立290字节正常样板，只有AnswerChoice/MC2Item等早期示例，并不包含完整INT Quest/UITest对应内容。它不是可覆盖INT的修复模板。

项目`tools/coalesced.py`明确按物理行抽值，不宣称解释完整INI语义；宽串已含U+0A0D及错位字符，抽出的`[] ItemName`值实际包含后续CurePoison文本的错位表示，Accept值也包含RewardInfo错位表示。只替换可读前缀的整字段会顺带丢弃附带原数据。当前三个ID不能当正常独立显示字符串直接采用。参见`source-crosswalk.json`、`independent-boundaries.json`、`counterfactual-segments.json`。

## Verified：CSMB场景局部对齐及可译共同语义

两盘各自的INT和JPN `CSMB09_20`都是69个字段，原始来源全段保存在`source-crosswalk.json`。两种语言键起点不同：INT从00到68，JPN从01到69。本次目标**INT06对应局部顺序中的JPN07，不对应JPN06**。`adoption-evidence.json`锁定四份来源的资源hash、文档hash、精确字段UTF8/UTF16LE hash、原始容器偏移、12对连续上下文窗口。此局部对齐不推广为全游戏统一编号规则。

目标之前连续内容为两军首领同台、休战声明、群众惊讶、千年繁荣、灾祸再临；目标之后双方又连续转入阻止灾祸的方法、玛格纳卡尔塔、寻找救赎之光、王女身份。该顺序使对应不是仅凭相似词或同键猜测。INT07与JPN08细节有差异，证据保留此差异，不把日文整段覆盖到韩文。

INT目标可读主句直接说明“折磨我们的这一切灾难”与“KAN循环发生严重问题”的因果；JPN07明确说明世界的KAN循环出了问题。INT的`이 세계를`保留世界关联，但后面的`감Ｒ`修饰谓语无法还原。原资源中这两个字符就是U+AC10/U+FF32，UTF16LE为`10ac32ff`，紧邻前后韩文仍正常，没有本段发生整段端序错位的迹象。

建议草稿保留INT已知因果主句、严重程度及“这个世界的KAN”，不推断缺失词为“笼罩/环绕/充满”等任何一个具体谓语，也不导入JPN独有的“力量之源”。单个字面`\n`保持；KAN沿用既有词形。该方法采用的是交叉证明的共同可读命题，不是悄悄修原文或宣布日文可全面替代主来源。

`adoption-candidates.json`提供一条可用草稿；`adoption.py`重新读取四资源，以固定hash验证并重建该证据。原来源与catalog source值完全不变，human-finalized及runtime-accepted均为false。原来batch050的held原因应在权威裁决记录中追加这次“共同主句可译，但损坏修饰仍未恢复”的新状态，而不是删除历史损坏发现。

## 有限包/原生引用搜索

`bounded-references.json`只搜索已验证MC2Game逻辑包及原生映像，记录ASCII、UTF16BE/LE的精确位置和包含导出。完整目标Strings路径、CSMB06/07裸键均无直接命中；ItemName、Accept、Cancel等短词有大量名称表/不相关方法命中，这些不是目标翻译的运行消费者证据。UTF16LE在原生大端宽串中可能只是偏移一字节的重叠命中，不据此宣称双端序运行路径。

未搜索完全部关卡/电影包，未排除动态构造键；不能从上述缺席推断字段从未显示。对白采用依据来自原始完整场景与局部跨语言对齐，而非臆造运行引用。MC2Game异常模板缺少实际读取闭环，保持整份原值。

## 复现

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python build/phase-287-malformed-research/source.py
python build/phase-287-malformed-research/boundaries.py
python build/phase-287-malformed-research/adoption.py
```

三脚本均已执行退出0；最后两脚本文字结果分别为：

```text
PASS independent 6-source boundaries; parser exact; bounded package/native reference inventory
PASS 1 conservative damaged-source draft; 4 exact source locks; 69-field scenes; 12 ordered pairs; no source repair
```

没有运行游戏，没有修改tools/locales/tests或原始资源。本研究文档与忽略目录中的脚本/证据可供主流程独立复核后采用；双盘构建、回滚、现有测试目录增量刷新与推送由主流程执行。
