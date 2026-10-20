# 第一百零四批：材料、场景动作与配方（220条）

日期：2026-10-20。221候选审读后新增220条INT draft，累计11,636；新增79项candidate，共787项，旧708项保持。1条未知转义保留held。

## 完整功能组与语境

- Ingredient剩余28字段、FieldAction剩余34字段、Recipe可解释的158字段合批；名称/说明/简述各保留独立ID。Ingredient38/38、FieldAction56/56已有draft；Recipe158/159，未称全部配方完成。
- Recipe/1458_recipe_D源含未知反斜线序列`\공격`，不猜为漏写n，不局部改写其材料数量或属性；整条源值与SHA256保留，名称/简述仅按各自可解释源回填。
- Recipe1412全述的全角．、1419简述精神+5与抗性+5之间无空格、1434全述引号内前导空格均保留。1417简述攻击/防御+20而全述+15，分别依源，不自动修齐。
- 配方的效果、材料列表和制作说明是不同字段。保留全角ＬＶ/（）与半角括号/数量/空格/加号；单位개译个，不改数字或原括号形态，不把材料列表改写成效果值。
- 源标记174个加号、40个百分号、29处ＬＶ、6对全角括号、24对半角括号、1个全角．、49对「」、53个冒号、112处功能换行及逐行边界空白保留。
- 配方名保留冒号/原间隔；术语表只录被制作物的基础名，避免以“配方:”前缀限制后续Accessory复用。Accessory数字key与Recipe数字key不同，不按序号推断对象身份或实际合成关系。
- 雪水晶有限核读JPN Recipe1424及Accessory1303实际名/同列能力；清水之香核读JPN对应字段；不推广为全表多语对齐。猫猫炸弹复用INT及旧候选，JPN为火晶爆弾，不覆盖INT源名。
- 复用红色宝石、猫猫、马雷族、属性/状态及雷电/漩涡炸弹旧译；同名空瓶、麻痹陷阱仍分节/ID保留。仅翻译源功能，不补概率、持续时间或目标种类。

## 格式校对与保留事项

按既有非剧情行级标点规则调整陷阱/炸弹说明的单句句号，功能换行与源语义不变；初次格式校验失败的记录保留在本地研究输出。
未知转义、配方数值差异和实际显示/合成机制的置信度分开：这里Verified仅指资源源值、回填及静态约束；游戏行为未验证。
相关记录见PITFALLS及KNOWN_ISSUES顶部；旧译与旧708候选未静默修改。

## 重建、验证、清理与接续

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-104-verification/final-workspace
python build/batch-104-verification/verify_resources.py baseline
python build/batch-104-verification/verify_resources.py modified
python build/batch-104-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
双盘回填相同；旧11,416条和6,540个其余源值保持，全部历史held与新held1条保持原值。隔离回滚恢复11,416，主MODIFIED_FILE保留11,636。
基线1380测试，本批新增六项覆盖/held/全角形态/源差异/候选/锁回归；完整命令、字面输出和退出状态见本地VERIFICATION.txt。
只清理已核实可再生成且无入口依赖的隔离源码pyc；原盘/配置/存档/runs/当前包/基线/回滚/研究保持。
不合盘、不生成ISO或整盘副本、不启动模拟器，不刷新字库/TOC/入口；邮件128/235、44字幕315cue保持，离线非游戏验收。
推送核对后继续Accessory名称及关联属性/状态说明等完整功能组；剩余原值包含工具/样本，不当作确定玩家待译量。
