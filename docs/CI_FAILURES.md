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
