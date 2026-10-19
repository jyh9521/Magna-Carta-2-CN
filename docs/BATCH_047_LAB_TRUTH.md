# 第四十七批：艾尔加身世与研究所平民营救

日期：2026-10-20。新增INT88条，累计6,251条draft；308项共享candidate，另保留1项历史字幕来源记录。
字幕28份194/315cue、邮件114/235字段保持，均未人工定稿。

## 范围与上下文

- CSMB08_20艾尔加身世61条；Quest/08_801_0平民营救20字段。
- Compose/Chapter08_11-15休息对白与X/Y菜单5字段；Item/Valuables通行卡第二occurrence名称/说明两字段。
- 分类79 dialogue、3 narrative、2 name、1 quest_description、1 quest_progress、1 menu、1 item_description。

Verified / source/offline：新增ID与前46批无重叠；CSMB08主线116/239有draft，Compose前15字段及当前营救任务均有draft。
人形哨兵、二号、一号艾尔加、二号艾尔加、绝对命令、研究室通行卡新增6项candidate；
玛格纳卡尔塔、一号、血之契约、主人等复用既有候选。身世与幻想术式仅译角色对白，不补现实制备参数或后续剧情结论。
画像与绝对命令的“不能杀死/不能放任死亡”两个条件都保持；一次命令、卡蒙德与回忆叙述不混成全知旁白。
58-60为朱特的第一人称念白，与研究员对白区分。

## 同key不同用途的Item

Valuables/key_laboratory与key_laboratory_D在同一section内各出现两次。
第一组是研究所钥匙，第二组才是研究室通行卡；本批仅回填第二组两个稳定ID，第一组原值保持。
匹配必须包含完整资源/section/key/occurrence/source_sha256，不按key去重、不按第一个匹配盲选。
主脚本与独立回填验证分别断言第二组改动、第一组不变，所有重复occurrence结构保持。

X/Y、Styles标签、菜单换行及DES换行/尾随空格保持；42条普通对白有显式去硬换行策略。
第八章独立字幕只含csm08-30/40，本批尚未到场景，不重复导出ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/lab-truth-batch047/workspace
python build/batch-047-verification/verify_resources.py baseline
python build/batch-047-verification/verify_resources.py modified
python build/batch-047-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新88条双盘回填一致，旧6,163条保留，11,925条仍为源值；独立回滚恢复6,163条，主修改产物保留6,251条。
旧译/历史held/未知格式/重复key occurrence保持；错误hash回滚拒绝且不变。
干净Git index源码测试、125项依赖锁、164文件重建一致性与四组CI分别核对；完整原文/资源/证据只留build/batch-047-verification。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究与回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批接续CSMB08_25/27/28及同阶段营救，再补csm08-30字幕，不重复本批身世说明。
