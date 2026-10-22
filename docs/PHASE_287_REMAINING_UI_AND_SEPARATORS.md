# 第287阶段：剩余日志语法与保留分隔符实际回填

## 实际采用

batch120新增13项，累计14148 INT草稿；旧14135目标逐值保持。此批是剩余字段完整有证子组，不以空值、删除标记或已译项凑150条。

- 七个UI字段成套采用：Objective_0/1为“已”，GetITEM/GetWeapon/GetItem3为“获得”，SkillSubject为“的”，GetSkill为“习得”。14函数的完整typed赋值窗口支持“名词短语＋已＋获得/习得”；人物与技能名间为“的”。原脚本ASCII空格与数值不改。47处直接标签引用全在已核窗口中；MC2Game/原生指定对象之外和动态构造键不作穷尽断言。见[实际消费者](PHASE_287_REMAINING_UI_CONSUMERS.md)。
- 五个裸反斜杠字段翻译周围可读语言，逐个保留U+005C及既有字面`\n`，不猜作换行。完整INT/JPN五section每盘各272字段已提取；CSMB03_20的日文有局部键偏移，不按同键替换。配方1458沿用力量与迅捷戒指，原5/3/1/2、全角ＬＶ、加号和数量保留，不根据别处面板值纠正原配方。
- CSMB09_20 INT06采用“困扰我们的这一切灾难，\n都是因为这个世界的KAN循环出现了严重问题。”。四来源hash、69字段完整场景、12对顺序语义对应支持其可读主句，JPN对应07而非06。`감Ｒ`确切缺失修饰未还原；不添加日文特有“力量之源”，不修原文/原文对照字节。该译文是保守草稿，不宣称损坏源已完整恢复。见[损坏源复核](PHASE_287_MALFORMED_TEXT_REVIEW.md)。

## 可复现技术推进

Core.Object.Localize export981经精确初始化表行intUObjectexecLocalize、完整VM包装、三StrProperty参数和返回结果，绑定到原生0x823915e8。五完整pdata函数锁hash，查读配置后的n/t替换及###截取；裸反斜杠在这段后处理没有单独删除分支。配置reader间接vtable目标、所有Strings入口与渲染仍未闭合，不把后处理模型说成游戏执行。见[原生绑定](PHASE_287_ESCAPE_CONSUMER_BINDING.md)。

通用validate_catalog增加RETENTION_TOKEN用于保留未知单反斜杠，既不锁下一语言字符，也不放行删除/新增/变成已知转义或跨控制码重排。TOKEN仍只表示已知非字面标记，字形需求继续包含裸U+005C，避免把保护的字符错误地从可见字库审计删除。八个自制测试覆盖令牌、显式换行策略、markup、可见码点和实际Coalesced重建拒绝删除。工具没有本作ID或中文特例。

MC2Game.int/.jpn的三异常宽串保持整个文档原字节。四份390字节负载一致，独立负长度UTF16LE读取与现解析器吻合；原负载11处三字节边界和末段异常不是可用“补NUL”盲修的问题。不凭零直接引用宣称它们运行时不用。

## 数据与验证

- batch120/review、remaining-ui-and-separator-adoption.json、remaining-ui-assembly-evidence.json保留精确源/目标/证据hash及七字段原子joins。
- 新46号profile仅13新项；46份profile按新canonical plan重锁，1523个功能换行记录保护。原有45份目标不改。
- 新字形需求为空，七字体与315字幕复用；双盘独立构建27/29资源，单轮现有目录仅文本/TOC和入口元数据增量刷新，无ISO/整游戏副本，无游戏启动。

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/NEW-workspace-batch120
python -m unittest discover -s tests -q
python -m unittest discover -s tests -p test_unknown_separator_retention.py -q
```

基线1806、修改1818、隔离旧源码1806、干净源码1818项（各1跳过），双盘独立重放、当前/原文对照资源、旧27资源隔离回滚、完整依赖hash及Git提交推送的实际证据放在build/phase-287-verification/VERIFICATION.txt。四实物均重开；正式新译保留、回滚只在独立副本验证。游戏画面/最终人工验收仍不以离线测试代替。

## 下一步

剩余19个MC2UI字段继续按真实消费者处理，尤其HuarenRecover两个直接标签及其中间对象；其他任务未完片段、성쇄、坏MC2Game文档、嵌入/图片/硬编码文字和最终运行验收仍需推进。已采用Objective/日志和五反斜杠语言不再仅因历史held快照重新排队。
