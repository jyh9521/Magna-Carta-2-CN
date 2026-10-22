# 第288阶段：Huaren 状态内恢复日志成对回填

## 实际采用范围

`Battle_Log.HuarenRecover_1` 原值 `휴아렌이` 采用 `修亚伦恢复了`；`HuarenRecover_2` 原值 `의 HP를 회복했습니다.` 采用 `点HP`。两条必须通过 source-locked-atomic-fragments 成套进入同批，不单独迁移谓语。离线样例为 `修亚伦恢复了125点HP`。名称沿用 `terms.json` 的 `mc2-canyon-142` 候选“修亚伦”，不宣称官方译名或跨作品同一性。

## Verified：之前漏掉的 State-owned Function

来源是本地原包，不是字符串邻接猜测：`build/phase-282-verification/MC2Game-logical.bin` 的 export **20544**：`MC2PawnInterfaceBattle_Huaren.Huaren_Wait_SummonMonsters.HuarenSelfHeal`。函数序列化偏移8648328，脚本249字节。原 `function_header` 仅接受 Class 直接拥有的 Function，因此旧七个 AddHealthPercent 消费者没有包括此条。正式读取器现验证一层 Core.State → 本包 Class 所有权；本证据直接使用正式 `function_signature`，不篡改图表或跳过尾部检查。

所属链为 State20571 → Class20572 Huaren → Class19298 MC2PawnInterfaceBattle → Class17092 MC2PawnInterface。全部原始函数头、脚本长度、尾部 friendly name 和参数/局部属性链由正式读取器检查。脚本经有限语法连续覆盖249字节、8条语句；没有声称通用反编译器、VM执行或游戏验收。

| 脚本偏移 | 长度 | 精确静态表达式 |
|---:|---:|---|
|0|17|nOldHP = GetCurrentHealth(0)|
|17|17|AddHealthPercent(0,10.0,省略的可选Bool参数)|
|34|24|nAddedHP = GetCurrentHealth(0) - nOldHP|
|58|11|JumpIfNot(nAddedHP > 0)|
|69|13|strHP = PrimitiveCast0x53(nAddedHP)|
|82|103|tempStr = HuarenRecover_1 + strHP + HuarenRecover_2|
|185|61|对象/Context 链上的 NotifyShowLog(tempStr)|
|246|3|ReturnNothing / EndOfScript|

`nOldHP`20543、`nAddedHP`20542 均为 IntProperty；`strHP`20541、`tempStr`20540 均为 StrProperty。中段是两次有同样参数的 GetCurrentHealth 返回值之差转串，不是别处七函数的 `nAddHP`，也不是目标姓名或百分数。Core token112为 Concat_StrStr；147为 Subtract_IntInt；151为 Greater_IntInt；参数/返回声明逐一取自哈希锁定Core包。`0x53`转换语义沿用已锁定的上游CastToken来源和项目既有整数转串证据。

GetCurrentHealth 的MC2PawnInterfaceBattle声明返回Int，AddHealthPercent声明参数为Int/Float/可选Bool，NotifyShowLog声明接收Str。尾部Context引用Engine.Actor.WorldInfo、Engine.WorldInfo.Game、Engine.PlayerController.myHUD的导入符号，保留“导入声明类型”与“实际对象身份/动态分派已证明”的区别。本轮不执行恢复、不确认运行时数值、不把函数名字当作实现效果证明。

## Verified：直接引用覆盖与采用边界

精确完整tag在整个哈希锁定MC2Game逻辑包中各有一次ASCII引用，偏移8648463、8648513，均严格落在上述已证明的103字节赋值窗口。整个逻辑包UTF16BE及完整原生映像ASCII/UTF16BE均无该完整tag其他直接引用。该结果不排除其他包或动态拼出的键；证据字段 `dynamic_constructed_keys_excluded=false` 明确保留此局限。

GetSP、GetItem2和通信片段没有因本轮Huaren链而获得拼接证明，不连带猜填。旧七函数仅是不同消费者，不能据此把本条强行套成 `nAddHP`。

## 可复跑证据

运行（仓库根目录，未启动游戏）：

```powershell
$env:PYTHONIOENCODING='utf-8'
python build/phase-288-ui-research/replay.py
```

最后一行：`PASS Huaren: 249 bytes / 8 contiguous statements; typed nAddedHP delta -> strHP; 2 exact direct tags covered; 2 atomic translation candidates; no runtime execution`，退出状态0。

新证据目录 `build/phase-288-ui-research` 保留 input-lock、完整函数、候选、提交用精简adoption-evidence、原子review-groups。脚本核对原始输入哈希，重建每一语句窗口并再次打开全部JSON。提交用证据拟存 `locales/zh-Hans/candidate-decisions/recovery-party-assembly-evidence.json`，不包含完整包或游戏资源。父任务负责批次回填、双盘重建、控制码/字形、隔离回滚、增量测试目录刷新及提交推送。
