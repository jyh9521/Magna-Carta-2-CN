# 第六十三批：机关零散字段与第十一章支线审计

日期：2026-10-20。新增INT84条，累计7,696条draft；351项共享candidate及1项历史字幕来源记录。
字幕37计划270/315cue、邮件116/235保持；3处新待查原值保留，均不计draft。

## 范围与来源判断

- Compose机关24/25/26/28/29五条与独立场地对白32-36五条；27的성쇄语义未确认，锁定原ID/hash为held，不据JPN同key的措辞替换韩文。
- Quest11_303_0爱情魔药18、11_307_0洞窟香料17、11_302_0终极药16/18、11_zuto_0高原挑战14，共65字段。此为同章节候选支线收尾，不证明所有存档均可同时接取。
- 关联Item9字段：神奇/奇怪蘑菇、软体动物体液、洞窟香料名称/说明及已有爱情魔药名称对应的说明。旧名称译文保持，本批不回写旧批。
- 分类53 dialogue、9 name、8 quest_progress、5 narrative、5 item_description、4 quest_description；35条普通对白显式去硬换行。九条机关/任务说明保留换行0/1/1/1/1/2/2/2/1，两个空段落位置保持；数值、Quest/QUEST/%s/方括号及新字段尾随空格保持。

Verified / source：爱情魔药yes/in/DES分别要求4/3/5，且奇怪蘑菇与毒蘑菇名称不一致。逐字段忠实保留，不替游戏统一任务条件；实际运行条件仍未验证。
Item key Mashpoison的韩文源为“奇怪蘑菇”对应源词，不能凭英语key擅自译毒蘑菇。神奇/奇怪/毒三个源名分别入candidate。
11_302_0的302_6/7是未完片段，显示/拼接未验证，原值及尾随空格保留，不补成完整句；held IDs/hash/reason见review。
체액/채액、코타메레各自原拼写保持，仅按同任务上下文给候选译法，不修正源字段或认定官方写法；비약复用既有묘약的爱情魔药候选，单列alias。
32-36不添加说话者、鬼魂或复活设定，触发仍未确认；原ID/hash回填只处理现存语言，不改触发逻辑。跨locale的不同分句/计数仍见docs/PITFALLS.md。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/sidequests-batch063/workspace
python build/batch-063-verification/verify_resources.py baseline
python build/batch-063-verification/verify_resources.py modified
python build/batch-063-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
84条两盘回填一致，旧7,612条保留，10,480条仍为源值；隔离回滚恢复7,612条，主产物保留7,696条。
干净index源码测试、166项依赖锁、164工作区文件重建一致性、旧341项术语保留/新10项追加及错误hash回滚拒绝分开验证。
历史held与新增3处待查、重复occurrence保持；字幕profile、37计划270cue、历史字幕来源与README逐字节冻结，本批不读取或导出ISO。
第62批CI run39299602981四组均completed/success，实际jobs保留；当前提交排队/运行中不记为成功。
仅清理核实绝对路径下可再生验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB12_005/007的出发与传送事件接续，按场景补对应Compose/NPC/关联名称；本批待查字段保留，不阻止其他已明确内容推进。
