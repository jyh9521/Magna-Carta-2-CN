# Phase 287：Localize原生绑定与裸反斜杠的限定证明

## 已验证：从Core声明到完整原生包装函数

本轮新增的是实际调用绑定，不是再次发现已知的`\n`/`\t`字面值。调查只读原版映像，不启动游戏、不修改游戏资源。主要证据为`build/phase-287-escape-research/escape-binding-proof.json`，重放入口为同目录`verify.py`。

- 原生映像：`build/xex-native-verification/final/disc1-pycryptodome.bin`，SHA256 `d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`。地址采用映像VA、PPC大端指令，不采用PE raw pointer。完整函数范围由仓库`tools/ppc_pdata.py`独立读取CE/PPC packed pdata，保留其原有格式归属和边界限制。
- 初始化表精确8字节行`0x8320ecf8 = 821595dc82517b18`。前一word指向UTF16BE完整名称`intUObjectexecLocalize`，后一word指向代码`0x82517b18`，不是近邻字符串推断。该代码完整pdata范围为`0x82517b18–0x82517ca4`，SHA256 `b7dba3b0f37193364fa4329e1f19146e135e998a42ca675afc0766acd6503c31`。
- `build/phase-283-verification/Core-logical.bin` SHA256 `5ac2c9745bdf6220ddb3dbe898ef88b1c8ac84c882b06816e8257ad5b4c6e2a9`及`Core-tables.json` SHA256 `3cd1cd977e7552b202ae88ee2f10db74d3056d4770a7ddbed7de8ead26434c0b`中，export981是`Object.Localize`，native/static标志存在。其三个按声明顺序的StrProperty参数是`SectionName`(980)、`KeyName`(979)、`PackageName`(978)，返回值977亦是StrProperty。
- 包装函数三次VM参数求值分别写入frame `+0x78/+0x68/+0x58`。`0x82517c28/0x82517c40/0x82517c5c`分别把PackageName/KeyName/SectionName装入r6/r5/r4，`0x82517c6c`直接调用`0x823915e8`。`0x82517c78`把所得FString复制到VM result。完整包装函数已保存为`function-82517b18.txt`。这些证据闭合`Core.Object.Localize`声明→命名原生行→包装代码→本地化读取函数的静态链；不宣称实际VM执行。

## 已验证：读取完成后的处理仅按精确模式分支

本地化函数完整pdata范围`0x823915e8–0x82391a6c`、289指令、SHA256 `dd18e65a3675b8ae390de651137c600bac2fe90267b681563c2a620b0815a7e3`。重放不仅检查一个窄窗口，还锁定并完整解码下列完整函数：

|范围|作用及限定证据|
|---|---|
|`0x823915e8–0x82391a6c`|本地化入口：按语言路径循环，读配置；后处理、输出复制及早退路径完整可见|
|`0x8238d958–0x8238da78`|模式替换helper，按传入模式长度寻找匹配，复制前段并追加replacement，再复制余段；调用者仅在完整`\n`或`\t`模式存在时调用|
|`0x82398b00–0x82398bf0`|分隔符helper：寻找传入的`###`，可输出左、右段；本调用只传左输出、右为0|
|`0x82517b18–0x82517ca4`|上述完整VM Localize包装|
|`0x826b6af8–0x826b6c5c`|另一完整dot-triplet读者；静态直调已证，具体类和Strings入口仍未绑定|

读取返回后的`0x823918a4`起，函数先查找精确UTF16BE模式`\n`(0x82151f74)，有匹配才用LF(0x820aa1f0)替换；再查找精确`\t`(0x82151f64)，有匹配才用TAB(0x82151f7c)替换；最后以`###`(0x82152054)调用上述分隔符helper，再复制FString输出。完整选定代码中没有以单个U+005C作为通用转义前缀逐字符删除/解析的额外分支。全局条件早退只复制传入key，不运行这一后处理链。

这里的结论是**读配置之后这段完整后处理不会仅因一个裸反斜杠而删除它**，不是“整个游戏所有反斜杠都按字面显示”。`###`本身有截取语义，不能推广为所有未知序列都不处理。

## 对本轮5条原文的具体意义

输入是hash锁定的`build/disc1-selected/MC2Game/Localization/Coalesced.int`，SHA256 `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。以下5条每条都含一个非`\n`/`\t`的裸反斜杠，且没有`###`或`\t`：

- MC2CSMB/CSMB03_20/voc_csmb_0320_50
- MC2Item/Recipe/1458_recipe_D
- MC2NpcTalk/Ch00_1/00_101_00
- MC2Quest/06_603_0/603_0
- MC2Quest/06_zepi_1/order_2

重放从原始容器按真实字段提取，而不是使用拟译文本代替原文，核验5个源ID/source hash，并在**以后处理入口文本等于该原字段为前提**的离线模型中执行两个精确替换及`###`左段选择。五条结果都恰好保留一个裸反斜杠；原`\n`只在模型中成为LF。完整模型输出存于证据JSON，不修改源字段或译文。翻译仍应逐字保留原来的裸反斜杠和原来的`\n`，不自行改成换行、空格或删除。

这与已有phase284保留未知分隔符而采用周围可读文字的约定兼容；新增证据没有要求为了不相关的未知读者继续冻结已可读语言，也没有授权猜修分隔符。

## 尚未闭合的边界

1. 两条配置读取调用都通过全局对象`0x832559ec`及vtable `+0x18`间接调用（调用位置`0x82391700/0x823917e4`）。本轮未绑定具体vtable目标，也未证明该配置reader在返回前完全不处理反斜杠；因此上述5条模型只对读取后的选定后处理负责。
2. `0x826b6af8`将输入按`.`拆为三段，依次取+0x0c/+0x18/+0x00字段到r4/r5/r6，并于`0x826b6be4`直调同一本地化函数；其代码指针出现在`0x821c5b8c`。这为后续Strings读者调查提供具体入口，但本轮未把该表绑定到具体UE3类，未证明所有`<Strings:...>`都经过此函数，故不将“dot-triplet形状”当成已完成Strings入口绑定。
3. 后续字体、标记解析、渲染与游戏画面仍需各自证据；本轮没有用静态模型替代游戏验收。

## 重放与反例检查

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE=1
python build/phase-287-escape-research/verify.py
```

字面输出：

```text
PASS Core.Object.Localize fixed native row + 3 typed parameters + complete wrapper;5 complete pdata functions;5 post-lookup bare slashes preserved;config getter/Strings entry remain unbound;no execution;reopened
```

exit0。脚本先锁定原映像/Core/原INT输入、初始化表精确行、名称完整边界和五个函数hash，再核对声明及关键数据流、提取5原字段、输出模型，最后重开证据JSON和完整反汇编。对隔离内存中的函数副本翻转一个字节后，其全函数hash校验按预期失败；原映像未写入。先前phase286记录只给出本地化函数本身，本轮新增的Core声明/初始化行/包装数据流链与完整helper控制流是新的证据。
