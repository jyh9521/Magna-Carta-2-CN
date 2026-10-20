# 第九十八批：战斗风格、AI与关联界面（189条）

日期：2026-10-20。193条候选逐组核读后新增189条，累计10,371条draft；4项助词拼接/空值保持held，不为数量凑译。共享candidate468项，旧455项不改；另1项历史字幕来源记录保持，未人工定稿。

## 范围与语境

- Battle_Style36、AISetting_Description36、Navigation29、Common26、Help12、Quick7、切换语音12、教程25、任务类别2、邮件类别4合批。97菜单项、39菜单说明、17教程、12技能说明、12效果说明、12对白；177个功能字段，0去硬换行。
- Help/Left_Request_particle、Help/Change、Change_Guidence_Massage/Guidence_Massage保留：助词与输入/角色前段的拼接位置及中文词序未验。QuestCommon/QuestDeleteAlarm源空值保持；不补猜测警告。三个非空片段与一个空值均用稳定ID/hash登记。
- 普通攻击、队长、场景动作、固有技、超限、过热、反击、精华提取、连环力增幅、武器风格及地图名沿用旧候选。复核后统一普通攻击/队长/场景动作并润色巨剑表述，初始工作区保留；规范输出为build/batch-098-verification/reviewed-workspace。
- 新13项candidate：重击、狮子吼、破甲无空格变体、风之盾、连环力增幅无空格变体、连环爆发、精气吸收、连环反射、瞬杀、雷震波、气之KAN、古代灵、注视模式。古代灵与旧古代之魂不凭相近字面合并为同实体；不核官方名或机制运行。
- 太刀风格名/短刀描述及弓的冰之连环术/水属性减伤各依源，不擅自改齐。2倍、耐力恢复30、20%/30%、受属性伤害固定1、1对多/1对1均保留；一定概率不补具体百分比，不把受伤害固定1改成攻击伤害。
- Styles及A/B/X/L/U字面顺序保留，不按常识改为扳机或摇杆。Tutorial1/BtA_Guide两个occurrence的日文終了/韩文끝均独立译结束，不覆盖ID；Tutorial4/Text1换行前1空格及13处功能换行保持。
- 固有技不耗耐力、超限阶段与攻击结束后只能移动直到恢复依原说明，未增补教程没给出的按钮或公式。AI优先级仅翻译源声明，不代表算法实测；邮件类别改显示值，不改枚举key。
- 导航按实际源值：silence_land为阿巴泽特草原、south_door为寂静荒野、Stras_grave仅石碑，不补墓主；公会联盟不改成商人公会。转场语音保留敬语/语气，不根据键名补角色身份。
- NPC1443/1473、邮件正文128/235、44字幕315/315已提取cue、README、所有旧译/held/重复occurrence保持；双盘来源独立，不表示全文或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-098-verification/reviewed-workspace
python build/batch-098-verification/verify_resources.py baseline
python build/batch-098-verification/verify_resources.py modified
python build/batch-098-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
189条双盘回填一致、旧10182条保留、7805条其余原值不改；隔离回滚恢复10182，主文件保留10371。
基线1344、修改/干净index1350测试各skip1；243输入锁、164工作区文件重建一致、731份index导出复核；错误hash回滚拒绝且目标不变。字体与游戏行为未验。
只清理绝对路径内核实可再生成且无依赖的干净源码测试pyc，保留原盘/配置/存档/runs/当前包/基线/回滚/研究证据。
不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口；离线不代替游戏验收。提交推送后核对远端与工作区，再接完整大批剩余界面。
