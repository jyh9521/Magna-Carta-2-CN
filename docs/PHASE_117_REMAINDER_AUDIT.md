# 第117阶段：剩余原值分类与宽字符串边界审计

2026-10-20，接续116批。无新增翻译计划：INT14,082 draft、1104 candidate、44字幕315cue保持；translation-workflow最后批次仍116。本阶段不是空批次凑数，新增通用只读研究工具与可复核分类证据。

## 24项源锁定分类

locales/zh-Hans/remainder-audit.json仅存resource/容器hash及24个ID/sourcehash/定位/分类，不存原文全集或译文。分类为2明确测试样本、1孤立笑声上下文未核、3宽字符串结构异常待研究、2默认编辑样本、16无需改写的数字/标点/SID。CSM11_12/435的孤立笑声不能因邻表测试内容就认定为测试垃圾；仍需引用研究。分类不代表运行用途/玩家可见性已验证。
所有其他游戏非空未译项已有历史held记录；4094其余源值还包括编辑器、空白等，不当可译玩家总量。无需改写项不制造译文，未知格式不猜补，不翻译编辑器凑150条。

## Verified字节事实与未验证解释

双盘原INT SHA256均179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。仅MC2Game.int检测到11个0D 0A 00模式；内容头偏移895017，payload895021，去终止符390字节/hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7。payload相对偏移28/59/92/143/146/165/194/235/264/269/288，奇偶交替。
现行宽字符串解码后出现异常Unicode并让物理行提取只得到三值；容器解析/序列化仍字节完全一致，不等于INI语义正确。原始字节模式已核；生成器漏字节/混接换行/运行读取方式只是待核解释。该模式也可能来自合法U+0A0D，不可把所有命中自动修复，不能全局翻端序或补零，也不重划section/key/稳定ID。没有回写任何游戏值。

## 可复现入口

```powershell
python -m tools.audit_wide_line_boundaries --source build/disc1-selected/MC2Game/Localization/Coalesced.int --expected-sha256 179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c --output build/phase-117-verification/new-audit.json
python -m unittest discover -s tests -p test_wide_line_boundary_audit.py -q
python -m unittest discover -s tests -q
```

输出必须新建且与源不同；未知hash拒写。报告只含路径/hash/偏移/奇偶/保留策略，不含完整原文。工具没有语言硬编码，不依赖私人研究目录；合成fixture验证正常CRLF无命中、两种奇偶、窄字符串跳过、完全不修复、源hash拒写、源与既有输出保持。CLI使用模块入口，不把tests当Python包导入；针对单文件测试使用discover。

## 验证与回滚

基线1453项测试，新增7项后修改与索引导出干净源码1460项均OK(skipped=1)。24项逐ID/源hash/section/key/occurrence定位核对；双盘审计JSON相同；原容器不变。重建翻译工作区164文件与116批逐字节相同，全部18176值/14082旧译及历史held保持；workflow/terms/subtitle-profile字节不变，不新增batch117。
新工具原状态为不存在；独立工具副本回滚恢复不存在状态，主MODIFIED_FILE.py保留新增工具。错误hash回滚拒写；可执行ROLLBACK.sh和MODIFIED_FILE.py/DIFF_FILE.json/VERIFICATION.txt位于build/phase-117-verification，含精确命令/输入/字面输出/退出状态。生产源码不执行回滚。
只清理绝对路径已核实的隔离干净源码可再生成pyc，保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。
下一阶段先续查孤立笑声引用、异常边界来源/引擎读取语义，再决定是否能形成独立格式修复方案；未获证据前保持原值，不把候选当人工定稿。验证清理提交推送并核对远端后自动接续。
