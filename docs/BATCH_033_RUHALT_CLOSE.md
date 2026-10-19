# 第三十三批：第六章主线与独立字幕收尾

日期：2026-10-19。新增INT102条，累计4,943条draft；共享220项candidate，另1项独立字幕candidate。
全部均未人工定稿。独立字幕新增26cue，累计187/315cue，profile27份计划。

## 范围与明确覆盖

- CSMB06_100/110/121：23/4/15，共42条；现CSMB06全部201条有draft。
- NpcTalk/06_Abajet源序第51至80条：27条draft，2268/2273_0/2216三条删除标记保留。
- Compose/Chapter06_01–32：32条；FieldName/Ruhalt_plateau名称1条。
- csm06-80/90/120/122：2/8/13/3，共26cue；第六章五份33cue均draft。
- 分类92 dialogue、8 narrative、1 menu、1 name。

Verified / source/offline：与前32批无重叠。城镇前80条累计73draft/7删除标记，后续从偏移80继续。
215_0与215_1各有两条不同occurrence，均保留独立ID与台词，不按key去重。
X/Y菜单保留样式和1个功能换行；58条普通对白/叙述去硬换行有显式line_break_policy。
6条Compose括号念白与100末两条回忆叙述分别归类；源尾随空白逐条保持。

角色身份指认、朱特否认、同伴质问与命令分别保留发言立场，不给未完成台词补身份结论。
雷卡斯复用既有独立候选，不合并成贝卡斯。鲁哈尔特高原与特雷瓦沙漠新增共享候选。
一号（퍼스트）是代号的candidate意译，真实锚点仅来自csm06-120字幕。
当前Coalesced术语导入器不接受Movies资源，因此该候选存于review.subtitle_term_candidates，保留真实resource、
subtitle ID和cue源hash，不伪造Coalesced姓名；未改通用工具或放宽验证。详见PITFALLS。

新字幕完整保留timings/KRCC/BOM和br，旧161cue逐字段保持。实际来源按profile选Disc2，不强行在Disc1找缺失成员。
本阶段主线与字幕覆盖不表示全章所有文字完成：Compose仍余35条、城镇/其他地区NPC和任务/邮件仍有缺口。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/ruhault-close-batch033/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-033-verification/subtitle-catalogs
python build/batch-033-verification/verify_resources.py baseline
python build/batch-033-verification/verify_resources.py modified
python build/batch-033-verification/verify_resources.py rollback
python build/batch-033-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT原hash保持，102条新值回填一致；旧4,841条保留，13,233条仍为源值。
独立回滚恢复4,841条基线，主MODIFIED_FILE.int保留4,943条；错误hash输入拒绝且不变。
字幕导出重新核验双盘ISO完整hash及44份文本成员，不输出整盘副本；字幕独立回滚恢复，修改副本保留。
干净Git index源码测试、96项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文/资源与本机验证脚本只在build/batch-033-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批先补Compose剩余35条和同阶段地区NPC/任务，城镇从源序偏移80接续，再按场景推进第七章。
