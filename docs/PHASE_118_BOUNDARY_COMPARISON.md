# 第118阶段：跨源边界核对与统一补零假设反证

2026-10-20，接续117阶段。INT14,082 draft/1104 candidate/44字幕315cue保持，translation-workflow最后批次仍116；本阶段不制造猜测译文。

## Verified：八源与payload身份

使用extraction-profile现有八份源，逐文件完整SHA256核对并parse/serialize逐字节往返；不新提取整盘。两盘INT/MC2Game.int和JPN/MC2Game.jpn的去终止符宽payload均390字节，hash e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7；11候选相对偏移均28/59/92/143/146/165/194/235/264/269/288。INT内容头895017，JPN801126；同payload不合并盘别/locale或断言同运行对象。两份INI与两份KOR零候选，不能由零命中推断其他格式完全正常。
JPN并非这三条异常INT值的可用修复原稿；按locale同key机械对齐仍不成立。以上为仓库工具静态字节证据，不是native运行引用/引擎解析验收。

## 尺寸反证而非修复

统一把每个0D 0A 00候选变成四字节宽CRLF的假设，每处新增一字节，总长度390+11=401奇数，不能直接构成完整UTF16载荷。新增documents[].naive_nul_insertion只给inserted_bytes/candidate_payload_bytes/even_utf16_byte_length/policy，不生成修复数据。偶数反例仍不证明字符或INI语义正确，模式也可能来自合法U+0A0D。
另作本地只读假设比较：原UTF16LE产生三个物理行值；整体UTF16BE可解码但得到四个带乱码前缀的键、section均空，不能当端序修复。源生成器/漏字节/运行读取方式仍未证实。所有原ID/section/key/值/hash和24分类保持，不调用导入器修复。

## 可复现与合同

```powershell
python -m tools.audit_wide_line_boundaries --source build/disc1-selected/MC2Game/Localization/Coalesced.int --expected-sha256 179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c --output build/phase-118-verification/new-audit.json
python -m unittest discover -s tests -p test_wide_line_boundary_audit.py -q
python -m unittest discover -s tests -q
```

JSON schema1新增可选诊断字段；旧字段和值保持，CLI成功字面输出不变。三项新合成测试覆盖奇数反证、偶数不授权修复及只添加元数据、不输出替代原文。hash拒写/既有输出保持/不修复等旧合同继续通过。
基线1460测试，修改及索引导出干净源码1463测试均OK(skipped=1)。旧CLI/新增CLI分别在同源输入运行，删除新增JSON字段后结果完全相等；独立副本回滚恢复旧CLI并重跑得到原JSON，主MODIFIED_FILE.py保留修改。可执行ROLLBACK.sh、错误hash拒写和四证据MODIFIED_FILE.py/DIFF_FILE.json/VERIFICATION.txt/ROLLBACK.sh位于build/phase-118-verification，记录精确命令/输入/字面输出/退出状态。
八源hash、双盘审计相同、24分类逐ID/hash核对；翻译工作区164文件与116逐字节相同，全部18176值/14082译文及历史held保持；workflow/terms/subtitle-profile不变。仅清理绝对路径核实的隔离干净源码可再生成pyc，保留原盘/配置/存档/runs/当前包/依赖/基线回滚研究。无新ISO/整盘副本/模拟器/字库/TOC/入口刷新；离线非游戏验收。

## 接续边界

117阶段原名扫描仅覆盖selected中不大于32MiB的文件，只有两份INT容器自出现；未解析压缩/未选中/较大包，不能证明孤立笑声无运行引用。此阶段没有新增运行证据，不继续重复计数或试写补零。验证清理推送远端核对后转入现有draft/held关联上下文及候选术语一致性审校；保留未知格式，未有证据不升级人工定稿或声称全游戏完成。
