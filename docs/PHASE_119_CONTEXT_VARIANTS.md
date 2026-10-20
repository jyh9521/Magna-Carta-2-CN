# 第119阶段：同源译文上下文审校

2026-10-20，接续118的两组一致性候选。没有新增翻译batch或改译：INT14,082 draft、1104 candidate、44字幕315cue保持，translation-workflow最后仍116。

## 上下文处置，不是机械统一

- CSMB02_25的15/46/64三次相同礼貌应答分别承接战斗菜单、连锁及AI设置讲解；知道了/明白了均可表达当前应答，保留自然变体。只核对邻接文字，不由译文变体推断不同说话人或声优，不以此冒充配音/游戏验收。
- MC2Quest/04_405_0同源字段name与GoalDesc分别是标题与目标，前者讨伐、后者击败；kill进度也为击败，科洛瑟斯名称一致，目标和标题文字不必机械相同。关联描述、接受/拒绝/进行/完成文本一并审读，QUEST%s保持原值。
- 两组处置为context-variant-retained，仅记录对当前draft的上下文判断，不升级reviewer、候选术语或人工定稿。没有修改任何翻译值，也不是全部游戏的全面审校结论。

## 可复用只读审计

新增tools.audit_translation_variants，从原始容器和既有hash计划构建内存验证，再按embedded_path/section/源hash分组，只标出译文hash不同的完整组。不会跨文档/section盲合并，不输出完整原文或译文。locales/zh-Hans/variant-review.json保存两组ID、source hash、全部translation hash和说明；源hash、成员/译文hash变化即拒绝陈旧处置，重复组拒绝，不以宽泛词面白名单忽略后续变化。
工具输出保留所有组和pending/context变体数，不修改游戏、计划或状态。唯一可接受的处置为context-variant-retained，human-final不是合法处置。

```powershell
python -m tools.audit_translation_variants --source build/disc1-selected/MC2Game/Localization/Coalesced.int --plan build/batch-116-verification/reviewed-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json --review-profile locales/zh-Hans/variant-review.json --output build/phase-119-verification/new-context-audit.json
python -m unittest discover -s tests -p test_translation_variant_audit.py -q
python -m unittest discover -s tests -q
```

输出必须新建，不能覆盖源/计划/处置文件。无profile时两组pending；带当前profile时零pending、两组上下文变体，不等于从目录消失。

## 验证与收尾

双盘INT源hash均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。基线1463测试，新增8项source-free合同；修改与索引导出干净源码1471测试均OK(skipped=1)。两盘报告相同，处置前后全部源/译文hash及组成员完全一致；原容器、18176值/14082旧译和全部历史held保持；164文件复现与116工作区逐字节相同。八源hash、24余项分类、workflow/terms/subtitle-profile保持。
独立报告副本回滚恢复2 pending的基线报告，主MODIFIED_FILE.json保留0 pending/2上下文变体；错误hash拒写，可执行ROLLBACK.sh及MODIFIED_FILE.json/DIFF_FILE.json/VERIFICATION.txt保存在build/phase-119-verification，记录精确命令/输入/字面输出/退出状态。生产译文不执行回滚。
仅清理绝对路径核实的隔离干净源码可再生成pyc；保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。
下一阶段按现有测试包manifest/依赖hash只读核对累计字形需求与已有remap覆盖，先复用覆盖审计；未经对应验证流程不刷新资源。边界异常与孤立笑声缺乏运行证据，保持未知，不重复补零/翻端序或凑翻译数量。验证清理提交推送并核对远端后自动接续。
