# 第十八批：王之证明、战后独白与杜南丘陵出击

日期：2026-10-19。新增INT169条draft，累计3,140条；183项candidate术语。
本阶段csm04两份独立字幕14cue已有draft，全部字幕仍为141/315cue，本批不重复修改。

## 范围与限定覆盖

- CSMB04_074/075/080/085/090五场91条：残党战后对话、王之证明、订婚谈话及杜南丘陵简报。
- 075末尾3条、080末尾3条为内心独白，显式分类narrative，不与对白混淆。
- Ch04_Abazet索引30–60共31条，完整接完04_250_00/01矿工话题；累计61/242条。
- 04_401_0机密文件13条、04_402_0营救阿尔斯13条、04_403_0支援南部军16条，共42条。
- 关联名称4条：王室之魂、黑刃要塞、阿尔斯、机密文件；关联双手剑说明1条，保留攻击+70属性行。
- 分类146 dialogue、6 narrative、7 name、各3条quest_description/quest_progress/quest_objective、1 item_description。

## 语义、术语和格式

新增王之证明、王室之魂、黑刃要塞、阿尔斯、机密文件5项candidate；系列引用命中不证明跨作同一性。
王之证明共有4片、修恩扎伊特已获两片，均按敌方角色的陈述翻译，不扩写为已验证历史或亲缘结论。
本场明确提到订婚和战后结婚约定，按本场原文翻译；不暗改上批的契约台词或补断双方感情。
杜南丘陵与杜南平原区分；两处哨所与任务第1哨所分别保留，晶柱转换发生于占领之后。
三份任务DES各保留5/1/2个功能换行，第一份保留中间空段落；武器说明保留1个属性行换行。
3条进度文本均保留QUEST%s空格/冒号和另两个%s；数字70、4、1及全部键位/控制标记逐条核对。
其余继承硬换行只按显式line_break_policy移除；未知反斜线、纯标记、空白pay、重复key与旧译不变。

## 重建、复核与接续

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/proof-batch018/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。双盘原始INT hash不变，169条新值双盘回填一致；旧2,971条保留，15,036条仍为源值。
独立修改副本回滚恢复2,971条基线，主MODIFIED_FILE.int保持3,140条；错误hash目标被拒绝且不变。
源码从Git index干净导出后执行完整测试；57项依赖锁从index逐一核对；两次工作区164个文件hash一致。
subtitle-profile与全部18份字幕计划逐字节保持旧HEAD，本批不重新读取完整ISO或声称新增字幕验证。
本地主证据MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt、可执行ROLLBACK.sh及测试日志均在build/batch-018-verification。
完整源文、容器和回滚副本不提交。清理仅处理确认无入口依赖的可再生验证缓存，原盘/配置/存档/runs/当前包/必要证据保留。

不生成ISO/整盘副本，不自行启动模拟器，不更新字库/TOC/可玩入口；离线成功不替代游戏内验收。
提交推送、核对远端与干净工作区后，从CSMB04_091和Ch04_Abazet索引61（04_251_00）继续。
同阶段剩余任务04_404_0/405_0/406_0等另批按完整上下文推进，不因一次提交宣称全篇完成。
