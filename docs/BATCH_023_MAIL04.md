# 第二十三批：E04库布邮件与署名

日期：2026-10-19。新增INT59条draft，累计3,834条；200项candidate术语。
同阶段csm04两份14cue已经覆盖；全部独立字幕仍为141/315cue，本批不重复修改。

## 范围与限定覆盖

- MC2QubeMail/E04_001–029共29封邮件，分别翻译29个_Sub主题与29个_Con正文。
- MC2CharacterName/Default/Igton关联姓名1条，统一为伊格顿。
- 分类29 mail_subject、29 mail_body、1 name。所有新增ID与前22份计划不重叠。

Verified / source/offline：当前INT的E04_前缀58个字段均有draft。整个MC2QubeMail共235个原字段，
当前只有E04的58个已译，不能声称所有邮件或第四章全部文字完成。B04共10字段、Q04共2字段仍需
核读与当前剧情的关联；E02/B02/Q02等较早前缀以及其他章节也还有缺口，Test字段是否面向玩家未确认。
既有CSMB04 411、Quest04_186、Ch04_Abazet242、Compose/Chapter04 68条均保持。

## 邮件格式与上下文

29封正文保守保留全部248个源硬换行及空段落位置，不应用对白去硬换行策略；
E04_018_Sub保留源尾随空格1个。这里验证的是源结构和回填一致性，尚未证明每一行的游戏内功能或排版。
主题中的系列编号及ASCII括号保留；180、1152、3000和LV2保持字面，方括号数量和边界不动。
邮件按不同收发阶段逐封翻译，不把寻找公主、归队、哨兵情报遗失等内容改成当前主线的最终状态。

匿名信的怀疑、传闻、科普系列的世界传说与人物自述保留叙述来源，不当成工程研究或官方史实证明。
阿尔戈两封感谢信保留后悔与反对无差别灭族的不同层次，不替角色简化立场。
先女王为公主生母有明确源文支撑；其姓名暂译伊芙琳，不回头暗改其他计划。
新增伊格顿、惠西斯、阿维斯贝尔克、惩戒者、卡利达、伊芙琳6项candidate，均未人工定稿；
惩戒者是攻城兵器名称的候选译法，尚未核对官方英文或跨作身份。

## 验证、收尾与接续

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/mail04-batch023/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。双盘INT原件hash不变，59条新值回填一致；旧3,775条保持，14,342条仍为源值。
独立副本回滚恢复3,775条基线，主MODIFIED_FILE.int保留3,834条；错误hash输入拒绝且不变。
干净Git index源码测试、67项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
字幕profile和18份计划逐字节保持旧HEAD，本批未重读完整ISO，不将旧字幕证据称为新增验证。
主证据、基线、回滚与测试日志位于build/batch-023-verification；完整原文/容器不进入Git。

只清理已核实可再生成、无入口依赖的验证缓存，保留原盘、配置、存档、runs、当前包及必要研究/回滚证据。
不生成ISO/整盘副本，不自行启动模拟器，不刷新字库/TOC/可玩入口；离线成功不是游戏验收。
下一批先核读B04/Q04共12个邮件字段的场景关联与格式，再从CSMB05_001接第五章正文与相邻字幕，
同时持续审计其他邮件和未覆盖文字；不重复E04邮件或已译的主剧情/NPC/任务。
