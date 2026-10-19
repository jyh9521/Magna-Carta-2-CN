# 第九批：强化教学、老狐峡谷与人质营救

日期：2026-10-19。新增144条draft，累计1,776条INT草稿，143项candidate术语。

## 连续剧情与关联文本

- CSMB02_43/50/60/60_1/61/63六场72条，含60_1分支与最后5条内心独白。
- Ch02_Abazet索引162–181共20条；城镇累计182/276条。
- Ch02_251_0营救人质43条，含接受/拒绝/进行/三名获救者/总部奖励和重访分支。
- 克蕾尔、修亚伦、公会联盟及两份成员名称、水色湿地、杜南丘陵、精华提取和强化标题共9条关联名称。
- 分类：125 dialogue、5 narrative、10 name、1 menu、1 quest_description、1 quest_progress、1 quest_objective。

Verified / offline：当前INT Coalesced的CSMB02全部585条可提取剧情已有draft，包括后缀分支；
该统计不包含独立动画字幕、NPC、任务或其他资源内嵌文字，不等于整个第二章或游戏完成。

## 术语与格式约定

卡蒙德盘、插孔、精华提取、强化、卡尔玛、饰品加工、克蕾尔、修亚伦、杜南丘陵新增9项candidate。
沿用哨兵/守护者、晶柱、反击、公会联盟、水色湿地等用词，不将候选升级为人工审核或官方命名。
强化说明区分镶嵌卡蒙德、盘面扩展与武器强化；精华提取保留“有时可得特殊卡蒙德”的条件。
强化教学X/Y顺序与Styles标签及1个功能换行不变；任务DES保留6个功能换行和段落空行。
任务Resque字段保持原拼写，其`QUEST%s:`进度仅有1个`%s`，不套用击杀进度3占位符的假设。
非剧情任务字段按标点规则不添句末句号。三位获救者使用各自ID，不合并相同台词。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/canyon-batch009/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出路径须全新；workflow组合九个不重叠计划。原1,632条逐ID不变；原18,176条中16,400条保持原文。
两盘源hash与回填结果一致；未知转义、重复NPC key和旧49条独立字幕不变。
本地build/batch-009-verification保存基线、MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt和ROLLBACK.sh。
独立副本回滚恢复1,632条基线，主修改资源仍为1,776条；另验证585条剧情覆盖、干净源码测试、164文件重建一致性。

仅清理核实可再生成的验证缓存；保留原盘、配置、存档、runs、入口依赖、必要基线/回滚/研究证据。
本批未更新字库/TOC/可玩包、不启动模拟器、不生成ISO或整盘副本；游戏显示另行验收。
推送核对后从CSMB03_20继续；同阶段NPC/任务与独立字幕仍按TRANSLATION_QUEUE.md推进。
