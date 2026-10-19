# 第四十三批：泽罗哈潜入准备与第七章主线收尾

日期：2026-10-20。新增INT76条，累计5,897条draft；267项共享candidate及1项独立字幕candidate。
字幕28份194/315cue、邮件98/235字段保持，所有译文/术语未人工定稿。

## 明确范围

- CSMB07_50泽罗哈情报33、07_60克罗塞尔故乡15、07_70梅莉莎16，共64条。
- NpcTalk/07_velfort剩4条698_0、720_0/e0/e1；Compose/Chapter07_39/40技能学习两条。
- Item漩涡炸弹、晶柱控制装置及说明、研究所通行卡及说明5字段；Skill暴雪之刃1字段。
- 分类68 dialogue、4 name、2 system_message、2 item_description。

Verified / source/offline：新增ID与前42批无重叠；CSMB07主线282/282、Compose40/40、城内NPC41/41均有draft。
不是第七章所有可见文字完成；07_701_0追踪20字段已有draft，其他支线和邮件仍待接续。
漩涡炸弹、晶柱控制装置、哨兵研究所通行卡、暴雪之刃无空格/有空格两种源拼写，新增5项candidate。
两种技能源拼写保留各自ID与hash、复用同一目标；不混同其他近似名称技能。

泽罗哈仅记得“大概中间”的石像，不改成精确保证；3个炸弹及补给3个保持原数量，仅按游戏道具原用途翻译。
控制装置对白说任意晶柱，Item描述说北部军晶柱，分别保留来源范围，不暗改为统一机制结论。
研究所道具源名为通行卡，说明/对白称钥匙，两者保留原差异；Item尾随空格保持。
克罗塞尔家人死亡、朱特道歉与归责是角色叙述；梅莉莎离队意愿、对方否认知情与排斥反应按原对白，
不提前补写幕后身份或现实医学解释。两条技能学习提示保留弓/斧装备条件及两个功能换行。
39条普通对白有显式去硬换行策略；字幕profile/28计划与独立字幕候选保持，不重读完整ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/infiltration-batch043/workspace
python build/batch-043-verification/verify_resources.py baseline
python build/batch-043-verification/verify_resources.py modified
python build/batch-043-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新76条双盘回填一致，旧5,821条保留，12,279条仍为源值；独立回滚恢复5,821条，主修改产物保留5,897条。
所有历史held/未知格式/旧译/重复key occurrence保持；错误hash回滚拒绝且不变。
干净Git index源码测试、117项依赖锁、164文件重建一致性与四组CI分别核对。
完整原文、容器、差异和本机验证证据只留build/batch-043-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究和回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批补第七章同阶段市民/星光平原支线及相关名称、物品，再接第八章连续剧情。
