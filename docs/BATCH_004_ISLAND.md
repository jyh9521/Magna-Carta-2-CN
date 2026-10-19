# 第四批：洞窟、守护者与海岸防卫

日期：2026-10-19。新增308条draft，累计841条INT草稿；本轮仅文本资源离线回填。

## 连续场景覆盖

- CSMB00_21/22/25/31/50共84条：公主到访、同伴介绍、进入洞窟、寻找梅莉莎、守护者与北部军反应。
- CSMB01_05/07/11/15/17/21/25/31/47/48共151条：朱特苏醒、力量与失忆、家人、海岸防卫、
  风属性状态、伤员/陷阱/燃烧瓶、战败及撤退。
- Ch01_0/Ch01_1村民共68条：战前反应、战争背景、任务标记、北部军进攻及村民避难。
- 关联名称5条：艾尔加两份独立姓名字段、修恩扎伊特、青灵森林、润喉糖。

本批分类为300条dialogue、3条narrative、5条name。
CSMB01_07两句和CSMB01_17一句自言自语单独分类narrative，不改成对他人发言。

**Verified / Coalesced coverage：** INT内CSMB00_*与CSMB01_*的427条可提取剧情值目前全部有draft。
对应Ch00_*/Ch01_*的156条NPC值已有155条draft，剩余1条为上一批记录的未知反斜线条目，继续保留原文。
这个完成度只针对上述Coalesced文档/section，不包含动画字幕、任务文档、xxx内嵌或图片文字，
不表示完整游戏第一章已经全部翻译或通过画面验收。

## 用词与校验

既有533条逐ID保持不变；累计841条，18,176条INT原值中其余17,335条不变。
新词表由59增至75项candidate，不自动提升reviewed或跨作继承状态。
新增艾尔加、修恩扎伊特、青灵森林/海岸、死亡弩炮、穿刺蠕虫、属性KAN、连环术师、
眩晕、沉默、润喉糖、绷带、燃烧瓶、陷阱、瞄准圈及屠杀者艾尔加。
艾尔加短名与“屠杀者艾尔加”称号是不同术语ID和form，原两个姓名字段也保留各自资源ID。
眩晕的敏捷/回避下降及沉默的技能禁用按对白分别翻译，不自行改成其他状态效果。

所有新增源值逐条检查数字和A/B/X/LT/LB/RB/RT/BACK键位的内容/顺序，
保留RT+方向键选择物品、X键使用和A键投掷确认的区别。
任务提示的[!]标记逐条计数保持一致，不把功能标记改为中文标点。
继承硬换行只通过每条source_count/target_count=0显式移除；其他标记仍按顺序校验。
不因字体容量缩短/删改译文，不增加空格或手工换行伪造排版通过。

## 重建与证据

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/island-batch004/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -v
python tools/check_repository.py
```

输出必须全新。当前workflow显式组合readability-fix、batch-002/003/004四个不重叠计划，
所有依赖使用LF字节hash；两盘各自核验原容器后共享同一份累计译文，不合盘、不复制整盘。
历史533条工作区保留为基线，原始资源保持不变。

本地build/batch-004-verification中：BASELINE_FILE.int是533条版，MODIFIED_FILE.int是841条版，
DIFF_FILE.json保存308条增量及源/基线/新hash；ROLLBACK.sh在独立副本恢复533条版，主修改文件保持841条。
VERIFICATION.txt记录精确命令、输入、字面输出、exit、测试与提交/远端身份。

**Runtime pending：** 本轮未更新字库/TOC或刷新可玩包，也未启动模拟器。
现有一键入口、原版对照、存档、用户配置和runs保持不变，不能把离线回填当作游戏画面通过。
独立动画字幕仍为49条既有draft，其余另行推进；下一批接阿巴泽特到访与对应NPC/任务。
