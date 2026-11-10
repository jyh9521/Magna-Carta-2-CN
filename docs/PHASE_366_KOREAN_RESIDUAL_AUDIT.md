# 阶段366：图2碑文与双盘韩文残留排查

日期：2026-11-11。本轮是**排查和审计门禁修订**，没有翻译、替换游戏资源、
刷新安装器或测试目录，也没有生成 ISO／完整游戏副本。

## 已确认：图2不是字体回退

图2全文对应主线 `Coalesced.int` 内：

```text
..\MC2Game\Localization\INT\MC2Compose.int
[Chapter11] Chapter11_27
coalesced:53c21149e6042a65db33e839bdfbb97207a5fab20759ecc43cd6b622f03a5cb4
```

该字段因 `성쇄` 语义尚未确认而保留韩文。它**已经被旧扫描器命中**，不是新发现的
文本容器；旧 `--require-classified` 只检查“有分类”，不会阻止 pending 项通过。
这次用户截图使它从普通 pending 升级为 `confirmed-player-gap`。
术语待考不能把已观察到的玩家漏译排除出待处理清单。

用户图2 SHA256 为 `95220ecb9e2fafe9aeb56ba90c7c4d3aa55ec8e434e5e0e3fda9d85aaf10e082`。
截图证明该句在用户游戏中出现；**截图不标识所用安装包或资源 SHA**。
本轮另外读取当前 recipe 的实际资源，独立验证两盘均保留同一句：

- recipe：`build/phase-365-omission-repair/prepared/recipe.json`
- recipe SHA256：`f9f80fad31dfd7b90d909504248745aa357dfdcee9c661fc2d3b818701114ff2`
- 主INT SHA256：`ee45b275cbcd5275d65a48926bc26d7f2270fd7d19757ad3f7719f57edad0f60`
- 字段值UTF-8 SHA256：`8fcf504429b6addbc0e750a14667647d0573e28f4c35c4a0f2d4b7897d4f5c88`

## 全部正文、场景提示、字幕及DLC

从两份锁定原盘和当前 recipe 重新提取49个文本视图／52个物理成员，原盘完整摘要
前后复核，主INT parse→serialize逐字节一致。扫描的是成品值，不只是译表。

| 集合 | 本轮实际检查 | 结果 |
|---|---:|---|
| 主INT | 39个嵌入文档、18,176字段 | 63个含韩文字段 |
| 章节／队内提示 | MC2Compose全921字段：621章节＋300队内 | 仅图2含韩文；84个原样字段为83个省略号＋图2 |
| 独立字幕 | 44份、315 cue | 没有韩文／假名残留 |
| DLC字幕引用 | 593字段 | 全部绑定主INT，已绑定正文没有韩文／假名残留 |
| DLC武器字段 | 12武器、36字段 | 已绑定正文没有韩文／假名残留 |
| DLC SPA／包元数据 | 两包各221有效语言字段及字符串元数据 | 没有韩文／假名残留 |

63项韩文按证据分开，而非全部自动当作玩家正文：

| 分类 | 数量 | 处理状态 |
|---|---:|---|
| 图2碑文 | 1 | 用户确认可见，待修复 |
| UI动态拼接片段 | 10 | 待核所有消费者、语序和运行显示 |
| 独立过场笑声 | 1 | 待核字幕触发路线 |
| 源中注明不存在／未使用的台词 | 2 | 源注释不是不可达证明，仍待核 |
| 混合编码的接受／拒绝提示 | 2 | 待恢复结构证据 |
| `삭제` 删除占位 | 24 | 待核引用，不计为24条已确认玩家正文 |
| 编辑器字段、显式测试、占位邮件 | 23 | 有依据单列排除，仍保留原值和字段身份 |

额外新增4个非韩文待核记录：`MC2NpcTalk.Default.Default`、
`MC2Quest.Default.Default`、`MC2Quest.Q07_qube_1.no_0` 的英文默认值，
以及 `MC2Game.ItemName` 的混合编码串。因此v36共67条处置记录：
**1 confirmed-player-gap＋43 pending＋23 excluded，未决44**；
63是韩文字段数，67不是“67条确认漏译”。完整逐项清单在本轮 `REPORT.md` 和 `MODIFIED.json`。

