# 启动阶段文档审计（2026-10-18）

修改前逐份读取根目录与 docs 下全部 11 份 Markdown；保留原文模板及规范，项目实际内容置于前言或新增章节，模板例子不当成本作已实现事实。原始 SHA-256 记录如下：

|文档|原始 SHA-256|
|---|---|
|AGENTS.md|`4cc241d57a71acecb5fd615237021de830cec1ad5d2160f93e409a69375cb76d`|
|BUILDING.md|`a95c725f67e1fa2c303ab0ac7373a14c906f7c204216acdf94551b9cdbc1f7dc`|
|LICENSE-translations.md|`628961315399c200a4f93bd266ae6bd970d7efb3fce5a5f62d4b674022ef001f`|
|LICENSING.md|`f182da75c96e9e586e5bdad78f521615f4502923f63bb232a4dcbf92fd2ee0ca`|
|README.md|`c7a80fb4ba01d2e4362e7060417aa152e60e6d5df83296d519f265278cc43f98`|
|TECHNICAL.md|`aaa695bff0f737136ed436b405b78644486123899192274b30907e3b915e7a42`|
|TRANSLATING.md|`9bdddb20cc2512b2ff8c47cc76244bac3aaa77f09c93a01bfc8d4058475023de`|
|docs/FILE_FORMATS.md|`5720c2b28c18169ba0be6a1fea35fbb2672366b949c10e15a8a5f3c9684bc824`|
|docs/KNOWN_ISSUES.md|`528b7e8e3625a73a81ae4b213427b24aa05b161a946fa23647d7a02f55e85e1a`|
|docs/LOCALIZATION_STANDARD.md|`b634321ffa0599db3224ccb6b6eee388ad2c536ba9376e6c6551c86fef9862ec`|
|docs/PITFALLS.md|`ab27d3901a7f0c57563f6dfa973f41826627c5788a6ec5f349858948e949443e`|

## 模板存在情况与处理

- 已有：README、AGENTS、BUILDING、TRANSLATING、TECHNICAL、LICENSING、LICENSE-translations、FILE_FORMATS、KNOWN_ISSUES、LOCALIZATION_STANDARD、PITFALLS。
- 初始不存在：CONTRIBUTING、CHANGELOG、CREDITS、CODE_OF_CONDUCT、SECURITY、GLOSSARY、INSTALLATION_GUIDE、TESTING_CHECKLIST、BUILD_AND_RELEASE、FILEMAP。非必要模板不创建空壳；本轮新增术语、资源图、状态、测试与来源文件。
- 原目录没有 .git；GitHub 同名仓库 main 尚无 commit。新建 main，不覆盖远端历史。
- AGENTS 与 LOCALIZATION_STANDARD 已有 ignore；本轮保留本地，加入索引前检查。xenia/ 原来未整体排除，补充规则，连同 ISO / package / font / key 类文件排除。
- 通用规范示例以 zh-CN 命名，本次明确要求 zh-Hans；实际术语采用 locales/zh-Hans，不复制双份数据。
- 模板含 Windows runtime/SDK 示例，只是通用举例，本项目不采用原生重编译；已在 README/TECHNICAL 明确当前路线。
- 未发现需要推翻核心规范的冲突；原文保留，不宣称模板命令已经实现。
