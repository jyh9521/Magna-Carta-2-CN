# 第一百零三批：特殊卡蒙德与恢复物品（296条）

日期：2026-10-20。新增296条INT draft，累计11,416；新增96项名称candidate，共708项，旧612项保持。

## 完整功能组与源差异

- 特殊卡蒙德34种/102字段，完整名称/简述/全述；Recover剩余194字段，既有13字段保持。当前Karmond309/309、Recover207/207均有draft，不代表其他物品、全部游戏文字或实际触发完成。
- 全量核读INT内日韩混合说明，不以韩文字符筛选当总量，不对照英文key改写实际源名或效果。
- 1719/1726全述未写敌方受体，未从简述补回；1727全述有“攻击时”条件，保留；1740–1742全述限定战斗中获得SID，简述不补来源。
- KAN消耗减少一/两/三个、重复效果不叠加；生成量/经验/SID/暴击伤害/命中率的百分比及普通攻击成功率分别处理。不把成功率改成命中率，不添加概率或未给的持续秒数。
- 沿用旧治愈/疗愈种子叶花系列、苏生丸对应苏生水及体力/耐力/状态用词；恢复速度提高与直接恢复不同，一名与全体不同，体力完全恢复与解除所有异常不同，不补复活。
- FrozenRemedy名源为凍傷用軟膏，说明源为凍結：分别译冻伤药膏/冰冻状态，不擅自统一。diarrhea名源天敵剤且描述脱力，译天敌剂/虚弱，不按key改腹泻。
- EmergencyBandage实际源蜂蜜水，不译绷带；Firecracker源空蝉长袍，不译爆竹；Matatabi源catnip译猫薄荷；Katuobusi源굴비译黄花鱼干，不按英文key改物种。
- 地面效果的全述/简述、各属性KAN的生成、喵语气分别保留；水英文key对应源冰之元素体，依源译冰，不改水。

## 格式与候选置信度

Verified / source：34个加号、44个百分号、101处功能换行、11对「」、4个~、数字与逐行首尾空白保持；字段与occurrence独立。
名称意译/音译均为candidate，未声称官方中文；源声明不是算法或实机证明。어지러움/스턴同译与旧批次异写的统一QA事项继续保留，不静默改旧译。
凍傷/凍結及脱力/탈진等源字面差异按字段记录；是否属于相同枚举、开发残留或实际显示仍未验证，见KNOWN_ISSUES顶部。

## 可复现验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-103-verification/reviewed-workspace
python build/batch-103-verification/verify_resources.py baseline
python build/batch-103-verification/verify_resources.py modified
python build/batch-103-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT SHA256仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
回填双盘相同、旧11,120条与6,760个其余源值保持；隔离回滚恢复11,120，主MODIFIED_FILE保留11,416。
基线1374测试；本批新增六项覆盖/旧译/held/标记与语气/条件/源差异/候选锁回归。字面输出、命令与退出状态见本地VERIFICATION.txt。
清理只移除核实可再生成且无依赖的隔离验证pyc；原盘、配置、存档、runs、当前测试包与基线/回滚/研究证据保持。
不合盘、不生成ISO或整盘副本、不启动模拟器，不刷新字库/TOC/入口；邮件128/235、44字幕315cue保持，离线不是游戏验收。
提交推送核对后继续剩余场景动作物品、制作材料及配方等完整功能组；原值剩余含工具/样本，不当作确定玩家待译量。
