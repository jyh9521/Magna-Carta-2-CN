# 第九十批：伤员救治与作战指令书

日期：2026-10-20。新增INT66条，累计9,192条draft；共享candidate432项，另有1项历史字幕来源记录。未人工定稿。

## 范围与语境

- 02_3_01伤员任务15、03_302_2传令兵13/0指令16/1军官16、Tutorial_Scene_22四、Item指令书二同步；46 dialogue、6 name、3 system_message、1 menu_option、4 quest_description、2 quest_objective、3 tutorial、1 item_description。
- 31条普通对白显式去硬换行，20个功能字段保留布局；四个%s、QUEST、[]、HP/A/X与0/3数字、教程空段及前后空白保持。
- 救援小游戏与柯塔马雷情报链分别核读；后者按传令兵/指令/军官的信息线阅读，不以写入顺序证明实际任务触发。先备战勿主动进攻、可先发制人的提议、另一个角色拟消灭军官均按各源发言保留，不替人物统一战略。
- 救援目标要求全部存活，完成对白只说把损失降到最低，各按源保持，不改成成功保证零伤亡。连环术争取时间、补给抵达、HP随时间减少不补时限或减少速率；拒绝/失败/完成分支各自保留。
- 教程仅洁菲、左摇杆、A一个KAN小回复/X两个KAN大回复、HP为0前治疗及定期生成KAN按源保留，不补游戏公式。命令对象北部军位置已掌握与努伦斯具体位置未知并非同一句结论，不给坐标。
- 努伦斯、作战指令书有空格/无空格两源变体、北部军传令兵、伤员救治新增5项candidate至432；旧427项不改。基洛蒂/柯塔马雷/水色湿地/马雷族/洁菲/连环术/KAN/阿巴泽特/老狐峡谷沿用候选。努伦斯未见独立名字段，不造官方英文或运行人物绑定。
- north_command实际Item名为作战指令书，不按任务全名加北部军前缀；源空格变体不合并ID或改源。Order_01按需要与否暂分菜单选项，实际调用未验，不依键名补剧情。同义yes/in两组各自回填。
- NPC1443/1473及余30占位/未知标记、邮件128/235、44字幕315/315已提取cue、README和全部旧译/held/重复occurrence保持；这些计数不表示全部游戏文本或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/relief-orders-batch090/workspace
python build/batch-090-verification/verify_resources.py baseline
python build/batch-090-verification/verify_resources.py modified
python build/batch-090-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
66条新译双盘回填一致，旧9,126条保留，8,984条其余原值未改；独立回滚恢复9,126条，主文件保留9,192条。
基线1296、修改/干净index1302测试各skip1；227依赖锁、164工作区文件重建一致、699份index文件复核及错误hash回滚拒绝分别验证。
GLOSSARY由432项结构化源渲染核对，旧427项不变；README、字幕profile/全部计划/历史候选冻结。只清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和工作区干净状态，当前CI按实际结果记录。
