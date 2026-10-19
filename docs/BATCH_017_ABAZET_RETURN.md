# 第十七批：归返阿巴泽特与峡谷破障作战

日期：2026-10-19。新增INT150条draft，累计2,971条；178项candidate术语。
独立动画字幕仍为141/315cue：本阶段csm04两份14cue已在上批翻译，本批不重复修改字幕。

## 范围与限定覆盖

- CSMB04_001/010/030/040/050/070/073七场86条，按场景顺序从归城报告推进至峡谷残党交涉。
- Ch04_Abazet索引0–29共30条；该独立状态共242条，剩余从04_215_00接续，不复用旧章节ID。
- Ch02_291_00共20条破障任务、Ch02_291_01共14条三路进军状态，分别保留section和原key。
- 分类146 dialogue、各1条menu/name/quest_description/quest_progress；没有新增关联字段的猜测回填。

Verified / offline：当前INT的MC2Quest中，section以Ch02开头的条目除Ch02_296_00/pay空白字段外均有draft。
这是精确前缀范围，不表示全部第二章任务、Compose引导、邮件、硬编码或游戏内所有文字已完成。
CSMB03仍为687/688条（未知转义1条保留）；本批未重写历史草稿。

## 语义和格式

- 死亡弩炮、库布、卡蒙德、拉提族等复用既有术语。新增鲁哈尔特、猫猫炸弹2项candidate。
  鲁哈尔特来自地点列举；猫猫炸弹来自任务方括号简称，不把不同源词强并为特制炸弹同一字段。
- 女王身份以本场明确的“母亲/女王”称谓为依据；不据此暗改旧计划，不扩写契约的具体内容。
- 北侧小路、中央/南侧少量兵力扰乱与北侧集中主力保持；291_01中的292系列key保留原样。
- X/Y选择的Styles标记和1个功能换行保持；DES保持2个功能换行；[RT]、移动模式与场地行动顺序保持。
- 对白继承硬换行仅按显式计数策略移除；QUEST空格/冒号、数字、旧占位符和未知格式保留。
- subtitle-profile及全部18份字幕计划逐字节保持HEAD基线，本批不重新读取完整ISO或新增字幕回填。

## 可复现验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/abazet-return-batch017/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出目录须全新。双盘原始INT源hash保持；150条新值准确回填，旧2,821条逐ID不变，15,205条仍为原值。
独立副本回滚恢复2,821条基线，MODIFIED_FILE.int保留2,971条；回滚脚本拒绝错误hash输入。
源代码干净检出运行测试，所有依赖锁从Git index复核；两次工作区164文件逐一hash一致。
四份本地主证据、测试日志及副本回滚证据位于build/batch-017-verification，完整原文/资源不进入Git。

仅清理核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包、基线和回滚/研究证据。
不生成ISO/整盘副本，不启动模拟器，不刷新字库/TOC/可玩入口；离线成功不是游戏验收。
推送核对后从CSMB04_074、Ch04_Abazet索引30接续，随后按场景补齐下一阶段任务和独立字幕。
