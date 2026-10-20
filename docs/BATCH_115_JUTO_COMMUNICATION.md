# 第一百一十五批：朱特通信对白（152条）

2026-10-20，从114批接续。新增152条INT draft，累计13,826；1104项candidate原样保持。

## 完整组与上下文

MC2_communi_Juto.int实际韩文，九动作/状态组overheat24、focus14、bad_abnormal14、good_abnormal17、HP_30为17、communi_order24、cancel14、success14、failure14共152非空字段整组合批，另9空白保留源值且不计译文。
72种精确源值分别核读，同源复用但稳定ID/section/key/occurrence不合并。初期对洁菲的敬语与公主殿下称呼保留，后期直呼与熟悉口气区分；对同伴自信/逞强、成功打趣与失败歉意依源，不由动作key补治疗或数值。不拿com日文/JPN同key覆盖韩文。
12行尾ASCII空格保持，源无字面反斜线/功能换行，不新加。不同阶段相同源不擅自改台词；source的三点与单字符省略号属于有语言内容对白，不当纯占位。名称沿用洁菲等共享candidate，不新增术语或提升人工定稿。
Verified仅指源形态/hash/离线回填；运行触发与配音字幕用途未验证，所有新增draft。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-115-verification/reviewed-workspace
python build/batch-115-verification/verify_resources.py baseline
python build/batch-115-verification/verify_resources.py modified
python build/batch-115-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；新增152双盘回填一致，旧13674译文/4350其余源值/全部历史held逐值与hash保持，9空白亦保持。基线1444测试，新增四项source-free合同，修改与索引导出干净源码1448测试均OK(skipped=1)。
完整收尾另含164文件逐字节复现、输入依赖锁、候选/字幕保留、独立回滚/错误哈希拒写和可执行脚本。隔离回滚恢复13674旧译，主MODIFIED_FILE仍13826；build/batch-115-verification保存MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt、ROLLBACK.sh及精确命令/输入/字面输出/退出状态。
显式LF写出并锁定计划，避免CRLF与Git索引规范化造成hash差异。仅清理绝对路径核实的隔离源码可再生成pyc；保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。
提交推送远端核对且工作区干净后继续Crocell28/Zephi114/Zephie114共256非空通信完整组，228空白保留不计。候选/context/格式初审已保存，未见未知反斜线；Crocell日文有功能换行/ASCII~，双拼写韩文表分别保留，下一阶段仍逐条核读。4350原值含编辑器/样本，不是玩家待译量。
