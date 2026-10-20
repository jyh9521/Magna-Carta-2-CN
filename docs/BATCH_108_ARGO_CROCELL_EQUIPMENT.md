# 第一百零八批：阿尔戈与克罗塞尔装备（184条）

日期：2026-10-20。第107批清理/提交/推送并核对HEAD远端一致、工作区干净后，直接接续194候选。新增184条INT draft，累计12,459；新增63项candidate共1018，旧955保持。

## 完整功能组与源上下文

- 阿尔戈斧31、锤33、护手31；克罗塞尔火球27、拳套31、KAN充能器31合批。名称63、装备说明121；旧421火球及445充能器名字/全述保持，简述补齐各自实际源。
- 完整分母核对后，斧31/33、锤33/33、护手31/33、火球29/33、拳套31/33、KAN充能器33/33有draft。未声称缺值组或全物品完成。
- 308斧、428火球、407拳套、349护手D/S共8字段以加号结束而缺数值，完整原值/hash held；不局部翻译、不按相邻数列或JPN补数。
- 424火球S空白、名字毒炎球与中文候选字面相同，两字段保留原值且不计新增；D的致命中毒说明单独draft。首次格式验证拒绝unchanged source，失败计划/日志保留研究证据，不用添空格/换字绕过。新held合计10。
- 309斧全述攻击+ 240、简述攻击+240分别保持；1000吨锤名称数字不变。181加号、120功能换行、数字顺序与所有逐行边界空白保留。
- 323일류전结合INT幻觉说明及本地JPNイリュージョン有限核读候选幻象；420赤炎球/423火舞只核读对应实际名，不推广为数字key全表对齐，不覆盖INT精神数值。
- 349源名竜人译龙人护手，残缺D提到特雷瓦族不据此改名或确认实体关系。308斧残缺D含阻碍复活描述仍整条held，不据片段声称已验证效果。
- 复用特雷瓦族、阿维斯、KAN充能器、斧/锤/火球/拳套/护手及能力候选。传说/据说与究极等源叙述限定保持；非剧情单句行无内部标点则不加句末句号。
- Verified仅指资源源值/格式/回填，不证明实际显示、数值、装备/异常状态机制或官方中文。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-108-verification/reviewed-workspace
python build/batch-108-verification/verify_resources.py baseline
python build/batch-108-verification/verify_resources.py modified
python build/batch-108-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填一致，旧12275与5717个其余源值保持，历史held和新held10独立核对。
基线1404测试，新增六项source-free合同覆盖分组/缺值及空白和同字源名/布局/源差异/候选/锁与字幕。合批完整验证包含164文件逐字节复现、索引导出干净源码测试、独立回滚和错误哈希拒写。
隔离回滚恢复12275条旧译，主MODIFIED_FILE仍12459；四实物及精确命令/输入/字面结果/退出状态见build/batch-108-verification/VERIFICATION.txt。
只清理绝对路径已核实的干净源码可再生成pyc；原盘/配置/存档/runs/当前包/依赖/基线/回滚/研究保留。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235及44字幕315cue保持，离线成功非游戏验收。验证清理提交推送核对后继续塞蕾丝汀/露装备162候选；剩余物品210原值另存待审，不将含工具/样本的5717原值当玩家待译总量。
