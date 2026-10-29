# 可复现的提交前与 GitHub 验证

## 唯一检查入口

```powershell
python -m pip install -r requirements-font.txt
python tools/validate_ci.py --report-dir build/ci
```

本地与 `.github/workflows/validate.yml` 使用同一入口。它依次执行依赖一致性、
仓库卫生、Python 编译、生成术语表一致性、完整普通路径测试、完整路径别名测试、
固定参考下载与引用核验。每项都有日志和退出码；任一项失败则整体非零退出，
不会用后续成功覆盖失败，也不会跳过测试或放松原有检查。

路径别名模式把临时目录以真实的 `directory/../directory` 形式交给夹具；
`samefile` 核验物理身份，原始 TemporaryDirectory 仍负责清理。它在所有平台
稳定暴露路径拼写与解析后身份混用的问题，不依赖 NTFS 是否启用 8.3 名称。
生产 API 的非规范路径、目录链接、越界和哈希守卫不受影响。

## 实际推送前检查

新检出首次安装（仅本仓库的 Git hook，不改全局配置）：

```powershell
python tools/ci_preflight.py install-hook
```

已存在的其他 hook 或自定义 `core.hooksPath` 会保留并报出冲突，不静默覆盖。
之后普通 `git push` 自动检查 Git 提供的每一个待推送 commit；删除远端引用
没有代码可测试，按 Git 协议略过。版本化入口为 `.githooks/pre-push`。

也可独立验证已提交版本：

```powershell
python tools/ci_preflight.py check --revision HEAD
```

此入口从提交导出源码，逐文件核对 Git tree/blob 身份，然后创建**全新虚拟环境**，
只安装 `requirements-font.txt`，执行同一检查入口。不会带入工作区未提交的修复、
未跟踪文件、`build/`、游戏文件、用户 site-packages 或开发机缓存。
固定参考也从新快照的空缓存下载。Git hook 导出的仓库环境变量会在子仓库操作前
清除，避免新快照的 `git add` 指向原仓库的 index。

`build/ci-preflight/<运行编号>/receipt.json` 记录准确 commit、解释器、命令、
退出状态和源码不变性；旁边保留源文件摘要、安装日志及各项检查报告。
记录按运行隔离，不以旧报告或最近一次绿灯代替当前提交。若 Git archive 的
属性导致漏文件或改写字节，会在测试前报错，而不是验证一个缩水的源码集合。

## 云端验收与收尾

- 保留 Ubuntu/Windows × Python 3.12/3.14 四组，并保留 `fail-fast: false`。
- 每组都执行普通与别名两套**完整**测试；结果中的 skipped 必须保留具体原因。
- Actions 组件固定到完整提交摘要；升级须连同回归一起验证，不使用漂移标签。
- 每组无论成功失败均上传 `ci-<OS>-py<version>` 诊断，保存 14 天。
- 推送后必须查询**该提交**的 Actions，等待四组全部 success，再报告收尾成功。
  HEAD 与 origin/main 相同只说明推送成功，不说明构建成功。
- 本地 preflight 是当前操作系统、当前 Python 的严格预检；它不替代另一操作系统
  和 Python 版本的云端结果，也不承诺外部服务永不故障。
- CI 仅核验汉化工程源码，不代表字体观感、游戏启动或全流程实机验收。

已验证的负向测试会向本地临时 bare 仓库执行真实 push：提交内的故意失败被拦截，
即使工作区留着未提交修复也仍拦截；提交修复后相同入口才允许发布。

Git hook 接口与环境隔离依据：[Git 官方说明](https://git-scm.com/docs/githooks)。
诊断留存依据：[GitHub 工作流产物文档](https://docs.github.com/en/actions/tutorials/store-and-share-data)。
历史根因与本轮复现见 [CI_FAILURES](CI_FAILURES.md)。
