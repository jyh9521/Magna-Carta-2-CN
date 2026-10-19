# 第四十四批：贝尔福特市民与星光平原支线

日期：2026-10-20。新增INT105条，累计6,002条draft；274项共享candidate及1项独立字幕candidate。
字幕28份194/315cue、邮件98/235字段保持，均未人工定稿。

## 范围与语境

- Quest/07_703_0求婚第一段20、07_703_1第二段32、07_705_0饥饿孩子16、07_721_0周边危险14、07_702_0御寒15，共97字段。
- CharacterName斯特萝/拉兹2字段，Valuables红色宝石/战斗口粮/怪物皮及各自说明6字段。
- 分类79 dialogue、10 name、5 quest_description、4 quest_progress、4 quest_objective、3 item_description。

Verified / source/offline：新增ID与前43批无重叠；Quest/07_由20增至117/150字段，尚余33字段。
斯特萝/拉兹、红色宝石/战斗口粮/怪物皮、野猪人/地行兽新增7项candidate，复用既有星光平原等译名。
红色宝石只回填当前Valuables/redjam；Recipe/Accessory同字面但未证明同一用途，不凭名字自动扩大修改范围。
求婚表演、男方表白及女子的条件台词按角色立场保留；必须在斯特萝站到拉兹身边时进行、
明日婚礼及游戏男性/非特雷瓦条件不改写，不作为现实建议或全知叙述。
孩子父母不见了仍为失踪，不擅改成死亡；饥寒、居民援助和临时清怪的限度依原对白。

10只怪物、3张皮、Quest/QUEST大小写、%s占位符与ASCII括号/斜线保持。
五条DES保留4个功能换行；29条普通对白有显式去硬换行策略。所有旧译、未知值与重复key occurrence保持。
CSMB07主线282/282、Compose40/40、城内NPC41/41维持不变；其他支线及邮件仍有缺口，不称全章完成。
字幕profile/28计划与独立字幕候选逐字节保持，不重读完整ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/city-quests-batch044/workspace
python build/batch-044-verification/verify_resources.py baseline
python build/batch-044-verification/verify_resources.py modified
python build/batch-044-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新105条双盘回填一致，旧5,897条保留，12,174条仍为源值；独立回滚恢复5,897条，主修改产物保留6,002条。
错误hash回滚拒绝且不变；干净Git index源码测试、119项依赖锁、164文件重建一致性与四组CI分别核对。
完整原文、容器、差异与本机验证证据只留build/batch-044-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究与回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批核读07_720_0拜泽恩线索、07_crocel_0/1/2家族支线和同阶段邮件，关联名称/物品按实际源ID补齐。
