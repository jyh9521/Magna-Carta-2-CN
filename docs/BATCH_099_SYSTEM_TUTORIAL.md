# 第九十九批：强化、设置、影片与完整战斗教程（200条）

日期：2026-10-20。新增200条INT draft，累计10,571；共享candidate475项，旧468项不改，全部仍待人工定稿。

## 范围与核读

- MC2UI采集/失败提示6、武器类别1、LiveMsg系统提示12；MC2UI_Field剩余104（强化18、影片目录53及设置/信息等）；晶柱传送13；完整剩余教程64。按完整功能组合批，不用数字/按键样本凑数。
- Battle_Log、System_Log、diction、Level_Up的45个主语/助词/对象/数值拼接片段登记held，包括先前两条HP片段；没有验证调用点或中文组合词序，因此全部保持源值。SID字面保持，不计新译。
- 影片标题按实际源值，不根据数字key补剧情；water_attribute字段源为冰属性，译冰，不按英文key改水。파국译灾变，不译正面的破局。
- 教程保留50%、5秒、1.5倍、2倍、3人限制、四大属性数量与源条件；不以译文断言算法实测。所有功能换行、空段、逐行首尾空格/制表符、Styles与按钮顺序均保留。
- 新增候选：贝里艾尔、卡蒙德盘、疗愈术、冰爆箭、冰冻箭、救援请求、协同请求。统一复用队长、普通攻击、场景动作、连锁/连锁超限/连锁终结及原有地图/人名；不冒充官方译名或人工reviewed。
- 数字校验首次指出Tutorial_Scene_33/Text_2少保留一个字面4，已修正并重新完整构建；早期工作区保留作研究，最终以verified-workspace为准。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-099-verification/verified-workspace
python build/batch-099-verification/verify_resources.py baseline
python build/batch-099-verification/verify_resources.py modified
python build/batch-099-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

Verified / offline：双盘原始INT SHA256仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
双盘回填相同、旧10,371译文保留、7,605个其余原值不变；隔离回滚恢复10,371，主MODIFIED_FILE保留10,571。
源免费回归覆盖200条范围、旧前缀/全部held、候选、功能布局/按钮/数值及字幕锁；完整运行结果和命令退出状态保存在本地VERIFICATION.txt。

不合盘、不生成ISO/整盘副本；原盘、存档、配置、runs及当前入口依赖保持。清理仅限经绝对路径和依赖核实可再生成的输出；必要基线/回滚/研究证据保留。
邮件128/235、44字幕315/315已提取cue不变；没有刷新字库/TOC/可玩入口，没有游戏内验收。推送核对后接续技能/卡蒙德等完整功能组。
