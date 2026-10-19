# 第四十五批：利登家族支线与第七章邮件补齐

日期：2026-10-20。新增INT68条，累计6,070条draft；291项共享candidate及1项独立字幕candidate。
字幕28份194/315cue不变，所有译文/术语未人工定稿。

## 明确范围

- Quest/07_720_0四字段、07_crocel_0二、07_crocel_1六、07_crocel_2二十一，共33字段。
- E07_002-005、Q07_qube_1-3及关联Q_kenaros_1共8封16字段。
- CharacterName/Kenaros一、FieldName隐者洞窟/古代墓穴二、家族信件/武器/护具与五钥匙共16个Item字段。
- 分类24 dialogue、15 name、8 mail_subject、8 mail_body、8 item_description、4 quest_description、1 system_message。

Verified / source/offline：新增ID与前44批无重叠；Quest/07_全部150字段有draft，E07/Q07八封16字段均有draft，
加上关联封印石邮件，全部邮件由98增至114/235字段。CSMB07主线282、Compose40、城内NPC41与独立字幕7均保持。
这仍不是全游戏或所有可能显示资源完成；其他章节与硬编码/图片文字等覆盖缺口继续保留。

利登/家族空格变体、凯纳罗斯、隐者洞窟/封印石/古代墓穴、老狐沃尔凯诺/石灰丘陵、
五把钥匙、家族火球/祖母绿/KAN充能器共17项candidate。五钥匙采用暂定音译，未确认汉字或官方译名，不能误称定稿。
父亲反对为复仇送死的信、长者的判断和巨人的威胁分别保持角色立场；拜泽恩下落仍无新增结论。
家族空格变体保留独立源ID/hash，邮件定位清单的1至5顺序、5块封印石与源地点对应不变。

14字段保留67个功能换行与全部空段落索引；17条对白显式去源硬换行。
属性61/40/30、家主信与五钥匙的尾随空格、第三钥匙说明的前导空格保持。
两件装备的单句说明按既有逐行样式移除句末句号，功能换行/属性不动；校验器未削弱。
字幕profile/28计划及独立字幕候选逐字节保持，本批不重读完整ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/family-legacy-batch045/current-workspace
python build/batch-045-verification/verify_resources.py baseline
python build/batch-045-verification/verify_resources.py modified
python build/batch-045-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；current-workspace为样式修正后的最终输入锁，早期失败工作区保留为诊断证据。
双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新68条双盘回填一致，旧6,002条保留，12,106条仍为源值；独立回滚恢复6,002条，主修改产物保留6,070条。
全部历史held/未知格式/重复key occurrence/旧译保持；错误hash回滚拒绝且不变。
干净Git index源码测试、121项依赖锁、164文件重建一致性与四组CI分别核对。
完整原文、容器、差异和本机验证证据只留build/batch-045-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；原盘/配置/存档/runs/当前包及必要研究与回滚证据保留。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批核读第八章连续主线，并按同场景补独立字幕、场地提示及相关NPC/任务。
