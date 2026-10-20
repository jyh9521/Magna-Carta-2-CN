# 第一百零七批：朱特与洁菲装备（202条）

日期：2026-10-20。从已提交106批接续，206候选核读后新增202条INT draft，累计12,275；新增70项candidate共955，旧885保持。四字段不完整属性完整held。

## 完整功能组与源上下文

- 朱特单手剑42、双手剑32、肩甲32；洁菲扇33、法杖33、手镯30合批。名称69、装备说明133。旧木剑三字段、无名战士巨剑全述及幻影之刃三字段保持，不重复统计。
- 目前单手剑47/47、双手剑36/36、肩甲32/36，扇33/33、法杖33/33、手镯30/30有draft。148/151肩甲D/S末尾防御+缺数值，四字段保留原值/SHA256，不补数字、属性或只改半条；这两组不称全部字段完成。
- 109/111/112单手剑、129双手剑、207/208扇、228法杖说明的功能尾空行/单空格保持；可解释的名称、说明和类别各按源翻译，不填空白属性行。
- 150_pauldron实际名称브론즈 건틀렛候选青铜护手，简述副装备，保留S字段末尾制表符；不因pauldron/key/相邻数据改为肩甲。
- 129_sword字面暫魂剣依源候选暂魂剑，不猜改斬字；雪华/水仙/风暴使者等仅候选，未核官方中文。칼린츠按实际传说剑士名、固定系列候选卡林兹复用，引用固定commit和词表锚点，不认定跨作同人。
- 114卡林兹的剑/131白夜均保留完成南部军首个任务后才能装备的条件，简述中的逗号各依源。梅莉莎、凯托、卡尔塔、阿维斯族、守护者、连环术师与能力值复用，不静默重译旧候选。
- 保留195加号、137功能换行、1制表符、全部数字及逐行空白/空行；千年前传说等叙事限定依源。非剧情单句行无内部标点则不加句末句号。
- Verified仅指资源源值/格式/回填，不证明显示、装备条件触发、物品身份或游戏机制。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-107-verification/final-workspace
python build/batch-107-verification/verify_resources.py baseline
python build/batch-107-verification/verify_resources.py modified
python build/batch-107-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填一致，旧12073及5901个其余源值保持，所有历史held和本批held4独立核对。
基线1398测试，新增六项source-free合同覆盖分组/残缺属性held/布局/源差异/固定候选引用/锁与字幕。合批后完整验证包含164文件逐字节复现、索引导出干净源码测试、独立回滚和错误哈希拒写。
隔离回滚恢复12073条旧译，主MODIFIED_FILE仍12275；四实物及精确命令/输入/字面结果/退出状态见build/batch-107-verification/VERIFICATION.txt。
仅清理经绝对路径核实的干净源码可再生成pyc；原盘/配置/存档/runs/当前包/入口依赖/基线/回滚/研究保持。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
邮件128/235及44字幕315cue保持，离线成功非游戏验收。验证清理提交推送核对后继续阿尔戈/克罗塞尔装备194候选；其余物品394原值另存待审，不把含工具/样本的5901原值当玩家待译总量。