另对未成为字段的文档行复核：UnrealEd的两条韩文分号注释独立记录。
`Core.int` 6559字节为 opaque-8bit，其唯一非ASCII字节是版权行 `0xA9`；
CP1252严格可逆解读为©，CP949严格解码失败。没有据此改动通用解析器的编码判断，
自动结果仍显式保留1个opaque主文档覆盖项，不能输出假“全部已解决”。
JPN／KOR替代语言库、配置、既定KAN／LT等术语和同形汉字不机械计为主线漏译。

## 审计工具与复现

`tools.audit_text_residuals` 保留旧 `--require-classified` 行为，新增：

- `confirmed-player-gap` 必须附截图来源／SHA；工具只验证元数据格式，**不自动解释图片**。
- `PENDING`、`EXCLUDED`、`CONFIRMED_PLAYER_GAPS`、`UNRESOLVED`、`OPAQUE_PRIMARY_DOCUMENTS`。
- 显式登记的非韩文未决记录也进入输出，不因没有脚本命中被丢弃。
- `--require-resolved` 遇未决记录或opaque主文档退出1；无问题才退出0，输入错误退出2。
- 跨盘观察元数据不一致、值SHA漂移、字段缺失继续报错，不静默合并。

语言策略为 `locales/zh-Hans/omission-screen-v36.json`；v34/v35历史快照不改。
按阶段364命令从当前recipe生成新的文本子集，然后：

```powershell
$inputs='build/phase-366-residual-audit/text-inputs/inputs.json'
$policy='locales/zh-Hans/omission-screen-v36.json'
python -B -X utf8 -m tools.audit_text_residuals `
  --inputs $inputs --inputs-sha256 (Get-FileHash $inputs).Hash.ToLower() `
  --policy $policy --policy-sha256 (Get-FileHash $policy).Hash.ToLower() `
  --project-root . --require-resolved --output build/residual-audit-new.json
