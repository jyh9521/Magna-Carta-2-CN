# 第七十批：巨蛾狩猎与四属性精气

日期：2026-10-20。新增INT93条，累计8,198条draft；新增12项candidate至383项，另保留1项历史字幕来源记录。
独立字幕38计划271/315cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- Quest/12_GiantMoth_0..4五组73字段、Item/FieldAction十字段与Valuables十字段同步。分类55 dialogue、15 name、5 quest_description、8 quest_progress、10 item_description。
- 接续因费尔诺后的新目标，依次核读白天现身传闻、成人礼往事/趋光推测、四属性精气、前往寂静荒野、狩猎回报。马雷族长与猎人的猜测保留“大概”“看来”，不把角色说明当运行或现实验证。
- 巨蛾的有空格主词与无空格alias、KAN精气、四种属性精气、四种容器、KAN之眼共12项候选，旧371项保持。精气不与旧试炼中的魂合并，相关物品不因同属性而归并。
- Kan_Orb的源名是칸 아이즈，描述明确是眼镜；按源名/描述暂译KAN之眼，不凭英文key译为球。未指明授予物品名的对白仍译“这个”，不凭Item位置补具体名称或脚本条件。
- 五个描述保留1/2/4/1/2处literal换行，任务18字段保留功能布局，46条普通对白显式去硬换行。所有QUEST前缀、4数值及方括号保持。
- 四处获取进度与四目标保留火/水/风/雷字段次序；描述的地点顺序水/火/雷/风独立保持。八个Item名称末尾一空格保持，十条物品描述遵循非剧情单句不加末句号规则。
- 寂静荒野、柯塔马雷、老狐峡谷、鲁哈尔特盆地、阿巴泽特、蓬蓬、霍格顿/迈耶及猎人公会沿用旧候选。无新增对应姓名或邮件字段，不重复旧译。
- Quest/12_明确前缀九组135/135字段有draft；不代表第十二章所有可见文字完成。CSMBQ11两组连携支线62条、关联任务/技能/Compose提示仍待补齐，历史held含63三处与68两处保持。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/giant-moth-batch070/workspace
python build/batch-070-verification/verify_resources.py baseline
python build/batch-070-verification/verify_resources.py modified
python build/batch-070-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
93条两盘回填一致，旧8,105条保留，9,978条仍为源值；隔离回滚恢复8,105条，主产物保留8,198条。
干净index源码测试、181项依赖锁、164工作区文件重建一致与错误hash回滚拒绝分别验证。
历史held、旧译、重复occurrence保持；字幕profile、38计划271cue、历史字幕来源及README逐字节冻结，本批不读取或导出ISO。
第69批CI run39309136489四组实际completed/success；当前提交排队/运行中不记为成功。
仅清理已核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包与研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。
下一批补CSMBQ11连携支线及关联任务/技能/Compose说明；第十三章剧情与独立字幕按后续场景接续。
