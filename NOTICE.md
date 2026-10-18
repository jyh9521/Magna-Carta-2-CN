# 来源与许可

## 独立迁移的工具

作者：jyh9521；上游：[MagnaCarta2-Recompiled](https://github.com/jyh9521/MagnaCarta2-Recompiled/tree/bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47)。
固定提交：`bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47`，MIT，版权声明见根目录 LICENSE。

- `tools/coalesced.py` ← `tools/formats/coalesced.py`
- `tools/validate_catalog.py` ← `tools/validators/validate_catalog.py`，扩展保护标记及顺序检查。
- `tests/test_coalesced.py`、`tests/test_catalog.py` ← 上游对应测试，去掉无关双盘比较依赖。

只迁移 Python 标准库工具及合成测试；没有引入 ReXGlue、SDK、PowerPC 生成代码、宿主运行时或游戏资源。
上游 Coalesced 与双盘研究仅作参考，当前资源结果以 docs/RESOURCE_SURVEY.md 和 docs/COALESCED_SURVEY.md 为准。

系列术语只读来源、固定版本与审核边界见 references/series.lock.json、docs/SERIES_TERMS.md。
原版游戏文本与资源不适用工具 MIT 许可；本地解析报告不进入公开仓库。
