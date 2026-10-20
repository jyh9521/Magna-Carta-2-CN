# 第一百零二批：能力、状态与复合属性卡蒙德（204条）

日期：2026-10-20。新增204条INT draft，累计11,120；新增37项candidate至612项，旧575项保持。

## 完整组与源核读

- Karmond八种属性LV1–5共40种/120字段；13种状态防护39字段；15种复合属性45字段。每种卡蒙德的名称、简述、全述按三个独立ID一起处理，不用等级数字样本凑数。
- 本地Karmond完整309字段：本批前有1705英雄卡蒙德3条旧译，306条未译；不是只含韩文的293条。INT内13条日文以及其他日韩混合特殊效果属于后续102字段，未在本批机械替换。
- 体力的2/4/6/8/10保留百分号，其余七种属性为固定值，不补百分号。复合属性按各字段数值与排列保留；简述双行、全述单行并列不强行改成同一布局。
- 源数据140个加号、18个百分号、83处功能换行、LV字面/等级数、逐行空白全部保留。名称重复不合并ID。
- 沉默防护仍包含眩晕免疫；烧伤/触电/冻伤分别包含炎热/麻痹/寒冷免疫。炎热/寒冷不是火/冰伤害，冻伤不按近义改成旧동빙冰冻。
- 风之卡蒙德源效果为体力/速度，不补风属性；复合名连环/再生/金刚等不当作机制或效果说明。英雄卡蒙德1705旧三字段不重译、不重复计数。

## 状态中文候选待统一QA

Verified / source：1640为어지러움，1697为스턴，均各有独立三字段；此处源字面、ID与免疫说明不同，不能按同译去重。
本批어지러움复用旧共享候选“眩晕”；스턴亦暂译“眩晕”，同译不代表枚举或实际效果相同。
第100批部分说明使用“晕眩/眩晕”分写；此为保留的后续统一校对项，未静默改写旧575项术语或旧译。
详见KNOWN_ISSUES.md顶部；资源/枚举/实机身份关系仍未验证，候选不得标为人工定稿。

## 重建、验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-102-verification/reviewed-workspace
python build/batch-102-verification/verify_resources.py baseline
python build/batch-102-verification/verify_resources.py modified
python build/batch-102-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
回填双盘相同，旧10,916条及7,056个其余源值保持；隔离回滚恢复10,916，主MODIFIED_FILE保留11,120。
基线1368测试；本批新增六项三联/等级数值/标记/状态范围/旧译/术语/字幕锁回归。完整命令、字面输出和退出状态保存在本地VERIFICATION.txt。

每阶段统一验证、差异/依赖检查、清理可再生成且无依赖输出、提交推送核对后继续；保留原盘/配置/存档/runs/当前测试包/基线/回滚/研究。
不合盘、不生成ISO或整盘副本、不启动模拟器；字库/TOC/入口未刷新。邮件128/235、44字幕315cue保持，离线非游戏验收。
下一阶段审读1716之后的102条混合语言特殊卡蒙德，按完整功能组与关联物品合批。
