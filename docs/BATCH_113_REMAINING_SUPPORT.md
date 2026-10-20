# 第一百一十三批：四角色支援对白（287条）

2026-10-20。从112批接续289候选，朱特71、克罗塞尔68、塞蕾丝汀88、洁菲60共287新增INT draft，累计13,522；1104项candidate，旧1096项完整保持。

## 语境与格式复核

四个完整角色动作/状态组一起收尾。初期朱特对公主敬语与后期熟悉口气分开；克罗塞尔保留逞强，塞蕾丝汀保留俏皮呼唤，洁菲保留关怀；不由技能key补数值/机制/关系。
复用共享候选，日文角色别名ルウ/ジュト/クロセル/アルゴ、大地のタミ/水のタミ、マレ、対センティネル部隊新增八项均candidate/unverified，不证明跨表身份或官方译名。
两条held：Zephi/Celestin/Abnormal_bad_ch3_01含未知\じっと；Zephi/Rue/Abnormal_bad_ch3_01以私がすぐに未完，整值保留源及hash，不补n或补治疗。
Celestin/Argo/Overheat_ch3_01的occurrence1/2是不同源对白，ID独立，不能三元key覆盖。Juto/Crocell与Celestin/Rue、common的不同状态同源对白仍独立保存，不按状态key改含义。
485字面\n、63全角～、1全角１、2tab、4个U+3000及Celestin/Argo/Focus_ch3_01第一行内部ASCII空格保持。初审两处候选误添～已纠正；长音ー/ぉ不当波浪线。格式记录及最初基线工作区保留。
所有新增draft，不作人工定稿；Verified仅指源形态/哈希/离线回填，不证明配音字幕触发或游戏验收。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-113-verification/reviewed-workspace
python build/batch-113-verification/verify_resources.py baseline
python build/batch-113-verification/verify_resources.py modified
python build/batch-113-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；新增287双盘回填相同，旧13235译文及4654其余源值保持。历史held与新held2逐值/hash核对。
基线1434测试，新增六项source-free合同，修改及索引导出干净源码1440测试，均OK(skipped=1)。验证另含164文件逐字节复现、所有计划锁、旧术语前缀、独立回滚、错哈希拒写及可执行ROLLBACK.sh。
独立回滚恢复13235条旧译；主MODIFIED_FILE仍13522。四实物MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt、ROLLBACK.sh及精确命令/输入/字面输出/退出状态留在build/batch-113-verification。
清理仅绝对路径核实的隔离源码可再生成pyc，保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。没有新ISO/整盘副本/模拟器/字库/TOC/入口刷新。Compose836/921、Item1608/1630、邮件233/235及44字幕315cue保持。
提交推送核对后自动接续communi_Argo完整152非空字段（9空白不计），实际韩文源独立核读，不拿com日文按key代换；候选/context已保存。4654原值含编辑器/样本，不是玩家待译量。
