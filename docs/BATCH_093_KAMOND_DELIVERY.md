# 第九十三批：卡蒙德碎片收集与递送

日期：2026-10-20。新增INT36条，累计9,355条draft；共享candidate440项，另1项历史字幕来源记录不变，未人工定稿。

## 范围与语境

- 03_363_0完整18条、03_363_1完整14条及Valuables/broken_kamond与包裹名/说明4条同步；26对白、4名称、2任务说明、1系统提示、1目标、2物品说明。
- 15条对白显式去硬换行，10功能字段保留布局；3个%s、QUEST/[]和两处8个保持。com_04对白与物品名源尾各1空格保留；同义yes/in分别保留ID。
- 卡蒙德碎片的파편/조각两种源词及碎片包裹新增3项candidate，旧437项不变；别名只基于本支线同对象语境，不修改原文。阿巴泽特/猫猫/阿维斯商人复用共享候选。
- 碎片让炸弹更强是角色的说法，不扩成伤害公式或制作教程；下次作战炸弹保管是主动提议，不改成已经保管。最近未见商人不补失踪/死亡或原因。
- 普通Ingredient/Small_piece_of_Kamond名/说明另有小碎片，不因相似词组混入任务Valuables或断言同物。包裹说明使用实际_B键，不改成猜测的_D。
- 第92批测试将术语总数等于437改为至少437，让追加候选可继续；旧候选前缀及内容另经全字节/结构比对，不放松旧译保护。其余通用工具未改。
- NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、全部旧译/held/重复occurrence保持；不表示全文或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/kamond-delivery-batch093/workspace
python build/batch-093-verification/verify_resources.py baseline
python build/batch-093-verification/verify_resources.py modified
python build/batch-093-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
36条双盘一致、旧9319条保留、8821条其余原值不改；隔离回滚恢复9319，主文件保留9355。
基线1314、修改/干净index1320测试各skip1；233输入锁、164工作区文件重建一致、711份index导出复核，错误hash回滚拒绝且目标不变。
只清理经绝对路径及无依赖核实的干净源码测试pyc；保留原盘/配置/存档/runs/当前包/必要基线/回滚/研究证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线不代替游戏验收。提交推送后核对远端一致和工作区干净，CI按实际可读状态记录。
