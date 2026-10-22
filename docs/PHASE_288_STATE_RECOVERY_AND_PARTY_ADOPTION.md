# 第288阶段：状态内恢复、队伍日志及未完任务实际回填

## 已回填的11个字段

batch121新增11条，累计14159 INT草稿，旧14148目标逐值不变。两条Huaren恢复片段成对译为“修亚伦恢复了”＋实际数值＋“点HP”；七个共享主语/升级/入离队字段成组采用“已”及自然动词后缀。既有work_E“制作完成！”通过源/目标/批次hash锁作不变依赖，不重入新批次凑数量。Guest与既有教程统一称“临时同伴”。四个日志行首字面\n全部保留。

另两条11_302_0未完任务字段，完整INT18/JPN19字段跨两盘核对后只翻译可读部分：302_6“现在由我处理的 ”、302_7“所以，请亲自到海底的 ”。两条都保持未完定语和末尾ASCII空格；不补事务、洞窟或后半句；中文连接语只形成未完定语，不声称复原缺失原句，也不从日文对应空值补内容。这不是完整原文恢复或画面验收。

## 新的源绑定，不重复旧研究

- [Huaren证据](PHASE_288_HUAREN_AND_UI.md)：State-owned Function20544完整249字节、8连续语句，先记旧HP，调用AddHealthPercent(0,10.0,省略可选Bool)，实际前后HP差nAddedHP>0后转strHP并拼接两标签，再NotifyShowLog。不是之前七函数的nAddHP，也不是目标人物名。两个精确标签直接引用在指定MC2Game/native对象内已覆盖；其他包/动态键未排除。
- [队伍日志证据](PHASE_288_PARTY_LOG_GRAMMAR.md)：三个完整原生消费者、16个完整native/helper及两叶窗口、四个typed升级赋值、plain%s实际状态/跳转表和UTF16输出链已核。明确FString赋值不等于追加；拷贝左侧/追加右侧/回写各有完整helper证据，不再靠lis/addi邻近候选推断。既有work_E不变，真实数值、名字列表、Comma、None和脚本ASCII空格保留。

这些都是静态结构/控制流证据，不是实际执行、内存分配成功或游戏画面的证明。

## 通用读取器修复

原function_header只允许Class直接拥有的Function，确实漏掉了Huaren的State函数。新增function_owner_scope限定支持“直接Class”或“一层本包Core.State→本包Class”。空所有者、非精确类型、嵌套/循环State、导入/无效Class父节点仍拒绝。函数头、脚本大小、friendly FName、尾部、参数/局部属性链的原检查没有放宽。

h.outer继续表示defining Class，新增declaring_owner保留真实State。parse_function_metadata分别报告二者；bounded UI decoder也从该根Class读取实例作用域，不扩大其受支持字节码语法，不伪装成通用State/VM解析器。--class CLI仍只选直接成员，显式State函数需按对象定位。八个自制测试覆盖合法State、Class兼容、无效父链及原头尾拒绝、有限脚本实例作用域；不含原版资产。

## 真正图片文字缺口已定位

[资产调查](PHASE_288_ASSET_TEXT_COVERAGE.md)新增实际看图/对象引用证据，不把正文草稿数当全游戏完成率：章节入口55740通过UI组件→材质→Texture2D闭合，原像素仍为韩文；独立UI_Title25/UI_Title_Jpn25是已知像素别名。战败Game Over/Press A Button为resident55656/55659与独立GameOver3/6成对图片。

12个已选UI/教程包789次Texture2D尝试、678严格解码、111明确未支持；这不是文字总数、逐张人审数或4145包完整覆盖。12个D2实际原资源与D1同hash，未重算整ISO，也没有生成整游戏副本。本轮只定位和验证图片，未声称已汉化图片；下一轮应实际实现有原像素/块守护、别名联动和隔离回滚的纹理补丁，而不是只追加研究文档。

## 结构化记录及验证

- batch121/review保存11个精确源/目标锁，两个原子组9成员；剩余2任务片段保持未完。
- state-recovery-and-party-adoption.json与recovery-party-assembly-evidence.json持久保存精简原生/typed证据、work_E旧批依赖和片段锁。
- 新47号语境profile只覆盖11新项；47份按新canonical plan重锁，1527功能换行记录受保护。新增字形需求为空，七Font及315字幕复用。

```powershell
python -m unittest discover -s tests -p test_state_function_metadata.py -q
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/NEW-workspace-batch121
python -m unittest discover -s tests -q
```

基线1818、修改1830、隔离旧源码1818、干净源码1830（均1跳过）；双盘27/29资源构建及独立重放、旧27项隔离回滚、当前/原文对照匹配、现有测试目录5文件hash保护增量刷新以及Git提交/推送/远端核对在build/phase-288-verification/VERIFICATION.txt记录真实命令、输入、输出及退出状态。四实物重开，正式修改保留；原资源、配置、存档、runs和必要研究/回滚证据不清除。没有游戏启动。
