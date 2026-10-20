# 第127阶段：分盘字幕候选、独立逆重建与TOC

2026-10-20，先核对HEAD 366dbd4、远端一致、干净工作区、每轮收尾与最后批次116。没有重复翻译或新增人工定稿：仍14,082 INT draft、1104 candidate与44字幕计划/315cue。

## 分盘与源身份

subtitle-profile.json明确第一盘21资源/152cue、第二盘23资源/163cue，共44个不同资源；不是把44份都写第一盘。对两盘原ISO分别验证完整SHA256与7838695424大小，再只读XDVDFS目录并核对Movies/*.txt资源集合闭合。只读取各盘所属字幕与各自MC2Game/Xbox360TOC.txt，不生成ISO或整盘副本。

新locales/zh-Hans/subtitle-bundles/disc1.json、disc2.json锁定profile hash、disc ID与本盘原TOC hash。第一盘TOC为04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab，第二盘为65a79c3005fa344e4cf5a3c292e92fce73458813ce50ac039ffbd368f5f880f6；不能复用第一盘TOC到第二盘。

## 实现合同

subtitle_text.rebuild_reversible复用原严格rebuild，从原cue构造逆计划，再重建到原始字节完全相等；正向/逆向保留UTF16LE BOM、SYNC start/end、P class、clear事件与未选cue。原parse/rebuild函数不改。source原文仅在内存逆计划及忽略的controls中，不写入公开报告。

通用tools.build_subtitle_bundle只处理显式单盘字幕与TOC：源profile/全部计划ref hash锁定，disc ID严格整数且无歧义；每盘1..64资源、每资源至多8MiB、计划总数1..256。所选盘每个member必须有匹配resource/input SHA的计划，输入文件集合必须精确等于该盘member+TOC，拒绝其他盘文件、重复/大小写歧义、角色冲突和未知源计划。合并同资源计划时仍逐条核查来源，重叠cue拒绝，不改文字/时序或补空占位。

build先验证原ISO整体大小/hash，按inventory读取所选局部资源；写前/写后复查profile/计划原值及ISO size/mtime。全部内容在内存通过后才新建输出，逐文件重开。controls/candidate/rollback-check与reports/manifest独立；rollback-check使用现有hash保护restore_copy，不覆盖主candidate。verify不依赖ISO再次提取，而从hash锁定controls重做所有cue/TOC/报告/manifest并检查精确文件集合，拒绝漂移/符号链接。

本工具是独立有界字幕包，不放宽原build_font_route_probe额外16计划上限；不包括INT或字体，也不改变TAB coverage分类/retention含义。manifest明确cumulative_INT_included=false、fonts_verified=false、game_rendering_verified=false及deployment_performed=false。

## 两盘真实结果

build/phase-127-verification/disc1-bundle有21字幕/152cue加本盘TOC，共22局部资源；disc2-bundle有23字幕/163cue加本盘TOC，共24局部资源。全部315cue正向/逆向字节验证与时序/class/clear事件保持；两包独立controls重放逐文件相同，46个retained-original回滚资源逐字节恢复，主候选保持。

第一盘20项字幕size变化，TOC字节长度197989保持；第二盘23项变化，TOC长度199817→199816。仅更新被请求字幕行的第一个size数值，再对这些修改做逆变换恢复原TOC。两盘TOC自引用原首size均为0，且其他数值不同；保留该行原值，不因新TOC长度变化而猜补0或未知数值。对应合成回归覆盖自身长度变化而零自引用仍不变。

原ISO、当前测试目录/TOC、XEX、配置、存档、runs与当前262文本包未修改。这两个字幕包不是可直接替换的完整玩家包；字体覆盖、累计INT、分盘组合TOC及游戏验收仍分别有门禁。

## 复现

```powershell
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc1.json --output-dir build/subtitle-disc1-rebuild
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc1.json --verify-root build/subtitle-disc1-rebuild
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc2.json --output-dir build/subtitle-disc2-rebuild
python -m tools.build_subtitle_bundle --plan locales/zh-Hans/subtitle-bundles/disc2.json --verify-root build/subtitle-disc2-rebuild
python -m unittest discover -s tests -p test_subtitle_bundle.py -q
python -m unittest discover -s tests -q
```

输出须新建。build读取用户原ISO；verify只需保留的局部controls及已提交ref链。没有隐藏本机字体/完整游戏复制依赖，不把原游戏资源提交Git。

## 验证、清理、推送与接续

基线1537，新增12项后修改/索引导出干净源码1549测试均OK(skipped=1)。覆盖cue逆变换、字符串start/no-op、两盘不混合/各自TOC、来源/角色/size/hash、重复/边界64、未知/缺失计划、重叠/时序、真实文件写入重开/独立verify/篡改拒绝与原ISO坏hash拒写，并保留零自引用与未知TOC字段。

同一自造字幕样本，旧模块没有逐cue逆证明API、exit2；新helper证明时序/class/clear与原字节恢复、exit0。隔离模块副本hash保护回滚恢复旧rebuilder、exit0，重新探针恢复exit2；主MODIFIED_FILE.py保留新helper。四件证据及精确命令/输入/字面输出/退出状态见build/phase-127-verification/VERIFICATION.txt，错hash回滚拒写。真实两盘22/24资源独立回滚亦通过，非只做helper测试。

双盘INT源18176值/旧译、八源hash、24剩余分类、164文件工作区复现、64当前入口依赖/配置/XEX、candidate/raw只读核对以及125路由hash保持；workflow/terms/subtitle-profile不变。仅清理核实绝对路径的隔离源码可再生成pyc，保留原盘/配置/存档/runs/当前包和局部候选/源控制/回滚/研究。无ISO/整盘副本/模拟器启动或现有目录增量刷新。

验证清理提交推送、远端相同及工作区干净后，继续核对两盘字体来源及累计INT/字幕/字体的组合合同；TOC必须从各盘原始基线统一计算，不把两个局部候选TOC互相覆盖，不以离线通过代替游戏验收。
