# 第九十六批：Live2散步回忆与午饭剧情（186条）

日期：2026-10-20。新增INT186条，累计9,996条draft；453项共享candidate与GLOSSARY不变，另1项历史字幕来源记录保持。未人工定稿。在第95批201条完整验证、清理和推送后，直接接续本组，无须等待用户说继续。

## 范围与语境

- CSMB_Live2_001..007完整42/17/18/37/27/28/17条。全186 dialogue，91条普通对白显式去硬换行，0功能字段、0新增held。午饭厨艺笑话、朱特与洁菲散步回忆、露向另一同伴讲述、回去用餐七场合批，不合并不同在场视角。
- 贝尔利内特王室/伊芙琳/贝尔福特/阿巴泽特/露/朱特/洁菲/阿尔戈/修恩扎伊特/艾尔加/哨兵复用旧译。9岁两处保留数字9；露更年幼不补年龄。
- 洁菲所知的露重伤、卧床未醒与露私下披露未受伤、女王雇人演戏分别照译。不要用后段秘密修改前段记忆，不给不知情角色补知情台词。
- 露说来救人的那家伙不知道演戏、看起来真心担忧又怀疑或许在演，保留矛盾与不确定。005未点名不提前补姓名，006才依源点名。两面派是角色比喻而非医学诊断。
- 幼年希望修恩扎伊特是父亲不改成血缘事实；先王不补父王。母亲之死按角色措辞，不补具体死法或动手者细节；关于正义/真心的疑问不替角色回答。
- 盐味苹果派、辣椒酱、巧克力胡椒鸡肉、三文鱼排、芥末蜂蜜鲜奶油等原有笑话成分保持，不补做法/剂量或中毒机制。首次候选香煎字样核对后删去，源只称三文鱼排；初始工作区保留，规范工作区为build/batch-096-verification/final-workspace。
- 食材/准备已完成不译成菜已上桌；预计朱特独食不写成已吃完。005_02明确场内停顿译中文省略号，不增加旁白，不据此解释未知PartyTalk字段。
- NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、旧译/held/重复occurrence保持。双盘来源独立，不表示全文或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-096-verification/final-workspace
python build/batch-096-verification/verify_resources.py baseline
python build/batch-096-verification/verify_resources.py modified
python build/batch-096-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
186条双盘回填一致，旧9810条保留，8180条其余原值未改；隔离回滚恢复9810，主文件仍保留9996。
基线1332、修改/干净index1338测试各skip1；239输入锁、164工作区文件重建一致、723份index导出复核；错误hash回滚拒绝且目标不变。
只清理绝对路径内已核实可再生成、无入口依赖的干净源码测试pyc，保留原盘/配置/存档/runs/当前包/必要基线/回滚/研究证据。
不合盘、不生成ISO/整盘副本、不启动模拟器、不刷新字库/TOC/入口；离线不代替游戏验收。提交推送核对远端及工作区后，接下一组Live3。
