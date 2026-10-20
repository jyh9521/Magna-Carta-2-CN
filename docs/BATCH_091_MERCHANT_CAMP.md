# 第九十一批：寻弟与阿维斯商人任务链

日期：2026-10-20。新增INT89条，累计9,281条draft；共享candidate437项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- 03_310_0寻弟18、03_350_00/01/02/03商人链63、人物名2、Item6同步；64 dialogue、10 name、5 quest_description、4 system_message、3 quest_objective、3 item_description。
- 46条普通对白显式去硬换行，25个功能字段保留布局；六个%s、QUEST、[]、10%/4个、前后空白保持。被抢商品名与营地箱钥匙名各源尾1空格保留。
- 寻弟与找回货物/采集/放置/代送四段完整核读，section与分支ID不合并，不以本批顺序证明运行触发。弟弟的누나明确称姐姐，译名不靠英文key判性别；找到弟弟/他答应自己回去不扩写为已护送回村。
- 琼斯蒂전스티、阿维斯商人아비스 상인、气体陷阱가스트랩、被抢走的商品빼앗긴 상품、营地箱子的钥匙야영지의 상자의 열쇠新增5项candidate，旧432项保持。猫猫/马雷族/柯塔马雷/水色湿地/内斯汀/奇怪蘑菇/毒蘑菇沿用旧候选。
- 商人10%酬劳与对捡到东西的自问按源保留，不补支付公式或保证付款。Item气体陷阱明确为强烈恶臭，NPC气体折腾人不扩成致命毒气或额外伤害数值。
- 奇怪蘑菇名/描述两字段旧译不变，不因本支线4个改掉旧11_303_0的4/5源差异。350_key按独立Item名/描述回填，运行箱钥匙绑定未验；不因阿维斯商人词组相同就扩入strange_Drag药物，留待对应支线。
- 东边/南边营地、紫色蘑菇、南边柯塔马雷的yes/in发言分别保留，不因相同文本合并ID。商人车坏与收货人听说意外分别表达，不补受伤或死亡。
- NPC1443/1473及余30占位/未知标记、邮件128/235、44字幕315/315已提取cue、README和全部旧译/held/重复occurrence保持；不表示全文或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/merchant-camp-batch091/workspace
python build/batch-091-verification/verify_resources.py baseline
python build/batch-091-verification/verify_resources.py modified
python build/batch-091-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
89条新译双盘回填一致，旧9,192条保留，8,895条其余原值未改；独立回滚恢复9,192条，主文件保留9,281条。
基线1302、修改/干净index1308测试各skip1；229依赖锁、164工作区文件重建一致、703份index文件复核及错误hash回滚拒绝分别验证。
GLOSSARY由437项结构化源渲染核对，旧432项不变；README、字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和工作区干净状态，当前CI按实际结果记录。
