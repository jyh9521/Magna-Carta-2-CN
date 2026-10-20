# 第一百一十四批：阿尔戈通信对白（152条）

2026-10-20。从113批接续，新增152条INT draft，累计13,674；1104项candidate原样不改。

## 源与语境

MC2_communi_Argo.int实际为韩文；九组overheat24/focus14/bad_abnormal14/good_abnormal17/HP_30为17/communi_order24/cancel14/success14/failure14，152非空完整合批。另9空白不生成译文、不算进度。53种逐字相同源才复用，但所有152稳定ID/section/key/occurrence分别保留。
阿尔戈稳重、提醒同伴退下/等待援助，关怀洁菲；对塞蕾丝汀道歉保留人名。角色名复用洁菲/塞蕾丝汀既有candidate，不新增已验证关系。不同阶段/对象相同源不擅自扩写，不从com日文同key代换。
18处行尾ASCII空格保留，源无字面反斜线或功能换行，不新加。源…与...均有含义的对白，不当纯占位；省略/疑问语气依源转换为中文，不补机制、百分数或动作台词。
Verified仅指源/hash/离线回填，运行触发、配音或字幕用途未验证；全部新增draft。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-114-verification/lf-workspace
python build/batch-114-verification/verify_resources.py baseline
python build/batch-114-verification/verify_resources.py modified
python build/batch-114-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。新增152双盘回填一致，旧13522译文/4502其余原值/全部历史held逐值及hash保持；9空白亦原值。
基线1440测试，新增四项source-free合同；修改与索引导出干净源码1444测试均OK(skipped=1)。另有164文件逐字节复现、依赖锁/术语/字幕保持、独立回滚/错误哈希拒写及可执行脚本检查。
隔离回滚恢复13522旧译，主MODIFIED_FILE仍13674；build/batch-114-verification保留MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt、ROLLBACK.sh和精确命令/输入/字面输出/退出状态。
只清理绝对路径核实的隔离源码可再生成pyc；保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。不合盘，无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。
提交推送远端核对且工作区干净后继续朱特通信152非空完整组，候选/context已保存；4502原值含编辑器/样本，不当玩家待译量。

初次索引依赖锁检查发现本批JSON写出CRLF、Git按.gitattributes规范化LF，导致计划锁失配。已将新数据/测试显式写为LF并重新锁定，仅编码换行变化，译文字段不变；保留初次工作区/失败证据，另建lf-workspace及干净快照验证，不覆盖旧证据。
