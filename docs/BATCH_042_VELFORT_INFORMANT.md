# 第四十二批：贝尔福特入城、平民与情报员追踪

日期：2026-10-19。新增INT130条，累计5,821条draft；262项共享candidate及1项独立字幕candidate。
字幕28份194/315cue、邮件98/235字段不变，均未人工定稿。

## 场景与关联范围

- CSMB07_40休息与回想44、07_45研究所线索15、07_48灾祸种与战斗建议6，共65条。
- Quest/07_701_0泽罗哈追踪20字段，Compose/Chapter07_26-30五条救援提示。
- NpcTalk/07_velfort前37条；698_0、720_0/e0/e1四条后续泽罗哈/漩涡炸弹关联暂待下一阶段。
- CharacterName/zeroha/cooks、FieldName/SentinelLab/SentinelLab三个关联字段。
- 分类114 dialogue、10 narrative、4 name、1 system_message、1 quest_description。

Verified / source/offline：所有新增ID与前41批无重叠；CSMB07主线218/282、Compose38/40、城内NPC37/41。
泽罗哈、库克斯、哨兵研究所新增3项candidate；既有灾祸种、连环术、库布等复用旧候选。
灾祸种导致当前地区无法施术、朱特/阿尔戈代替克罗塞尔/塞蕾丝汀前排的建议保留原作用范围，
不推断整个游戏禁止施术。朱特对洁菲所在研究所的确信仍为角色判断，非新增全知结论。
泽罗哈已被抓或仍被追捕两种可能都保持；39-43第一人称念白与同伴对话区分。

平民的饥寒、父母失踪和另一人明确的父母遇害分别保留，不把失踪偷换成死亡。
投机NPC的3倍/4倍回报与驻军对峙2个月保持字面，均是游戏角色发言，不当实际建议。
1条DES与1条发现库布的系统提示分别保留功能结构，合计1个换行；系统单句按既有样式规则无句末句号。
80条普通对白/括号念白通过显式策略去源硬换行；其余未知、占位与重复key occurrence保持。
第七章唯一独立字幕此前已全7cue，本批profile/28计划/独立字幕候选逐字节保持，不重读ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/velfort-informant-batch042/current-workspace
python build/batch-042-verification/verify_resources.py baseline
python build/batch-042-verification/verify_resources.py modified
python build/batch-042-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；样式拒绝后修正单句系统句号，current-workspace为最终输入锁，不削弱校验。
双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新130条双盘回填一致，旧5,691条保留，12,355条仍为源值；独立回滚恢复5,691条，主修改产物保留5,821条。
全部历史held/旧译保持；错误hash回滚拒绝且不变。干净Git index源码测试、115项依赖锁、164文件重建一致性与四组CI分别核查。
完整原文、容器、差异和本机验证证据只留build/batch-042-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究与回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批接续CSMB07_50/60/70、泽罗哈相关四条NPC及后续潜入准备，再补技能与同阶段支线。
