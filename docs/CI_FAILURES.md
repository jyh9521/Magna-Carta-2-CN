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
