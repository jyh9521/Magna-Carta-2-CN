# 阶段354：任务提示去除句末句号

## Verified：范围和根因

用户明确要求任务开始、完成及同类进度提示末尾不带句号，并补充了“消灭克洛普斯 (1 / 3)。”截图。
当前 Coalesced 的 MC2Quest.int 中共95个带任务前缀的通知字段：91处句号、4处感叹号。
包含 common/start/end/fail 和各任务的独立模板、获得物品、击杀及计数进度；没有仅修通用模板而遗漏独立条目。

阶段351的正文规则把这些记录归入 system_message/quest_progress，冒号触发补句号。
最小复现 `corrected('任务: %s 开始', 'system_message', v24_rules)` 得到 `任务: %s 开始。`。
本轮在 locale 合同中按稳定ID显式分类为 quest_notification，通用工具仅实现可配置的
`no_terminal_stop_kinds`，不含中文任务名、资源路径或特定任务判断。

## 变更和保护

- `quest-notifications-v27.json`：91条源字符串SHA256及整个输入SHA256锁定的增量。
- `terminal-punctuation-v27.json`：保留122份既有分类来源及旧未完片段例外，添加95个明确通知分类。
- 只删除最后一个中文句号；冒号、括号、%s、数值、空格、尾空格、换行及原有感叹号保持。
- 18176个记录的ID集合保持，另外18085条内容保持；新字形需求为0。
- 不删除正文、任务说明、护送警告或剧情对白的句号；v24历史增量保留用于重放。

## 重建和验证

在阶段353最终 Coalesced 输入（SHA256 `06b43f98559cad59a29d52e12d13b3a0b99d711e3c64f7baaebfa4bea8a16f1f`）上运行：

```powershell
python -m tools.build_coalesced INPUT locales/zh-Hans/quest-notifications-v27.json --output OUTPUT
python -m tools.audit_terminal_punctuation --input OUTPUT --contract locales/zh-Hans/terminal-punctuation-v27.json --report REPORT.json
python -m unittest discover -s tests -p test_quest_notifications_v27.py -q
```

输出SHA256为 `b7bb76bc8b07dcf217511cdbbebe69be19a99025530ae1ff57223e1ca576eadd`。
增量合成沿用 `tools.compose_incremental_comparison`，双盘候选由
`tools.prepare_installer_sources`按原始路径及哈希共享匹配，分别更新各盘TOC；
双盘仍为442/543资源。既有目录入口用 `tools.refresh_oneclick_probe`增量刷新。
没有生成ISO/完整游戏副本，没有启动游戏；运行中的游戏需重新读取资源后再看提示。

## 三态证据

`build/phase-354-quest-notifications/` 保存原始摘要、MODIFIED_FILE.int、DIFF_FILE.patch、
VERIFICATION.txt、可执行ROLLBACK.sh、逐条差异、双盘报告、增量刷新备份和实际命令收据。
基线检测91个尾句号，修改后0；独立副本逆向恢复原始字节及91个尾句号，修改产物保持。
回归覆盖通用/独立模板、计数、尾空格、控制符、原感叹号、剧情及任务说明。
离线资源与合同检查不代替用户的游戏内复测。
