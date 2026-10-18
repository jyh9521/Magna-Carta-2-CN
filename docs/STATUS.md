# 当前状态（2026-10-18）

## 已完成

1. 审读现有 11 份 Markdown；原模板保留，当前事实单列，见 DOCUMENT_AUDIT.md。
2. 空远端对应目录初始化 main；本地规范、ISO、Xenia、完整原文及派生资源排除。
3. 两份系列 GLOSSARY 完整读取；固定 2 个 commit、9 个文件 SHA256；参考 2139 项、共有原词 9、字面译名冲突 0，见 SERIES_TERMS.md。
4. 本项目 terms.json 为唯一术语维护源，当前 0 项、继承 0 项；生成 GLOSSARY，避免把同名当同概念。
5. 两盘 XDVDFS 完整目录、全文件 SHA256、双盘差异；XEX2 title/media/disc 身份，见 RESOURCE_SURVEY.md / FILEMAP.md。
6. 独立 MIT Coalesced 提取器、通用记录校验器；8 个真实容器全部 byte-identical 内存往返；本地化物理行候选每盘 35901（不是可见剧情数）。
7. 76 个自制数据单元测试通过；真实缓存 fresh-fetch 9 文件通过；术语结构与 GLOSSARY 同步检查通过；compileall 通过。
8. .gitignore 修改副本/原始 hash/diff/回退脚本及独立副本恢复测试成功，证据保存在本地 build/verification/。该恢复测试不代表游戏汉化回退验收。

## 里程碑

|项目|状态|
|---|---|
|1 固定系列参考机制|完成；人工确认继承为 0|
|2 从当前原版提取实际文本|Coalesced 子集完成；全包/剧情覆盖未确认|
|3 无损提取与回写|容器内存无修改往返通过；磁盘回写及资源加载未实现|
|4 Xenia 中文与实际回退|未验证；没有中文部署或画面证据|
|5 字体/布局/术语游戏验收|未验证|
|6 全游戏汉化|未开始|

## 尚未解决

- 从文件名可知输入标为 Korea；其他发行版本、Title Update、DLC 不在已验证资源集合内。
- .xxx 只校验包头候选；包压缩、font 字符映射、glyph atlas/metrics、简中覆盖未解析。
- INT 实际含韩文；KOR/INT 的运行时优先级及本地化查找绑定未验证。
- Xbox360TOC 更新、重封装、存档兼容、换盘、完整游戏流程均未验证。
- 两上游字面无冲突不代表其世界观概念相同；别名/称号使用仍需语境复核。

## 下一轮唯一优先任务

追踪启动提示 `MC2UI_TCR.int [GameStart] LogIn_NewGame` 在原版 Xenia 中的真实读取与字体绑定，取得原版同场景基线；在完成此证据前不开展批量剧情翻译或宣称补丁可用。

提交、推送、Actions 结果以本次交付报告与 GitHub 实际运行记录为准；此文档不预先宣称远端 CI 成功。
