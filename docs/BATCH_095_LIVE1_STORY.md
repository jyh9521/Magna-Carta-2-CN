# 第九十五批：Live1完整剧情五场（201条）

日期：2026-10-20。新增INT201条，累计9,810条draft；453项共享candidate及GLOSSARY不变，另1项历史字幕来源记录保持。未人工定稿。按完整150–300条大批推进，五场合批后统一收尾。

## 范围与语境

- CSMB_Live1_001/002/003/004/005完整12/87/33/31/38条，全为实际对白，分别涉及早晨换羽、洁菲跌倒后性情变化、同伴商议、巡视演说与再次跌倒、恢复及末尾再变；不因Live命名归为调试样本。
- 201 dialogue，73条普通对白显式去硬换行，0功能字段、0新增held。源IDs/hash、数值/控制码/源值空白分别核验；无数字、键位或功能标记待改。
- 朱特/洁菲/阿维斯族/兰兹海姆/阿巴泽特/修恩扎伊特及连环术复用旧译。恢复术是普通会话简称，不追加具体技能、治疗数值或病理机制。
- 姐姐、洁菲小姐、公主殿下、愚民、女王按源的口吻转折保留，末段女王是同伴的说法，不改变角色身份。只有原文有朱特哥哥才补名字，不猜其他哥哥/姐姐的具体说话者或亲属关系。
- 同伴关于撞头/失忆/再次撞头恢复的疑问与猜测不升级成医学诊断，也不将怀疑本性变成确认；角色记忆和同伴隐瞒分别保留。不存在彻底康复的新增结局。
- 砍头、虫牢、滚锅、烤鸡是角色威吓而非已经发生；誓死保护大家是角色誓言，不是系统无伤保证。鲫鱼记忆笑话不补七秒等数值。
- 002_48纯省略号在明确同场停顿中译中文省略号，不增加动作/旁白；不据此解释仍未知的PartyTalk静默字段。001/004晴天跌倒呼应、005最后再次严厉口吻逐句保留，不补原因。
- NPC1443/1473、邮件128/235、44字幕315/315已提取cue、README、全部旧译/held/重复occurrence保持。双盘来源独立，不合盘，不表示全文或游戏内验收完成。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/live1-story-batch095/workspace
python build/batch-095-verification/verify_resources.py baseline
python build/batch-095-verification/verify_resources.py modified
python build/batch-095-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘原始INT SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
201条双盘回填一致，旧9609条保留，8366条其余原值未改；隔离回滚恢复9609，主文件保留9810。
基线1326、修改/干净index1332测试各skip1；237输入锁、164工作区文件重建一致、719份index导出复核；错误hash回滚拒绝且目标不变。
只清理绝对路径内核实可再生成、无入口依赖的干净源码测试pyc，保留原盘/配置/存档/runs/当前包/基线/回滚/研究证据。
不生成ISO/整盘副本，不启动模拟器，不刷新字库/TOC/入口；离线不代替游戏验收。提交推送后核对远端及工作区，CI按实际结果记录，再接下批。
