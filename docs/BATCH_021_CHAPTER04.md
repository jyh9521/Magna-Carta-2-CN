# 第二十一批：第四章主剧情尾段与剩余任务

日期：2026-10-19。新增INT162条draft，累计3,616条；192项candidate术语。
同阶段csm04两份字幕14cue早已覆盖；全部独立字幕仍为141/315cue，本批不重复修改。

## 范围与限定里程碑

- CSMB04_164/170/180/190四场54条，170末尾2条为内心叙述。
- Ch04_Abazet索引121–150共30条，累计151/242条，下一条04_2243_00。
- 04_4222_0/4225_0/4232_0/4239_0/4239_1/4239_2六任务77条。
- MC2Item/Valuables/stolen_kamond关联名称1条，统一为被盗的卡蒙德。
- 分类140 dialogue、2 narrative、1 menu、7 name、各6/3/3条quest_description/progress/objective。

Verified / offline：当前INT MC2CSMB的CSMB04前缀411条均有draft；当前INT MC2Quest中
04_前缀15个section共186条均有draft。这里的完成只针对上述两个精确前缀，
不包括仍未译完的城镇（151/242）、Compose、邮件、硬编码、图片文字、其他locale或全部第四章可见文本。
不把静态回填或分母覆盖等同于游戏验收。

## 上下文与格式

朱特关于归属的内心叙述、梅莉莎的战争立场及回忆按角色原文翻译；不增写信件来源、阵营真相或动机。
卫兵明确10名，饰品报价500SID；X/Y菜单顺序、Styles标记及1个功能换行保持。
五份含换行的任务DES各保留4/1/2/2/1个功能换行，第一份含空段落；第六份无源硬换行。
进度前缀`QUEST%s:`保持，三条进度的占位符个数分别1/3/1，不套用统一模板。
04_4239_2/04_4239_com_01保留源尾随空格1个；4225_02/03近似委托仍是两个独立ID，不合并。
南部关卡、荒野南部和远距离弓箭建议保持，不添加来源没有的按键、人物或数量限制。
91条继承硬换行使用显式计数策略去除；旧功能布局、未知转义、空白pay、纯标记和重复key保持。
仅新增被盗的卡蒙德1项candidate，其他术语复用；未做人工定稿或跨作同一性确认。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/chapter04-batch021/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。双盘原始INT hash保持，162条新值回填一致；旧3,454条不变，14,560条仍为源值。
独立副本回滚恢复3,454条基线，主MODIFIED_FILE.int仍为3,616条；错误hash目标拒绝且不变。
Git index源码干净导出后运行完整测试，63项依赖锁逐一核对；两次工作区164个文件hash一致。
本轮保留已修复的GitHub CI取参考及跨盘fixture流程；推送后的四组云端检查另外确认，不以本机通过代替。
字幕profile和18份计划逐字节保持旧HEAD，本批未重读完整ISO，不把旧字幕证据称为新回填验证。
本地主证据、测试日志、基线和独立回滚副本在build/batch-021-verification，完整原文/容器不提交。

只清理核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
不生成ISO/整盘副本，不自行启动模拟器，不刷新字库/TOC/可玩入口；离线成功不是游戏内验收。
下一批优先补齐Ch04_Abazet索引151起的91条，再从CSMB05_001接第五章剧情及相邻独立字幕，
并核对同阶段Compose/邮件等文字覆盖，避免正文前进而遗漏同阶段NPC。
