# 第二十二批：第四章城镇尾段与场地念白

日期：2026-10-19。新增INT159条draft，累计3,775条；194项candidate术语。
同阶段csm04两份字幕14cue已覆盖，全部独立字幕仍为141/315cue，本批不重复修改。

## 范围与限定里程碑

- Ch04_Abazet索引151–241共91条，补齐该独立section242条；保留无04_前缀的原key与交错顺序。
- MC2Compose/Chapter04独立section68条：战前确认、行进限制、哨所简报、治疗、临时商店与场景衔接。
- 37条ASCII括号内心/行动念白和1条会议结束后caption分类narrative，共38条。
- 分类120 dialogue、38 narrative、1 menu；没有新剧情section、任务进度或猜测的关联姓名字段。

Verified / offline：Ch04_Abazet为242/242条draft，Compose/Chapter04为68/68条draft。
此前CSMB04前缀411条、MC2Quest的04_前缀186条保持。上述四个精确范围不等于整章完成：
本轮另核对到MC2QubeMail的E04_001–029共29封、58个主题/正文原字段，当前均尚未翻译，优先接续。
硬编码、图片文字和其他状态/locale仍不包含在这些计数中。

## 上下文与格式

保留NPC关于早晚不同作战阶段的原表述，不因当前主线已占领某地而改写仍要求出击、失踪或结盟的台词。
青月/黑角过往、哨兵与守护者的议论分别保留传闻、推论与疑问，不提升为工程研究事实。
露、劳德司令官、连环术师等复用现有译库。新增贝卡斯/雷卡斯两项candidate，分别对应
Chapter04_39的베카스与66的레카스；尚未确认同一Boss或源拼写错误，不自动合并或回填不存在的匹配姓名ID。

保留37条ASCII括号边界；选择菜单X/Y顺序、Styles标记及1个功能换行保持。
第2首都、2处哨所及第1/第2哨所的阿拉伯数字不改写成汉字数值；毒攻击、治疗、临时店铺和通行状态按源翻译。
96条继承硬换行使用显式计数策略去除；旧译、功能布局、未知转义、纯标记、空白pay和重复key保持。
本轮只翻译已有字段，没有给念白补造发言者或任务触发条件。

## 重建、验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/field-comments-batch022/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。双盘INT原件hash不变，159条新值回填一致；旧3,616条保持，14,401条仍为原值。
独立副本回滚恢复3,616条基线，主MODIFIED_FILE.int仍为3,775条；错误hash目标拒绝且不变。
Git index干净源码测试、65项依赖锁与164文件两次重建一致性独立复核；推送后另查四组云端CI，
不以本机通过代替GitHub结果。字幕profile及18份计划逐字节保持旧HEAD，本批没有重读完整ISO。
四份主证据及基线/回滚/测试日志存于build/batch-022-verification，完整原文/资源不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存，保留原盘、配置、存档、runs、当前包及必要研究/回滚证据。
不生成ISO/整盘副本，不自行启动模拟器，不刷新字库/TOC/可玩入口；离线成功仍非游戏验收。
下一批先核对并翻译E04邮件58个字段，按邮件的段落/主题/正文结构保留功能格式，再接CSMB05_001与相邻独立字幕。
