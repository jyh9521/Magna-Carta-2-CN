# 第一百一十二批：剩余邮件与阿尔戈支援（158条）

日期：2026-10-20。从111批接续160候选，新增158条INT draft，累计13,235；新增12项candidate共1096，旧1084保持。Test占位与纯省略号主题共2held。

## 完整功能组与源语境

- 邮件105字段：52主题、53正文；Argo支援53对白合批，不每几十条单独收尾。邮件现在233/235，余Test더미及E02_016六点主题全部held；其正文独立draft，新增52对完整标题/正文及另1正文，不声称全部53封都已全字段译完。
- Q02任务提示、B02战斗书信、E02背景/系统介绍及E09余项连同Argo完整支援动作组核读。E02_002节实际key仍E02_001_Sub/Con，section/ID区分，不修key；来源保留INT与盘别，Argo日文源不是借JPN覆盖。
- 复用破甲、爆裂拳、神圣涟漪、精华提取、卡蒙德盘/插孔、饰品加工、库布、希昂·雷格拉尔、蓬蓬、炽热之心等。初期化标签核对既有MC2UI_Field/Kamond_Initialize为初始化，修正仅本批未提交草稿，旧13077条不改，初次术语审读计划/工作区保留。
- 胖胖/波蓬、伊格尼斯族、南部护国军/北部守护军、引燃、热血、大地之民和日文角色名仅candidate；不证明官方译名、族群身份或跨表对象相同。Argo声口沉稳，角色呼唤与援助/成功/失败状态各保留独立ID，源相同不合并。
- E02_012/014千年前与约1300年前、E02_015的2年前/第3年/2年前均保留，不修时间线；传说/据说与书信作者推测不变成研究事实。经验100%/70%/100%、AI类型次序与热血火免疫/50%减伤按源，不验证机制。
- E09写恸哭之壁，而B02为恸哭之门，各按壁/门译；Q02_004源为爆裂拳且要求锤，不改爆裂锤。B02_002力量KAN不因其他教程气之KAN改写。信件颜色组合、材料与属性差异各按源，不推演修正。
- 481功能换行、47空白段落行、27对方括号、14对半角括号、4百分号、2处全角１、5处AI、1处HP、8波浪线及数字顺序/行边空白保持。Argo的HP_30等key不据此补写数值。
- 写计划前的行数检查发现E02_014/023候选多一视觉行，已恢复源行数/段落边界，初次基线工作区与复核记录保留。所有新增保持draft，旧1084候选不变。
- Verified仅指源值/格式/回填；邮件叙述、支援配音/字幕使用和战斗效果未作运行验收。不盲对齐com/communi或跨locale表。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-112-verification/terminology-workspace
python build/batch-112-verification/verify_resources.py baseline
python build/batch-112-verification/verify_resources.py modified
python build/batch-112-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c；回填一致，旧13077及4941个其余源值保持，所有历史held/新held2核对原值/hash。
基线1428测试，新增六项source-free合同覆盖完整组/占位与主题held/段落和数值形态/菜单与壁门源差异/候选与别名/输入锁和字幕。完整验证含164文件逐字节复现、索引导出干净源码测试、独立回滚与错误哈希拒写。
隔离回滚恢复13077条旧译，主MODIFIED_FILE仍13235；四实物及精确命令/输入/字面结果/退出状态见build/batch-112-verification/VERIFICATION.txt。
只清理绝对路径已核实的隔离源码可再生成pyc；原盘/配置/存档/runs/当前包/依赖/基线/回滚/研究保持。不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口。
Compose836/921、Item1608/1630、44字幕315cue保持；离线成功非游戏验收。验证清理提交推送核对后接续其余四角色支援289候选（Juto71/Crocell68/Celestin88/Zephi62）；预审Zephi/Celestin/Abnormal_bad_ch3_01未知\じっと整条待查，不补n，其他也逐条核读。4941个含编辑器/样本原值不是玩家待译总量。
