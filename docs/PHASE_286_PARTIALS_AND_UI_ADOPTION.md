# 第286阶段：40条既有尾项实际回填

## 实际修改

batch-119新增40条INT草稿：18条装备缺值说明、普通攻击第1至9击的9条后缀、1条经验值后缀、六名恢复者的12条HP前后缀。全部进入正式workflow和双盘资源，不停在研究候选。累计14095→14135，原14095条目标逐值不变，未计划原值4081→4041；315条独立字幕不变。

这是未完成尾项的完整组，不拿空白、标点、编辑器字符串或已是中文的毒炎球凑150条。7个完整装备分区219字段的原始语境，以及相关完整脚本表达式均已核对；219不是219条新增翻译。当前所有译文仍是draft，不自动升级人工定稿或游戏验收。

## 缺值不等于已知文字不可译

18项装备长短说明保留原有ASCII `+`、缺失的数值、每条一个字面`\n`和308_ax_D的尾随空格。不补攻击/精神/防御数值，不增加源中没有的属性行，不假定游戏会自动追加数值。对应日文字段也缺数值，没有可导入的“修正值”。详见[完整装备核查](PHASE_286_PARTIAL_EQUIPMENT_ADOPTION_REVIEW.md)。

沿用已有斧、火球、拳套、背包、胸针、护手、肩甲、阿维斯族、特雷瓦族和连环术师；名称“龙人护手”和说明“特雷瓦族”仍是原字段的两种内容，不强行合并。

## 拼接顺序由实际消费者决定

**Verified / static**：四个完整赋值分支重建为“样式标签包围的战斗流派名＋动态Combo_N标签”。GetStyleName的六角色12个返回分支，以及Core.Concat_StrStr的两个字符串参数/返回和native token112均已核对。因此9后缀采用`的普通攻击<Styles:MC2UITextStyle_0>第N击<Styles:/>已可使用`，不凭key猜成角色名。

**Verified / static**：两个EXP消费者均为ExpNum＋GetEXP；ExpNum唯一赋值来自FloatProperty经FloatToInt再IntToString，非阶段283的逐数字标签循环。采用后为`100点经验值已获得`，不偷偷把后缀动词移动到数字之前。转换链与数值没有修改。见[数值来源](PHASE_286_EXP_NUMERIC_ORIGIN.md)。

**Verified / static**：七个恢复函数的完整赋值为Recover_1＋strHP＋Recover_2，且strHP来自nAddHP:IntProperty转字符串。中段是HP数值，不是目标角色名。六组一次性采用“恢复者名＋恢复了”及“点HP”，示例“别西卜恢复了100点HP”。三组不同consumer使用相同词面仍保持独立ID。

MC2Game逻辑包和原生映像的ASCII/UTF16BE直接引用全量核查中，12个恢复标签共有14个直接命中，全部落入上述7个表达式；原生映像完整标签和6词干未命中。这个结论不覆盖其他包或动态构造键，不宣称不存在其他消费者。Huaren、GetSP、GetItem2和其他助词仍保留。见[消费者证据](PHASE_286_UI_FRAGMENT_CONSUMERS.md)。

阿斯塔罗斯、普尔森是按精确韩文名采用的音译草稿，候选记录明确未验证官方定名，也未建立跨作同一性；其余四名复用已有译名。

## 持久证据与复现

- `locales/zh-Hans/batch-119.json`及review保存40条源hash、目标文本和完整六对原子片段约束。
- `locales/zh-Hans/candidate-decisions/ui-string-assembly-evidence.json`保存精确函数/属性引用、完整脚本hash、必要的短表达式窗口、类型和AST、直接引用覆盖边界，不提交完整游戏包。
- `locales/zh-Hans/candidate-decisions/preserved-partials-adoption.json`明确取代这些ID的历史原值状态；历史held报告不改成“当时已译”，也不永久阻止后续合法采用。
- 新增45号语境profile仅纳入新40项；45份profile重锁，功能换行保护1502→1520。字形需求没有新增码点，复用阶段285七Font，不重造无变化字库。

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/NEW-workspace-batch119
python -m unittest discover -s tests -q
python tools/check_repository.py
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
```

真实基线、修改、隔离旧源码、干净源码、双盘27/29资源重建和独立重放、原测试根hash保护增量刷新及四实物均记录在`build/phase-286-verification/VERIFICATION.txt`。字体、字幕和原文对照保持；不生成ISO/完整游戏副本，不启动模拟器，配置、存档、runs与必要研究/回滚证据保留。

## 接续门槛

“仅剩성쇄”只适用于之前的章节术语追踪，不能用它代表整个汉化项目的完成状态。本轮从完整18176字段重新审计才找到这些实际未计划语言项。接下来仍处理其他UI拼接、单反斜杠/损坏文本的实际读取链、图片和硬编码文字覆盖，以及最终游戏验收；不把编辑器/空值/数字原值机械计作漏译，也不凭文件名宣称运行时不用。
