# 《真名法典2》简体中文汉化

Xbox 360 版《MagnaCarta II》的简体中文汉化项目，包含结构化译文、可重建工具链与技术研究。

## 当前状态

**开发与测试中，尚非完整汉化发行版。** 自动检查通过不等于完成校对或游戏内验收。

当前面向已校验的韩版 Disc 1 / Disc 2，以 Xenia 为主要测试环境；两盘独立构建，不做双盘合一。
仓库不包含游戏本体、原版镜像或本地测试包，重建需自行提供匹配版本的原始文件。

最近一轮实测修订见 [阶段330：数字比例、正文排版与UI](docs/PHASE_330_GAMEPLAY_QA.md)。
该记录保留全量扫描分母、原有控制符待核实项和离线/游戏内验收边界。

2026-11-08追加返工：14张装备立绘的残留／右倾方向，以及11段Boss／恸哭之门过场特写，
见 [装备重制](docs/PHASE_360_EQUIPMENT_REMAKE.md)与[时序字图重制](docs/PHASE_363_TEMPORAL_TITLES.md)。
旧涂抹原型已退役；新资源经过离线原生检查与成品回解，游戏／用户美术验收单列。
剧情过场后的独立大章节名称仍在[修复列表](docs/GAMEPLAY_FIX_LIST.md)追踪，不以地图地名或Boss影片冒充完成。

同日29项遗漏修复见[阶段365](docs/PHASE_365_OMISSION_REPAIRS.md)：11段地图目的地动画、
两段换碟提示、8种属性字图及8条任务通知前缀全部进入源锁修复；背景先独立清底验收，
再检查实际编码成品。双盘累计471／573项资源及2项DLC沿用原测试目录与同名v1.0安装器。
大章节调查新增[真实过场结束显示链路](docs/PHASE_365_POSTCUTSCENE_TITLE_ROUTE.md)，
但用户所报的独立章节卡身份仍未闭合，继续单列。

2026-11-11追加[碑文与残留修复](docs/PHASE_367_RESIDUAL_REPAIRS.md)：用户图2的海底洞窟碑文、
其余40个文本字段及11处“大炮”名称已更新到原测试副本和同名v1.0安装器。
94个待核身份逐项记录为52修改、30有条件保留、12继续待核；严格门禁不伪报全量清零，
游戏内修复观感仍需复测。

## 文档入口

Windows 图形安装器候选版：[使用、构建、ZAR/XEX/DLC与验收说明](docs/INSTALLER.md)。
采用新版 LOGO，右下角「伯翎飞云」链接至 <https://blog.blfy.cc/>。

| 内容 | 文档 |
| --- | --- |
| 构建与测试 | [构建说明](BUILDING.md) · [支持版本](docs/RESOURCE_SURVEY.md) |
| 提交前与云端验证 | [统一 CI 入口与推送检查](docs/CI_VALIDATION.md) |
| 图形安装器 | [安装/构建/故障恢复](docs/INSTALLER.md) · [更新记录](CHANGELOG.md) |
| 翻译与术语 | [翻译说明](TRANSLATING.md) · [术语表](GLOSSARY.md) |
| 技术与格式 | [技术说明](TECHNICAL.md) · [文件格式](docs/FILE_FORMATS.md) |
| 进度与问题 | [翻译接续点](docs/TRANSLATION_QUEUE.md) · [已知问题](docs/KNOWN_ISSUES.md) |
| 开发记录 | [专项文档](docs/) · [历史阶段记录](docs/README_HISTORY.md) |

## 问题反馈

请附测试包版本、Xenia 版本、场景、复现步骤，以及截图或日志。

## 许可

原创代码：[MIT](LICENSE)；原创译文：[CC BY-SA 4.0](LICENSE-translations.md)。
第三方组件与字体的许可见 [NOTICE](NOTICE.md)；原版游戏资源不属于上述授权范围。
