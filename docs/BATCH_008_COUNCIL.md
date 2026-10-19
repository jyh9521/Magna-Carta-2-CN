# 第八批：总司令部军议、战前决心与炸弹运送

日期：2026-10-19。新增131条draft，累计1,632条INT草稿；134项candidate术语。

## 范围与上下文

- CSMB02_39/40/41共102条，依次为会议传令、军议争论和队伍战前对话。
- Ch02_Abazet索引142–161共20条，本城累计162/276条；承接前批同貌人物闲谈。
- Ch02_249_00炸弹运送任务8条，含原始02_295和02_249混合key；不重排或改ID。
- MC2CharacterName/Default/ASentinel关联名称1条，沿用“反哨兵部队”。
- 分类：125 dialogue、2 narrative、2 name、1 quest_description、1 quest_progress。

保留守护者与哨兵的区别，沿用洁菲、克罗塞尔、劳德、希昂·雷格拉尔、反哨兵部队等候选译名。
会议对话是本作角色立场，不将角色推断写成外部已证实设定。CSMB02_41末两条独白单列narrative。
新增恸哭之门、总司令部、炸弹包3项candidate；无人工reviewed或跨作同一性升级。
任务进度保留`QUEST:`前缀；任务DES无继承硬换行，本批不改既有功能性换行。
猫猫的喵尾音保留，仅出现在对应角色台词。

## 验证与重建

Verified / offline：两盘源资源hash相同，原1,501条逐ID不变；18,176条中16,544条保留原文。
重复NPC key、异常转义、旧49条独立字幕保持不变；本批不代表整章、整城或全游戏完成。

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/council-batch008/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新；workflow锁定八个不重叠计划。原资源保留盘别来源，80份catalog不复制两套译文。
本地build/batch-008-verification保存基线、MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt和ROLLBACK.sh。
回滚只对独立副本运行并恢复1,501条版本，主修改资源保持1,632条；另核对干净源码测试和164文件重建一致性。
清理仅处理核实可再生成的验证缓存，保留基线/回滚/研究、原盘、配置、存档、runs和入口依赖。

本轮未更新字库/TOC/可玩包、不启动游戏、不生成ISO或整盘副本；离线验证不代替游戏内验收。
每批整理、验证、清理、提交推送并核对后，按TRANSLATION_QUEUE.md持续接续。
