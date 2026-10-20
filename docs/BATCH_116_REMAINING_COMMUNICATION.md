# 第一百一十六批：剩余通信对白（256条）

2026-10-20，从115批接续。新增256条INT draft，累计14,082；1104项candidate原样保持。

## 完整组与来源

MC2_communi_Crocell.int日文28非空，Zephi与Zephie两份韩文各114非空完整合批；本批228空白原值不生成译文。五份communi累计560/560非空字段有draft，另246空白原值，不把空白算翻译。
两份拼写表按section/key/occurrence逐项比较，114/114实际source/hash相同、ID不同，各自保留盘别与embedded_path回填。只按精确源复用，不凭名字删表或宣称运行冗余；这不是拿com或JPN同key替换。
80种精确源变体分别核读；克罗塞尔保留逞强、怕露责备与对公主的口吻，洁菲保留关怀/合作、对各队友称呼及自身坚持。反哨兵部队/朱特/洁菲/阿尔戈/塞蕾丝汀/克罗塞尔/露复用共享candidate，不新增官方身份断言；不由动作key补伤害/治疗数值。
55个字面\n、6半角~、2全角～、16尾ASCII空格保持；不把波浪线全角化。韩文省略号与三点有语义对白照译，不作纯占位；功能断行不重排。
Verified仅指源/hash/离线回填；运行触发/配音/字幕用途未验证，所有新增draft。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-116-verification/reviewed-workspace
python build/batch-116-verification/verify_resources.py baseline
python build/batch-116-verification/verify_resources.py modified
python build/batch-116-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；新增256双盘回填一致，旧13826译文/4094其余源值/全部历史held逐值/hash保持。基线1448测试，新增五项source-free合同；修改与索引导出干净源码1453测试均OK(skipped=1)。
完整收尾另含164文件逐字节复现、输入依赖锁、旧候选/字幕保持、独立回滚/错误哈希拒写和可执行脚本。隔离回滚恢复13826旧译，主MODIFIED_FILE仍14082；build/batch-116-verification保存MODIFIED_FILE.int、DIFF_FILE.json、VERIFICATION.txt、ROLLBACK.sh及精确命令/输入/字面输出/退出状态。
显式LF写出并锁定计划。仅清理绝对路径核实的隔离源码可再生成pyc；保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。

## 下一阶段审计而非凑数

next-game-resource-audit.json已从实际工作区统计：4094其余原值含引擎/编辑器/测试/空白/历史held，不是玩家待译总量。游戏非空未归类24项：CSM样本/孤立笑声3、MC2Game异常混编3、NPC/Quest默认样本2、UI数字标点/SID15、Shop SID1；其他游戏非空余项已有held记录。下一阶段逐项分类及异常编码研究，保留原值，不翻译编辑器/占位以凑批量。通信非空有draft不等于全游戏翻译、人工定稿或游戏验收完成；提交推送核对后自动继续研究/审校。