```

当前预期输出 `PENDING=43 EXCLUDED=23 CONFIRMED_PLAYER_GAPS=1 UNRESOLVED=44
OPAQUE_PRIMARY_DOCUMENTS=1 RESULT=UNRESOLVED`，退出1。这是审计正确拒绝“已解决”，
不是把游戏文本修成中文，也不是扫描程序异常。

## 双盘包内文本与图像／动画边界

本轮完整执行结果：**4,145个物理包成员、2,551个不同有效内容，全部完成结构筛查，
解析错误／unknown包为0**。实际独立输入为7,709,065,216字节，首尾来源摘要复验通过。
输出38,888个字符串结构候选（不是38,888条漏译），其中38,690个计数FString、
198个未验证指令边界的VM宽串候选；完整资源账本在 `packages/census-r2/report.json`。

候选按原字节／邻接字段头再独立复解分类：22,630素材来源路径、1,568名称表ID、
12,418制作注释、1,581编辑器连接／标签、**50个需消费者调查的文本字段**，
以及198个未证VM候选和443个无类型二进制候选。分类项之和为38,888。
最后两组保持未定，不当作“没有文字”；不能仅凭Texture／Model载体名断言它们不可显示。

新增50条文本候选版本化登记在 `locales/zh-Hans/omission-package-findings-v36.json`：
**13个资源、15种文本、50个逻辑字段，按双盘成员展开为62处**。
其中StyleName 11、QuestName 27、PlayerName 3，以及Startup中的ItemName 2、
Description 5、Subject 1、SpecialReward 1。包括`대포`、三类任务原名及旧测试样例。
所有记录均为`pending-consumer-verification`，精确字节与邻接StrProperty头成立，
但没有声称完整对象链、实际读者或运行可见性已经证实；带Test路径的9项也没有直接排除。
这50项与主INT的44项未决**分属不同载体清单**，不把它们合称94条不同的玩家漏译。

DLC的6个包另检出855个结构候选：657注释、196素材路径、2个纹理载荷深处的短串巧合候选；
最后2项保留未定。DLC真正字幕／武器字段的正文绑定结果见上节，不用注释数量代替字幕残留数。

本地执行源码身份见`packages/execution-source-identity.json`：r2运行后增加了输入守卫、
范围说明及重叠owner防御，匹配算法不变。旧运行源码由修改记录反向重建，明确不是预执行
快照；`final-guards.json`对本次全部成员和38,888候选补验最终守卫、字节及0重叠结果，
不冒充最终文件的第二次完整扫描。

新增通用 `tools.audit_package_strings` 按双盘原始inventory与当前recipe构造有效资源视图。
逐盘核对整盘SHA、目录区段及全部当前资源SHA，再按**有效内容SHA**去重解压；
每盘物理成员独立记录，相同内容共享解码，同名不同内容不合并。输出保存全部物理成员、每包解析状态、精确逻辑偏移、值／序列化
SHA及owner。错误包单列unknown，不能把未解析当无文字。

扫描器检查全logical内长度／终止符成立的UTF-16LE FString，以及export载荷中的UTF-8
FString；另记录Function/State内的0x34宽串候选。长度上限分别为4096／512单位，
后者没有自动证明VM指令边界。UTF-8包头name表、其他编码、任意原生格式与图像像素
均不是此算法的已覆盖语义。候选还须按实际字段头区分ObjComment／Desc、素材来源路径、
普通文本与二进制巧合，不能把韩文路径、制作注释算成玩家漏译。

可重放命令（输出目录必须全新）：

```powershell
$recipe='build/phase-365-omission-repair/prepared/recipe.json'
$policy='locales/zh-Hans/omission-screen-v36.json'
$lzx='build/lzx/native-verified/ue3_lzx.dll'
python -B -X utf8 -m tools.audit_package_strings `
  --recipe $recipe --recipe-sha256 (Get-FileHash $recipe).Hash.ToLower() `
  --policy $policy --policy-sha256 (Get-FileHash $policy).Hash.ToLower() `
  --inventory ("1=build/disc1-hashed.json="+(Get-FileHash build/disc1-hashed.json).Hash.ToLower()) `
  --inventory ("2=build/disc2-hashed.json="+(Get-FileHash build/disc2-hashed.json).Hash.ToLower()) `
  --lzx-library $lzx --lzx-library-sha256 (Get-FileHash $lzx).Hash.ToLower() `
  --project-root . --output-dir build/package-string-census-new
```

图像／动画另核对现行身份：29项此前修复（13影片／8标签／8前缀）、16份源计划、
54当前成员及35份旧视觉QA证据SHA全部匹配。8前缀重新解析成品逐值核对；
4020帧离线视觉检查／原生回读证据属于前轮，本轮没有重新逐帧查看。13个resident与10个历史未解码
纹理、31个英文默认值的运行可见性、39个非UI原生载荷、15个函数metadata profile
继续留在覆盖账本。未知载荷与旧审计成品的逐项SHA相同不等于语义已解释。

既有入口66／volume37个字图别名绑定当前载体，两组有重叠；
`UI-20261107-02`独立大章节卡仍未结，不能被普通地图目的地或入口图冒充解决。
教程内嵌示意小图、15张技能保留图、Boss字样继续按用户已有决定单列。
证据为本轮 `visual-coverage/REPORT.{md,json}`；这次全资源文本筛查不是全游戏像素、
全流程运行或所有文字编码的穷尽证明。

## 三态、保留与收尾

三态针对审计策略的独立副本：旧策略／旧工具重现63项已分类、退出0；
新策略／新工具显式报告44项未决、退出1；哈希守卫恢复另一个副本后，旧分类行为和原摘要恢复。
`MODIFIED_FILE.json` 及版本化v36仍保留新状态，不回滚游戏、存档或配置。

证据根：`build/phase-366-residual-audit/`。四产物为 `MODIFIED_FILE.json`、
`DIFF_FILE.patch`、`VERIFICATION.txt`、可执行 `ROLLBACK.sh`；逐条精确命令、输入、
字面输出、退出码、回滚摘要及重新打开记录都在验证文件中。
没有游戏资源变化，原一键入口保持原身份；没有启动游戏，也不声称本轮解决了截图问题。
