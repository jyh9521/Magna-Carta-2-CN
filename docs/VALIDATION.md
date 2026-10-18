# 初始化验收记录（2026-10-18）

初始源码提交：`a6f0ddee6338c857137aa2d790366b07ebb30b80`，main 已推送；远端 ls-remote 与本地 HEAD 一致。

[GitHub Actions 首次运行](https://github.com/jyh9521/Magna-Carta-2-CN/actions/runs/39104759938)：completed / success，Ubuntu 和 Windows × Python 3.12/3.14 四个 job 全部成功。

## 实际执行

- 初始空 tests：Python 3.14 unittest discover → `Ran 0 tests` / `NO TESTS RAN`，exit **5**，不是通过。
- 修改后：`python -m unittest discover -s tests -v` → 76 tests / OK，exit 0。
- 无游戏、无本地规范、无缓存的独立 clean clone：同样 76 tests / OK，exit 0。
- `python tools/check_repository.py` → PASS repository hygiene，exit 0；index 无原版游戏、本地规范、Xenia、完整原文缓存或密钥。
- `python tools/series_terms.py check --with-references` → errors=[] / terms=0，exit 0。
- `python tools/series_terms.py render --check` → glossary=current，exit 0。
- 独立新缓存 fetch：2 references / 9 verified_files，exit 0；未以分支浮动读取替代锁定 commit。
- `python -m compileall -q tools tests` → 无输出，exit 0。
- `git diff --cached --check` → 无输出，exit 0（Markdown 原模板硬换行/空 TSV 列按属性保留，非 Markdown 正常检查）。
- 当前双盘 8 个真实 Coalesced 均 parse/serialize 原 hash 一致；单盘每个本地化候选 catalog 结构校验通过。
- .gitignore 的 BASELINE/MODIFIED/ROLLBACK 独立副本检查均 exit 0；原版 ISO 两次完整 SHA256 一致，游戏资源保持未修改状态。

## 证据保留与边界

本地 `build/verification/` 保存原始规范 hash/副本、修改副本、diff、ROLLBACK.sh、完整 VERIFICATION.txt、各命令 literal output 与退出状态、独立 clean checkout 结果及 Actions API JSON。
这些只是工具/容器/仓库检查；没有 Xenia 中文画面或修改后游戏行为证据。ignore 规则副本的回退不等同于汉化补丁游戏内回退。

后续纯文档提交的 CI 以最终交付报告所链接的最新运行记录为准。
