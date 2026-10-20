# 第九十七批：Live3动物往事及关联短剧菜单（186条）

日期：2026-10-20。新增186条，累计10,182条draft；新增2项候选至455，另1项历史字幕来源记录保持，未人工定稿。第95批201与第96批186收尾后直接继续，三批共573条（562对白与11关联UI）。

## 范围与语境

- CSMB_Live3_001..006完整22/35/22/48/10/38条，共175对白；MC2UI_Field/Live Drama完整11项，包含三个短剧标题/角色/摘要、选择和退出提示，同步补齐前两批关联界面。
- 175 dialogue、6 name、3 narrative、2 menu_option；99条普通对白显式去硬换行，11功能字段保留原布局。三个摘要各7个literal换行，空段位置不改，第三摘要开头1空格和三个人名列表ASCII逗号加空格保持。第3方保留原제3자的数字3。
- 쳉暂音译铖，仅为动物称呼candidate/unverified；两处对白、一处摘要没有提供独立物种表，不能擅自认成猫狗或特定兽种。라이브 드라마暂译短剧；新2项候选不改旧453项。未核官方名或实际播放触发。
- 朱特猜测动物闻到血味、过去或许染血与洁菲提出时间/技巧不足分别照译，不升级成已证实超自然设定、杀手身份或动物行为事实。
- 母狗、鹅、兔子、猫的往事保持角色叙述；猫体弱/可能产后变差保持不确定，临终望向家为听说，不补死因，不改成小猫死亡。恢复术不补数值或疗效承诺。
- 塞蕾丝汀黏人/约会和阿尔戈特雷瓦不说谎各是角色发言，不补年龄、血缘或物种绝对定论。误认猫猫为普通猫与猫猫不是宠物的收尾保持，不把族名归并成猫。
- 003_04/004_45省略号为明确场内停顿，依既有CSMB惯例，不增加旁白，不据此处理未知PartyTalk静默字段。
- 三组Live的562条现有对白均draft，不代表全游戏文本完成；NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、旧译/held/重复occurrence保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/live3-story-batch097/workspace
python build/batch-097-verification/verify_resources.py baseline
python build/batch-097-verification/verify_resources.py modified
python build/batch-097-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT原始SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
186条双盘回填一致、旧9996条保留、7994条其余原值未改；隔离回滚恢复9996，主文件保留10182。
基线1338、修改/干净index1344测试各skip1；241输入锁、164工作区文件重建一致、727份index导出复核，错误hash回滚拒绝且目标不变。
只清理绝对路径内已核实可再生成且无依赖的干净源码测试pyc；保留原盘/配置/存档/runs/当前包/基线/回滚/研究证据。
双盘来源独立，不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口；离线不代替游戏验收。提交推送后核对远端与工作区，继续大批推进剩余界面。
