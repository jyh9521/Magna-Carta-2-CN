# Windows 连续四次失败与提交前检查闭环（2026-10-30）

## 已验证的根因

运行 `40813213682`、`40925799658`、`40937260175`、
[40953504077](https://github.com/jyh9521/Magna-Carta-2-CN/actions/runs/40953504077)
分别对应 `291adee`、`a43acbf`、`14c9919`、`c0dc373`。
四次都是 Ubuntu 两组成功，Windows 两组失败。实际日志中的失败点相同：
`RevisionLayerTests.test_locked_replacement_roundtrip_and_immutable_inputs`，
`ValueError: new canonical output directory required`。不是最近载入动画、DLC、
资源包装或 Pillow 安装引起的另一种错误。

夹具把临时目录的原始拼写直接用于输出；hosted Windows 的 TEMP 使用短名时，
不符合 compose_revision_layers.build 明确要求的 canonical 输出契约。
本机普通路径及普通干净检出都可能通过，因而此前只验证这两种场景漏掉了错误。
同一夹具在本地真实 `directory/../directory` 别名上稳定复现完全相同的异常。
基线完整别名套件 2651 项检出 12 项失败/错误：1 项是实际云端故障，另 11 项
属于 compact_outputs 夹具意外触发明确的 `..` 禁止规则，不是 11 个新云端故障。

## 修复与防回归

- 仅在两组合法输入夹具处解析 TEMP 的规范路径。生产构建器/压缩整理工具未改，
  增加直接的非规范输出拒绝断言，保留哈希、越界和 reparse-point 检查。
- 跨平台回归在修复前已失败；整个测试集合新增别名模式，不只追补当前一个函数。
- 单一本地/云端检查入口、新虚拟环境和精确提交快照，阻止未提交修复或本机依赖
  造成假绿灯。导出还逐文件核对 Git blob，禁止 archive 属性漏掉源码。
- 真实临时 Git remote 验证 pre-push 的红/绿行为、未提交修复隔离和原 index 不变。
- 四组矩阵与失败传播保持；新增失败日志产物，checkout/setup-python 更新到已核对
  的 v6 提交。生产运行和原始游戏资源不变。

完整入口、安装与推送后验收规则见 [CI_VALIDATION](CI_VALIDATION.md)。
本轮基线、修改、独立副本逆补丁、固定输入摘要及云端结果保存在
`build/phase-334-ci-hardening/`。后续是否收尾必须看精确提交的四组实际结果，
不把本文或一次本地 PASS 当成未来运行证明。

# GitHub Actions 生成术语表不同步（2026-10-28）

## 已验证的根因

[失败运行 40704616373](https://github.com/jyh9521/Magna-Carta-2-CN/actions/runs/40704616373)
对应提交 `8f3b2eac59cdef04ea7a5953f07bedcacefe77e0`。Ubuntu / Windows、Python
3.12 / 3.14 四组均在最后的 `series_terms.py render --check` 失败；此前的单元测试、
依赖、仓库卫生和固定来源术语检查均通过。

`locales/zh-Hans/terms.json` 中 `mc2-calamity-144` 已改为“真名法典”，但未同步生成
`GLOSSARY.md`。本地同命令重现 `error: generated glossary out of date`（exit 2）。
连续两次生成内容完全相同，与旧表只差这一条译名；不是换行符或平台差异。

## 修复与防回归

- 使用 `python tools/series_terms.py render` 重建术语表，不手工绕过生成器或 CI 校验。
- 在 `test_series_terms.py` 增加仓库源文件一致性测试，直接调用与 CI 相同的
  `render --check` 入口；不取网络参考、不读游戏文件，也不自动改写过期文件。
  该测试在生成前失败，生成后通过，使默认单元测试也能及时发现漏提交生成物。
- 修改术语后，结构源与生成表必须一起提交；原四组 CI 和全部失败检查保持。
- README 只保留简介、状态和文档入口；第 289–316 阶段文字移至
  [历史阶段记录](README_HISTORY.md)，后续工作记录不再堆在首页。

```powershell
python -m unittest discover -s tests -p test_series_terms.py -v
python tools/series_terms.py render --check
```

三态命令、源文件散列及隔离回滚证据保存在
`build/ci-glossary-readme-20261028/VERIFICATION.txt`。独立副本恢复旧术语表后，
检查应重新报告过期；工作区保留同步后的术语表。本轮不改游戏资源、测试 ISO 或图片。
云端结果以修复提交对应的四组 Actions 为准，不以本地通过替代。

# GitHub Actions 路径别名回归（2026-10-27）

## 已验证的根因

[失败运行40372071810](https://github.com/jyh9521/Magna-Carta-2-CN/actions/runs/40372071810)
对应提交 `75015c701073a1db75d605e4a850c224e603ef64`。Ubuntu 的 Python
3.12/3.14 均通过；Windows 两组均在 2206 项测试中出现同一处断言失败：
`AuthoredGlyphBuilderTests.test_builder_resolves_and_snapshots_glyph_bytes`。

临时目录返回 `C:/Users/RUNNER~1/.../glyph.png`，而真实构建器
`build_texture_overlay.prepare()` 经 `Path.resolve()` 和 `confined_path()`
记录 `C:/Users/runneradmin/.../glyph.png`。两个路径指向同一文件，SHA256
均为 `5d83d313422584700dab9a54b26d268a3422b08845bd27cb93287b09c7478495`，
但原测试把未解析的路径直接放入预期元组，造成路径拼写不等的误报。
这不是图片损坏、依赖安装失败或 Python 版本特有的生产构建错误。

本地用真实 Windows `GetShortPathNameW` 路径复现：同一解释器、依赖和
合成输入下，完整路径通过，8.3 短路径失败。跨平台的 `spelling/..` 输入
也复现相同断言；两种输入均先验证 `samefile` 和解析后的身份。

## 修复与防回归

- 原 fixture 只将预期快照路径改为 `file.resolve()`，仍精确核对路径与
  文件 SHA256；不修改生产构建器、纹理计划、译文或已生成游戏资源。
- `test_ci_portability.py` 新增路径别名回归，实际调用原 glyph fixture
  和构建器。用真实存在的 `spelling/..` 目录拼写制造未规范路径，不模拟
  `Path.resolve()` 或构建器，也不依赖 Windows 短文件名功能或符号链接权限。
- 新回归在修复前已失败；错误哈希、越界路径、私有字段注入及不支持的
  图像尺寸/模式仍由原测试覆盖。四组 CI 和失败通知保持原样。

```powershell
python -m unittest discover -s tests -p test_ci_portability.py -v
python -m unittest discover -s tests -p test_image_review_v4.py -v
python -m unittest discover -s tests -v
python tools/check_repository.py
```

三态命令、原始散列、真实短路径复现、隔离回滚和远端运行记录位于
`build/ci-path-alias-20261027/VERIFICATION.txt`。回滚只在独立源码副本演练，
恢复旧测试后应再次出现路径别名失败；工作区保留修复。此轮不生成 ISO、
完整游戏副本或重新编码图片；现有测试包、配置、存档和运行记录保持。

# GitHub Actions 持续失败修复（2026-10-19）

## 已验证的根因

[失败运行39242431898](https://github.com/jyh9521/Magna-Carta-2-CN/actions/runs/39242431898)
包含两项独立问题，不是翻译内容损坏：

1. Ubuntu两种Python的单元测试已通过，但后续术语检查报
   `referenced project terms require --with-references`（exit2）。
   workflow仍调用旧命令，既没有取回固定参考文件，也没启用引用核验。
2. Windows相对路径测试在调用被测函数之前失败：checkout在D盘而TEMP在C盘，
   `os.path.relpath`未指定start，从不同盘符计算相对路径，抛出ValueError。
   本机C盘checkout和C盘TEMP未触发这个条件，因此先前本机绿灯并不证明云端通过。

## 修复与防回归

- workflow先执行series_terms fetch，再check --with-references；参考的commit和SHA256
  仍由series.lock锁定，不使用最新版、不放宽校验、不修改译文/候选审核状态。
- 使用全新缓存验证2个参考项目、9个文件，避免把开发机缓存存在当CI前置条件。
- 相对路径fixture通过contextlib.chdir从自己的root解析`Path('run')`，退出时恢复原目录。
  Popen仍为mock；不启动模拟器，也不改生产启动器、游戏资源或用户工作目录。
  首轮云端复核发现Windows Python3.14.8路径实现会绕过mock getcwd而使用真实OS目录，
  因此不能只mock getcwd；已增加stat('.')核对真实目录和退出恢复的回归。
- 新增CI回归：检查fetch/check顺序与参数；强制relpath抛跨盘错误时仍能执行真实原测试。
- 实际用临时Q盘映射仓库、C盘TEMP复现原始失败，并在相同跨盘条件确认修复通过；
  映射只用于测试，验证后解除，不移动或复制完整游戏目录。
- matrix设置fail-fast:false，使四组检查各自完整报告，不再因另一组先失败而被取消。
  保留全部检查，不添加continue-on-error，不关闭Actions或失败邮件通知。

## 验证与证据

```powershell
python -m unittest discover -s tests -p test_ci_portability.py -v
python -m unittest discover -s tests -q
python tools/series_terms.py --cache build/github-ci-fix/fresh-references fetch
python tools/series_terms.py --cache build/github-ci-fix/fresh-references check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

新回归在修改workflow和原fixture前已运行并出现2项失败，再修复为通过。
本地build/github-ci-fix保存源代码基线、独立回滚副本、差异和验证记录。
独立回滚恢复原workflow与fixture后应重新出现原来两项失败；主工作区保持修复。
云端验收以修复提交对应的Ubuntu/Windows、Python3.12/3.14四项Actions全部success为准，
不以本地通过替代。历史失败记录和已发送邮件不删除；本修复针对后续运行的根因。
