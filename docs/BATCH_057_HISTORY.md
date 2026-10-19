# 第五十七批：五碑机关与古代记录

日期：2026-10-20。新增INT92条，累计7,195条draft；330项共享candidate及1项历史字幕来源记录。
字幕35计划254/315cue、邮件116/235字段保持，均未人工定稿。

## 范围与上下文

- CSMB11_03/05/08/09四段85条，Compose11_07-11五块碑文，Item/Valuables马雷族印章名称/说明两字段。
- 分类85 dialogue、5 narrative、1 name、1 item_description；只覆盖休息后拜访族长、五碑机关与古代记录前半段。
- NPC现有康复阶段已在前批覆盖。高原挑战、传送材料与梅莉莎到访尚未到本批场景，不按section数字提前混入。

Verified / source/offline：五碑文按源顺序排列，分别保留2/2/2/2/3处功能换行，第四碑尾随4空格、印章名尾随1空格保持；机关触发逻辑未修改。
62条普通对白显式去硬换行。18、800、150三个阿拉伯数字按源保留，不改成长写或换算。
混血、卡蒙德成长与灾祸种均为幻想世界观中的古代记录或人物推测，疑问/据说/传闻语气保持，不升格为现实科学或已确定剧情结论。

阿维斯战争、塔斯、斯拉茨、恶魔、暗影、马雷族印章、斯特拉斯石碑新增7项candidate。
斯拉茨与斯特拉斯为不同韩文源名，各自保留候选，关系未核，不按近似拼写擅自合并或纠错。
鲁哈尔特内战、阿维斯贝尔克、卡尔塔大战、拉·斯特拉达等沿用共享候选，不标人工定稿。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/history-batch057/workspace
python build/batch-057-verification/verify_resources.py baseline
python build/batch-057-verification/verify_resources.py modified
python build/batch-057-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
新增92条两盘回填一致，旧7,103条保留，10,981条仍为源值；隔离回滚恢复7,103条，主产物保留7,195条。
干净index源码测试、152项依赖锁、164文件重建一致性与错误hash回滚拒绝分开验证，历史held及重复occurrence保持。
本批没有新增字幕，profile、35计划254cue、历史字幕来源与README逐字节冻结；11-50/60尚未到场景，不重复导出ISO。
第56批CI run39293350814四组均completed/success，保留实际jobs证据；当前提交云端状态单独核对。
仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字体/TOC/玩家入口；离线成功不代替游戏验收。
下一批从CSMB11_10起续读记录，再按场景接传送装置及同阶段NPC/任务/关联名称，不重复五碑文或前半段记录。
