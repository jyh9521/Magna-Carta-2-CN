# 第九十四批：任务收束与关联世界文本（合批254条）

日期：2026-10-20。新增INT254条，累计9,609条draft；共享candidate453项，另1项历史字幕来源记录不变，未人工定稿。本轮按用户要求改为150–300条左右合批，批内格式校验后统一完整验证、清理和推送。

## 范围与语境

- 三组完整任务58条：03_397_0元气恢复剂22、09_zepi_3雷之试炼23、10_zepi_4风之试炼13；Quest/common完整12条，关联Item4条。
- 同阶段及既有场景关联CharacterName剩余101条、FieldName剩余16条、UI/information剩余63条一次补齐。CharacterName/Unknown源只有问号，保持原值并登记held，不猜身份。
- 186名称、49对白、9系统提示、3任务说明、3目标、2菜单选项、2物品说明。32对白显式去硬换行；205功能字段保留布局。Styles/X/Y、8个%s、QUEST大小写、[]、材料3种/2朵、第1/2哨所数字及三处源尾空格保持。
- 梅雷孢子源明确采自背上植物；药尚待制作，不译成已经制作。旧解毒剂/神奇蘑菇Item不改；strange_Drag来自阿维斯商人，不凭药物词组与塞蕾丝汀任务强行绑定。
- 公主已通过雷之试炼但得不到帮助、两位魂灵已经选别人均依源保留；角色关于欺骗与王位认可的自述不是考据事实。雷神/雷之魂、神之形貌的生物、神殿/石板说明中的祭坛各依源措辞，不合并成机制断言。
- common的将来/已经无法继续两种提示分开；护送跨区或存档重读会失败的警告保留功能换行。Source角色名不由英文key补信息：女婿不按Sun译儿子、孩童不按Kidgirl补性别、派驻商人不按black补黑市；所有重复姓名分别保留ID。
- UI按实际源值：Lab_power制动装置、Lab_Warp动力装置、IceSwitch水之开关、两个Shallof键实际酒桶/水桶；不得按key反向补壳或冰。FieldName地图/房间名不等于运行绑定实测。
- 新13项candidate：帕因、赫尔加、雷之魂、风之魂、风暴石板、梅雷的植物孢子、元气恢复剂、王室之魂源变体、古代之魂、深层界、克拉普斯、排列之室、荒野森林。旧440项不改；크랩퍼스与旧클로퍼스异拼分别克拉普斯/克洛普斯，不擅合。真勇等旧候选仍未官方核定。
- NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、全部旧译/held/重复occurrence保持。余下原值含编辑工具/样本，不等于玩家待译量，也不表示全文完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/quest-world-batch094/workspace
python build/batch-094-verification/verify_resources.py baseline
python build/batch-094-verification/verify_resources.py modified
python build/batch-094-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT原始SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
254条回填一致，旧9355条保留，8567条其余原值未改；隔离回滚恢复9355，主文件仍保留9609。
基线1320、修改/干净index1326测试各skip1；235输入锁、164工作区文件重建一致、715份index导出复核，错误hash回滚拒绝且目标不变。
只清理绝对路径内经核实可再生成、无入口依赖的干净源码测试pyc，保留原盘/配置/存档/runs/当前包/必要基线/回滚/研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线不代替游戏验收。提交推送后核对远端一致和工作区干净，CI仅记录实际可读结果。
