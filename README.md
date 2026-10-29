# 《真名法典2》简体中文汉化

Xbox 360 版《MagnaCarta II》的简体中文汉化项目，包含结构化译文、可重建工具链与技术研究。

## 当前状态

**开发与测试中，尚非完整汉化发行版。** 自动检查通过不等于完成校对或游戏内验收。

当前面向已校验的韩版 Disc 1 / Disc 2，以 Xenia 为主要测试环境；两盘独立构建，不做双盘合一。
仓库不包含游戏本体、原版镜像或本地测试包，重建需自行提供匹配版本的原始文件。

最近一轮实测修订见 [阶段330：数字比例、正文排版与UI](docs/PHASE_330_GAMEPLAY_QA.md)。
该记录保留全量扫描分母、原有控制符待核实项和离线/游戏内验收边界。

## 文档入口

| 内容 | 文档 |
| --- | --- |
| 构建与测试 | [构建说明](BUILDING.md) · [支持版本](docs/RESOURCE_SURVEY.md) |
| 翻译与术语 | [翻译说明](TRANSLATING.md) · [术语表](GLOSSARY.md) |
| 技术与格式 | [技术说明](TECHNICAL.md) · [文件格式](docs/FILE_FORMATS.md) |
| 进度与问题 | [翻译接续点](docs/TRANSLATION_QUEUE.md) · [已知问题](docs/KNOWN_ISSUES.md) |
| 开发记录 | [专项文档](docs/) · [历史阶段记录](docs/README_HISTORY.md) |

## 问题反馈

请附测试包版本、Xenia 版本、场景、复现步骤，以及截图或日志。

## 许可

原创代码：[MIT](LICENSE)；原创译文：[CC BY-SA 4.0](LICENSE-translations.md)。
第三方组件与字体的许可见 [NOTICE](NOTICE.md)；原版游戏资源不属于上述授权范围。
