# 第120阶段：累计译文与当前测试包的字形覆盖门禁

2026-10-20，接续119需求预审。不新增译文或翻译batch，INT14,082 draft、1104 candidate、44字幕315cue及workflow最后116保持。此阶段复用既有工具，不增加同功能审计器。

## 包身份与范围

当前PREPARED指向build/readability-spaced-disc1，manifest SHA256 f3cf0551119094a3f1856a51443e508aadf8336c91546614564b228b3a500618。44个manifest成员加候选/原文对照20资源，共64项hash引用逐项匹配；两个XEX及现有配置hash也匹配。独立调用verify_resource_phase核验candidate/raw-controls各10/10资源，只写本阶段报告，不调用启动器，不写runs。
既有包262条INT/717码点在七别名下显式remap覆盖通过；不因此宣称累计14,082译文已入包。当前包的Coalesced/四份旧字幕与累计源计划范围不同，保持原样，不单独投放新文本制造空字。

## 实测覆盖缺口

复用tools.audit_text_font_coverage，从原INT及累计hash计划内存重建/逐ID回提/反向回原字节，对当前包实际七别名审计。累计INT范围2446码点：General_15三别名和SmallFont两别名各缺1612 remap，Subtitle两别名各缺1611；每个别名另有U+0009一个control-or-format-literal-unverified。覆盖门禁返回exit1，非输入/解析错误exit2。
进一步用既有load_font/font_coverage核查全部315独立字幕联合需求：2451码点，五别名各mapped834/missing1616/control1，字幕两别名各mapped835/missing1615/control1。字幕额外五码点为21009/28382/31713/34615/39278，其中四个增加缺口。联合字形需求不等于每条都实际使用所有别名；别名运行选择、像素alpha、atlas边界和游戏显示仍未验收。
U+0009保持译文与源原形，不自动删除、不当普通可见字栅格化；当前审计保守记未核。glyph_limit是新增字数量限制，不是总需求码点限制，不能单凭2451就断言生成器超限；源基线/透明字修复需求仍须分别核算。

## 可复现证据

完整七组--font-package参数与hash保存在build/phase-120-verification/coverage-commands.json，使用仓库已有CLI；BASELINE-command.json和MODIFIED-command.json记录原始命令、输入和字面结果。coverage_check.py复跑同一参数：

```powershell
python build/phase-120-verification/coverage_check.py baseline
python build/phase-120-verification/coverage_check.py modified
```

baseline exit0：262/717、all_fonts_cover_literals=true；modified预期exit1：14082/2446、all_fonts_cover_literals=false。不是通过门禁，更不是已修复缺口。all-text-coverage.json另存联合2451码点的显式remap结果；报告无完整原版资产。公开locales/zh-Hans/coverage-readiness.json只存源/工作流/包hash与七别名/分范围计数，保留scope与false状态。

## 验证、回滚与接续

基线1471测试，新增五项source-free快照合同；修改及索引导出干净源码1476测试均OK(skipped=1)。八源hash/24项余项分类、全部18176值/14082旧译及历史held保持，翻译工作区164文件与116逐字节一致；workflow/terms/subtitle-profile不变。
MODIFIED_FILE.json是累计范围缺口报告，不是游戏改包。独立报告副本回滚恢复262条通过的基线报告，主报告保持累计覆盖门禁失败；没有“回滚字体后解决缺字”的含义。可执行ROLLBACK.sh、错误hash拒写、DIFF_FILE.json、VERIFICATION.txt及精确命令/输入/字面输出/退出状态保存在build/phase-120-verification。
只清理绝对路径核实的隔离干净源码可再生成pyc；保留原盘/配置/存档/runs/当前测试包/依赖/基线回滚研究。未生成新ISO/整盘副本、未启动模拟器、未刷新字体/TOC/入口。离线覆盖缺口不等于游戏截图验收。
下一阶段继续核对源字体、三族补字需求/透明字修复/尺寸与像素门禁，以及U+0009处理策略，预备累计字库方案；不绕过未知控制语义，不自动缩字或翻译占位凑数。全套离线回滚验证通过后再按既有hash保护流程增量刷新测试目录，继续区分离线与游戏验收。清理提交推送远端核对后自动接续。
