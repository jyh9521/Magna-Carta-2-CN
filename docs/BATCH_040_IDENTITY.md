# 第四十批：第七章身份争执、运输队与独立字幕

日期：2026-10-19。新增INT100条，累计5,597条draft；258项共享candidate及1项独立字幕candidate。
新增csm07-10七cue，字幕28份194/315cue。所有译文/术语仍未人工定稿。

## 范围与上下文

- CSMB07_20身份争执68、CSMB07_23救援路线与运输队18，共86条；第七章主线前缀共282，本批86/282有draft。
- Compose/Chapter07仅01-05与32/33共7/40字段；其余救援、技能与场地提示待后续。
- CharacterName/AvisTransporter、Item/Avisticket及说明3字段，UI_Pillar退出/移动2字段，E07_001邮件2字段。
- 分类85 dialogue、8 narrative、2 name、2 menu、1 item_description、1 mail_subject、1 mail_body。

Verified / source/offline：新增ID与前39批无重叠。艾尔加身份、自述/同伴指认与质疑保持各自立场；
相同面孔的另一人是谁不补写答案。自我崩溃与失忆仅按虚构剧情原句，不作现实诊断。
62/63/67为第一人称念白；64-66为过去安慰的回忆对白，不擅加洁菲当前在场。
血之契约、救援愿望、失控时处置的条件不改成已发生结局；不抹去矛盾或替角色定罪。
阿维斯运输队/乘车券/商店新增3项candidate。终身使用、物品免费说明、危险/交战区不通行、
晶柱旁找阿维斯族人和独立商店条件分别保留，不扩写成任何地方都可到达。
邮件源压缩空格的名称变体复用乘车券目标，但ID/hash不归并；邮件由96增至98/235字段。
70条普通对白/念白去硬换行有显式策略，邮件7个功能换行与空段落索引保持。

## 独立字幕

csm07-10仅Disc2含该资源；重新校验两原盘完整hash与44字幕成员后导出44catalog/315cue，
从187增至194有draft。保留原cue时间、KRCC、BOM和唯一br标签；不把字幕与Coalesced按词面合并。
同伴的叛徒指认及回忆恢复后的罪责自述按原cue独立翻译，不加入额外身份结论。
逐成员回填、空计划原样重建、独立副本回滚、原成员hash复查；旧187cue保持，121cue仍未译。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/identity-batch040/workspace
python build/batch-040-verification/verify_resources.py baseline
python build/batch-040-verification/verify_resources.py modified
python build/batch-040-verification/verify_resources.py rollback
python build/batch-040-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

工作区与字幕导出目录须全新。双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新100条双盘回填一致，旧5,497条保留，12,579条仍为源值；独立回滚恢复5,497条，主修改产物保留5,597条。
第六章Quest仍314/316、仅两未知反斜线保持；所有历史held值/重复key occurrence与旧译保持。
错误hash回滚拒绝且不变；干净Git index源码测试、111项依赖锁、164文件重建一致性与四组CI分别核对。
完整原文、容器、字幕原文与所有本机验证证据仅留build/batch-040-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；原盘/配置/存档/runs/当前包及必要研究与回滚证据保留。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批从CSMB07_25接续南部军拦阻、相关场地提示及同阶段NPC/任务，不重复本批身份争执与运输队教学。
