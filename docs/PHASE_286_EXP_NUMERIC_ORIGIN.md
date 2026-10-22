# Phase 286：经验值字符串来源补证

## 已验证：两处都是原生类型转换，不是逐位标签数字

本次只新增补充文件，不改变既有候选、证据或hash锁。`build/phase-286-ui-research/exp-origin-proof.json`与`exp_origin.py`给出完整输入hash、函数hash、类型声明及15字节赋值窗口的精确偏移/hash/字节/AST。

- `MC2PawnInterfaceBattle.GetFullExp` export18084：输入`fExp`为FloatProperty参数18083；本地`ExpNum`为StrProperty18081。
- `MC2PawnInterfaceBattle.GetExp` export18093：本地`fExp`为FloatProperty18090；本地`ExpNum`为StrProperty18089。
- 两函数给各自ExpNum的Let赋值均只有一处，精确形状为`ExpNum = PrimitiveCast(0x53, PrimitiveCast(0x44, fExp))`。内部0x44是FloatToInt，外部0x53是IntToString。短窗口重建逐字节匹配，而不是仅搜索函数名或猜测数字用途。

类型转换编号对照核对自Eliot van Uytfanghe的MIT Unreal-Library固定提交8236c39b79e30887a487ecf9b018204e430a5ebc：[CastToken定义](https://raw.githubusercontent.com/EliotVU/Unreal-Library/8236c39b79e30887a487ecf9b018204e430a5ebc/src/UnrealTokens.cs)。当前取得的完整文件SHA256为`5f4ff4c33cf580596199dfb13353e9eae18f8361b3b8611b919bace0776c3165`，与项目既有`references/scripted-ui-research.lock.json`相符；这里只独立核对格式，不集成上游运行时代码。

## 对实际回填的含义

已证整段`tempStr = ExpNum $ "<Strings:MC2UI.Battle_Log.GetEXP>"`中的前半段是float→int→string所得裸数字字符串，不是phase283的`GetStringFromNumber`所生成的`<Strings:MC2UI.Number.Num_数字>`标签链。两条经验值赋值表达式内没有调用、没有任何数字tag构造，完整表达式已重建。

因此中文后缀`点经验值已获得`直接接在转换后的数字后，不需要移动数字、重建标签、删除标签、额外空格或特殊占位符。例如`100点经验值已获得`只是说明拼接结构，不伪称实际执行了float边界或游戏渲染测试。浮点溢出、NaN、负数及具体截断边界没有在游戏VM实测，本次翻译不会改变数值转换链。

如果未来其他调用者实际提供逐位Strings标签，后缀仍在整串完整标签之后，不插入标签内部；但该假设不是本次这两个消费者的来源，本次不据此推广其他消费者。

## 实际重放

`python build/phase-286-ui-research/exp_origin.py`输出`PASS ExpNum numeric origin;2 typed float->int->string assignments;no digit tags;reopened`，exit0。重放先验证原逻辑包、table、固定上游token文件及两函数完整脚本hash，再检验属性类型与唯一完整赋值窗口，最后重开JSON。本次未启动游戏。
