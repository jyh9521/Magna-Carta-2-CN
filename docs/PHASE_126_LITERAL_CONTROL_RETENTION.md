# 第126阶段：字面控制符的源锁定保留审计

2026-10-20，先核对HEAD fec2a51、远端相同、干净状态及每轮收尾约定。最后翻译批次116、14,082 INT draft、1104 candidate、44字幕计划/315cue不变。本阶段不新增猜测译文，不回填新游戏资源。

## 目的与范围

125已把七别名字库/局部路由验证到非控制映射与ink通过，但累计INT仍包含4条末尾实际TAB。它们不是转义文本\t：Movie/10_35、armor_pauldron_juto/150_pauldron_S、common/Communi_failure_short_01与common/Advantage_kan_01；两盘同源，保留各盘身份。源和草稿均各有一个尾TAB，不能简单删除、换空格或以字体记录存在当成语义已核。

新增audit_text_font_coverage.literal_control_shape和audit_control_retention，及只读CLI tools.audit_literal_control_retention。使用与既有coverage一致的保守Unicode category-C分类，仅在精确TOKEN匹配以外计数字面量；不声称所有category-C都是已理解的引擎控制语法。

## 合同

locales/zh-Hans/literal-control-retention.json锁定完整source SHA、resource、完整14,082项计划canonical SHA，并逐项锁定stable ID、source/translation SHA、控制符有序列表和非控制segment非空形状。四项序列都是[9]、shape都是[true,false]，说明尾部TAB，而不是只对比集合或总数。增加/删除/重复/重排控制符、从尾部移到头部/中间、源/译文/计划漂移、缺项/多项/重复ID均拒绝；行内非控制片段的确切文字offset不宣称等同。

ledger限制1..16384项，每序列1..4096个Unicode scalar category-C整数，拒绝bool、非C、surrogate和越界；shape长度为sequence+1且值严格bool。调用现有resolve_changes与rebuild继续源身份、编码、占位符/控制码、数值相关既有规则和重提取检查。ledger不自动随译文更新，不是可配置的忽略列表；任何变化需重新核读上下文并更新hash。

CLI要求新报告路径、输入尺寸上限、严格JSON、写前/写后输入原值复查与报告重开；没有游戏写入。报告exact_control_sequences_and_segment_shapes_retained=true只表示保留证据，font_coverage_verified、unknown_control_syntax_resolved、game_rendering_verified均false。retention exit0不是字体coverage绿色或投放授权。

## 真实验证

两盘源hash独立核对，累计计划14,082项解析/回填验证，两个报告均4项、[9]且相同，所有源/译文hash和尾部shape保持。独立调用原tools.audit_text_font_coverage审计全部14,082 INT、2446码点与125候选七字体：仍exit1，七个字体各自唯一failure是U+0009/control-or-format-literal-unverified，all_supplied_fonts_cover_literals=false。没有改原font_coverage/audit分支，也不以本阶段报告覆盖原结果。

125完整路由输出及十资源controls/candidate/raw-controls/rollback-check/报告manifest成员hash保持；十个rollback-check继续逐字节等于controls。未重建或刷新旧262测试入口。字幕44计划仍超既有额外16上限，本阶段未改上限或路由允许条件。

## 复现

先从源和已提交workflow复现合并工作区（输出须新建），再分别审计两盘；plan canonical与既有116工作区一致：

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/control-audit-workspace
python -m tools.audit_literal_control_retention --coalesced build/disc1-selected/MC2Game/Localization/Coalesced.int --plan build/control-audit-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json --ledger locales/zh-Hans/literal-control-retention.json --output build/control-audit-disc1.json
python -m unittest discover -s tests -p test_literal_control_retention.py -q
python -m unittest discover -s tests -q
```

第二盘替换coalesced路径和新output路径即可，不合并盘。报告不包含原文全集，原资源仍只在忽略目录。模块API audit_control_retention(original_bytes, changes_dict, ledger_dict)返回相同分类，不依赖当前本机测试包。

## 验证、回滚与接续

基线1525；新增12项后修改/索引导出干净源码1537均OK(skipped=1)。覆盖精确尾TAB、多控制/空segment、增加/删除/移动/重复/重排、已知TOKEN排除、top/entry/source/translation/plan hash漂移、scalar/shape类型、重复/额外/空/过大ledger、未知行字段拒绝和CLI新输出要求，且断言原coverage仍false。

同一源锁定TAB合成样本，旧模块无专用retention能力、exit2；新模块证明源hash/序列/尾部形状保留，同时coverage仍unverified、exit0。隔离模块副本hash保护回滚恢复旧模块、exit0，再跑恢复旧无专用审计exit2；主MODIFIED_FILE.py保留新helper。四件证据、精确命令/输入/字面输出/退出状态见build/phase-126-verification/VERIFICATION.txt，错hash回滚拒写。

源双盘18176值/旧译、八源hash、24剩余分类、164文件复现、64当前入口依赖/配置/XEX、candidate/raw只读核对以及125局部路由hash保持；workflow/terms/subtitle-profile不变。只清理核实绝对路径的隔离源码可再生成pyc，保留原盘/配置/存档/runs/当前包及必要字体候选/控制/回滚/研究。无ISO/整盘副本/模拟器启动及字库/TOC刷新。

验证清理提交推送并核对远端和工作区干净后，继续设计有界44字幕合成和显式源控制保留的离线资源合同；保留普通coverage原分类，不将源保留证据当作未知运行语义已解决。
