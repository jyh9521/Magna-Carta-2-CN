# 第一百一十一批：后续场景与关联物品（236条）

日期：2026-10-20。从110批接续271候选，新增236条INT draft，累计13,077；新增11项candidate共1084，旧1073保持。35纯省略号完整原值/hash held。

## 连续场景与关联资源

- 第四章至结局余下队员交谈151（朱特25/阿尔戈27/洁菲24/克罗塞尔27/露21/塞蕾丝汀27），第十章路线内心53，第十二章仪式6，Valuables剩余26合批；旧第七至九章等已有译文不重复翻译。
- 显式分类：对白154、叙述53、物品说明15、物品名11、系统消息3。角色声口、疑问/猜测、家属与同伴称呼依源，梅莉莎身份疑问不写成确认事实。
- 五角色Ch12/Ch13源值逐字相同才复用，两个稳定ID保留；塞蕾丝汀两句分别是希望和平/等和平后，各自译，不按尾声key复制。
- 第十章南部军营地、北部军入侵、村民敌视、黑刃要塞/鲁哈尔特高原及救朱特路线限制按各字段源，不因剧情印象修正阵营或替换高原路线。露东北方位、KAN地雷与火之KAN操作描述保持，不视为已验证机制。
- King_token_water源홍련의 수정候选红莲水晶，说明打破水祭坛结界；JPN名为紅煉の水晶，仅有限词面参考，不认定INT韩文已核汉字。King_token_fire的파계有限核读JPN破戒の巻物后候选破戒卷轴，不因破结界功能改破界；元素/英文key不替代实际名称。
- Alecs_mail按实际名南部军总司令信函，不补英文key暗示的人名；hidden_key按源控制室通行卡，不改隐藏钥匙。库布、杜南/鲁哈尔特、法伊尔瓦因、风歌洞窟、拉·斯特拉达/修恩扎伊特等复用共享候选。
- 144功能换行、53对半角括号、23个波浪线及逐行边界空白保持；初次批内行数检查在写计划前发现朱特Ch04_17_17两行候选被压为一行，恢复源功能换行，原基线工作区/复核记录保留。仪式末句不擅加源未写的最后一战。
- Compose现836/921、Item1608/1630、Valuables154/154有draft。Compose余85全是既有held：83纯标点与第63批성쇄/第68批[왕의 영병]两条待核语义；Item余22同样全既有held，不补数值/空白或猜未知配方转义。未称全游戏或所有场景文本完成。
- Verified仅指源值/格式/回填；官方命名、实际显示、配音/字幕触发与游戏机制未验收。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-111-verification/reviewed-workspace
python build/batch-111-verification/verify_resources.py baseline
python build/batch-111-verification/verify_resources.py modified
python build/batch-111-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填相同，旧12841和5099个其余源值保持，所有历史held/新held35核对原值/hash。
基线1422测试，新增六项source-free合同覆盖范围/标记held/功能布局及阵营与物品源差异/尾声独立状态/候选/锁及字幕。完整验证含164工作区文件逐字节复现、索引导出干净源码测试、独立回滚与错误哈希拒写。
隔离回滚恢复12841条旧译，主MODIFIED_FILE仍13077；四实物及精确命令/输入/字面结果/退出状态见build/batch-111-verification/VERIFICATION.txt。
仅清理核实绝对路径的隔离干净源码可再生成pyc；原盘/配置/存档/runs/当前包/依赖/基线/回滚/研究保持。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235、44字幕315cue保持；离线成功非游戏验收。验证清理提交推送核对后接续剩余邮件107字段与Argo支援交谈53合批160候选（含Test더미占位1，不计译文）；标题/正文与支援动作完整组核读，不混淆com/communi表，5099个含编辑器/样本的原值不当玩家待译总量。
