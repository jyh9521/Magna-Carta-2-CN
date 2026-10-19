# 第七批：司令部会面、新命令与狩猎任务

日期：2026-10-19。新增112条draft，累计1,501条INT草稿；131项术语均为candidate。

## 范围与格式

- CSMB02_37/38/38_1/38_2共71条，包含后缀分支：会面、致歉、卡蒙德实验与新命令。
- Ch02_Abazet连续索引122–141共20条，本城累计142/276条。
- Ch02_227_0共19条，另有阿巴泽特港口、柯塔马雷2条关联地点。
- 分类：104 dialogue、2 narrative、3 name，各1条quest_description、quest_progress、quest_objective。

任务DES保留2个功能换行；`QUEST%s:`和三个`%s`不变，3只目标保持原数值。
CSMB02_38末尾两条内心独白单列narrative；实验场景不补写未明说的人物身份。
劳德短名与司令官称号、破甲、拉普斯变种、炸弹及地点合计新增7项候选术语。

Verified / offline：原1,389条逐ID不变；18,176条INT中16,675条保持原文。未知转义、重复NPC key及旧字幕不变。
本批不代表整章、整城或全游戏完成；不把自动校验当作人工审核或游戏显示验收。

## 可复现重建

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/orders-batch007/final-workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出路径须全新；workflow锁定七个不重叠计划及依赖hash，八份原资源导出80份目录。
本地build/batch-007-verification保存BASELINE_FILE.int、MODIFIED_FILE.int、DIFF_FILE.json、
VERIFICATION.txt及hash守卫ROLLBACK.sh。实际独立副本回滚恢复1,389条版本，主修改文件仍为1,501条。
双盘输出、旧译保护、格式标记、数值、功能换行、干净源码测试及164文件重建一致性分别验证。

本轮只离线回填文本，未更新字库/TOC/可玩包，不启动游戏或生成ISO/整盘副本。
保留原盘、配置、存档、runs和入口依赖；工具清理装配临时目录，保留必要研究/回滚证据。
整理、测试、提交推送并核对后，按TRANSLATION_QUEUE.md继续下一批。
