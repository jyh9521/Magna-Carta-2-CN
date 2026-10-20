# 第一百一十批：开篇至第三章场景与队员交谈（227条）

日期：2026-10-20。从109已提交批接续，开篇至第三章249候选中220含语言内容，加关联Valuables7字段，新增227条INT draft，累计12,841；新增2项candidate共1073，旧1071保持。29纯省略号保留原值/hash held。

## 连续场景与关联资源

- Chapter00训练/休息/珍珠28，Chapter01守岛/治疗/陷阱28，Chapter02狼人据点/峡谷/晶柱/交通55，Chapter03柯塔马雷/人质/香水仪式71；同阶段五名有实际语言内容的角色可选交谈38，按场景状态串读。
- Chapter00 28/28、Chapter01 28/29、Chapter02 55/55、Chapter03 71/71有draft。开篇PartyTalk：朱特8/13、阿尔戈10/14、洁菲10/15、克罗塞尔7/12、塞蕾丝汀3/8、露0/4；差额全为本批纯省略号held，不给未出场/无内容状态编话。
- 胡安信、炸弹箱、猫猫铃铛/钥匙、阿塞莉娜之泪、尤尼昂之角共7物品字段与场景合批补齐；既有名称保持，bomb_box与带空格词面폭탄 상자同候选炸弹箱但独立ID。
- 显式分类：对白99、叙述81、教程22、菜单选项10、任务进度8、物品说明6、物品名1。保留所有源功能换行和逐行边界空白，不将内心半角括号或功能选项改成自由叙述。
- Chapter01治疗计数4 / 3与5 / 3各依源，不修上限；陷阱进度的紧凑斜线、按钮LT/A/B/X及Styles中的X/Y选项顺序保持。3天后与2楼保留数字，不改为中文数词。
- Chapter03香水提示保留左/右/相邻/两端及橙/黑/绿/不变色关系，只翻译提示，不推导具体答案或声称已验证游戏颜色机制。
- 复用反哨兵部队、风息、阿巴泽特、柯塔马雷、马雷族、公会联盟、死亡弩炮、固有技/必杀技、过热/超限/连锁终结等；阿巴泽特先核对terms.json，再仅修订本批未提交草稿，初始术语审读工作区保留。克罗克仅音译候选，不认定官方或怪物机制。
- 117功能换行、28处Styles标签、4对方括号、78对半角括号、7波浪线、22斜线（含标签及进度）和所有数值/键位保持；对白/叙述保留角色声口，非剧情选项/教程遵守既有标点规则。
- Compose整体626/921、Item1582/1630有draft，不代表整个游戏文本翻完。Verified仅指源值/格式/回填，不证明实际显示、触发或游戏机制。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-110-verification/reviewed-workspace
python build/batch-110-verification/verify_resources.py baseline
python build/batch-110-verification/verify_resources.py modified
python build/batch-110-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填一致，旧12614和5335其余源值保持，所有历史held与本批held29独立核对。
基线1416测试，新增六项source-free合同覆盖分组/纯标记held/布局/数值与方向/旧术语复用/锁及字幕。合批完整验证含164文件逐字节复现、索引导出干净源码测试、独立回滚及错误哈希拒写。
隔离回滚恢复12614条旧译，主MODIFIED_FILE仍12841；四实物及精确命令/输入/字面结果/退出状态见build/batch-110-verification/VERIFICATION.txt。
仅清理核实绝对路径的干净源码可再生成pyc；原盘/配置/存档/runs/当前包/依赖/基线/回滚/研究保持。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235、44字幕315cue保持；离线成功非游戏验收。验证清理提交推送核对后继续第四章至结局其余场景/交谈及关联物品271候选（236含语言内容、35纯省略号待保留），已排除所有历史held；不把5335个含工具/样本原值当玩家待译总量。
