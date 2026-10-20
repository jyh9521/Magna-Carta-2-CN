# 第一百零九批：塞蕾丝汀与露装备（155条）

日期：2026-10-20。从已提交108批接续162候选，新增155条INT draft，累计12,614；新增53项candidate共1071，旧1018保持。六字段缺值加一无需变化的简述共7held。

## 完整功能组与源上下文

- 塞蕾丝汀弓30、香器30、胸针25；露手里剑27、刀23、背包20合批。名称54、装备说明101。旧露608刀三字段保持，不重复统计。
- 完整分母：弓30/30、香器30/30、胸针25/27、手里剑27/27、刀26/27、背包20/24有draft；547胸针及644/646背包D/S缺防御数值六字段完整原值/hash held，不局部翻译、不按邻近数据补数。
- 606_katana_S为刀与功能尾换行，中文候选无需变化，初次格式检查拒绝unchanged source后整条held；不补空格或改名凑已译。可解释的606全述单独draft，未称刀所有字段已有draft。
- 600等源단도译短刀，603/606源刀译刀，不按英文key改太刀；604攻击180而605攻击140各依源，不按数列修齐。
- 643전격与644電撃同译电击背包，ID/各自说明独立；646ロック依仅本人可开的源语境暂译锁扣背包，缺值D仍完整held，不把命名判断当游戏机制验收。
- 527弓、507香器、625及626手里剑、606刀的尾空行/单空格保持；529弓S开头空格、627手里剑D尾空格保持，不补空白属性行。138加号、101功能换行及全部数字/行边空白保持。
- 香器复用既有아로마类型；马雷族、阿维斯、手里剑与能力名称复用。雨师、冰花、死星等按名字与雨神/冰气/死亡之星语境候选，传说/据说与究极措辞保持，不核为官方译名或实际效果。
- Verified仅指资源源值/格式/回填，不证明游戏显示、数值、装备条件、人物/物品身份或机制。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-109-verification/reviewed-workspace
python build/batch-109-verification/verify_resources.py baseline
python build/batch-109-verification/verify_resources.py modified
python build/batch-109-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填一致，旧12459和5562其余源值保持，所有历史held与新held7独立核对。
基线1410测试，新增六项source-free合同覆盖分组/held/布局/源差异/候选/锁与字幕。合批完整验证包含164文件逐字节复现、索引导出干净源码测试、独立回滚和错误哈希拒写。
隔离回滚恢复12459条旧译，主MODIFIED_FILE仍12614；四实物及精确命令/输入/字面结果/退出状态见build/batch-109-verification/VERIFICATION.txt。
只清理已核实绝对路径的干净源码可再生成pyc；保留原盘/配置/存档/runs/当前包/依赖/基线/回滚/研究。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235及44字幕315cue保持，离线成功非游戏验收。验证清理提交推送核对后，回到开篇至第三章场景感想和各角色可选交谈249候选（220含语言内容、29纯省略号保留待核），关联Valuables按场景补齐，不将含工具/样本的5562原值当玩家待译总量。
