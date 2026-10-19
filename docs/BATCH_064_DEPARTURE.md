# 第六十四批：装置完成、辞别与护送出发

日期：2026-10-20。新增INT76条，累计7,772条draft；352项共享candidate及1项历史字幕来源记录。
字幕37计划270/315cue、邮件116/235保持，均未人工定稿。

## 范围与上下文

- CSMB12_005/007/008/009/010/020六段66条，按装置完成、辞别、另一侧对话、出发与装置运送推进；劳德对峙与后续仪式尚不提前混入。
- Compose12_01-10十字段同步：六条护送/安装目标、准备询问、X/Y出发菜单与两条等待对白。
- 分类63 dialogue、12 narrative、1 menu_option；007末六条为紧张与出发的收束叙事，不按CSMB文件名全部归对白。
- “像父亲一样”保持比喻，不改成生父关系；008未明说的身份不擅加姓名。高速移动装置只作角色自命名候选，不把自述当实际性能实测。
- 鲁哈尔特盆地/高原、血之契约、主人、伊格顿等复用共享译库。相关盆地场地名两字段已译，不重复计数；辞别NPC也沿用既有成果，本阶段提取未见12_前缀NPC字段，不泛称游戏没有其他NPC显示。

Verified / source/offline：七条功能字段原换行计数1/1/1/0/0/1/1保持；首目标尾随空格保持。X/Y菜单四个Styles标签、X/Y顺序、标签后空格及功能换行原样保留，仅翻译选项文字，不改按键或触发。非剧情单句选项不加末句号。38条普通对白/叙事显式去硬换行。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/departure-batch064/workspace
python build/batch-064-verification/verify_resources.py baseline
python build/batch-064-verification/verify_resources.py modified
python build/batch-064-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
76条两盘回填一致，旧7,696条保留，10,404条仍为源值；隔离回滚恢复7,696条，主产物保留7,772条。
干净index源码测试、168项依赖锁、164工作区文件重建一致性、旧351项术语保留/新1项追加与错误hash回滚拒绝分开验证。
历史held含63批三处疑词/残句及重复occurrence保持；字幕profile、37计划270cue、历史字幕来源与README逐字节冻结，本批不读取或导出ISO。
第63批CI run39300818130四组均completed/success，实际jobs保留；当前提交排队/运行中不记为成功。
仅清理核实绝对路径下可再生验证pyc；保留原盘/配置/存档/runs/当前包及研究/回滚证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB12_030劳德对峙接后续护送/设置装置阶段，核读同阶段叫喊、目标提示与关联名称；12-80独立字幕尚未到对应场景，不重复导出。
