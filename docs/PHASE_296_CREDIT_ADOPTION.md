# 第296阶段：完整片尾职务与配音角色图实际回填

## 已采用范围 / Verified

13张UI_Credit图、112条完整职务/角色/部门短语、113个物理渲染层、26双盘别名实际进入正式计划。累计520图片组、960层、2122别名；源并集277，纹理组件177/234，对照资源202/261。INT14159/batch121、七Font与315字幕保持。职务含Produced by/Developed by及All QA staff，不因它们位于署名图片就一概漏译；公司、个人、版权原图/行保留。

4145原包逻辑header重新匹配原锁，双盘UI_Credit原资源完整重hash；13个源身份各有两盘实际别名，无源hash冲突。不是本轮重新完整hash全部4145游戏包。源图、payload、tiled、RGBA和GUID/namespace逐项绑定，真实preview由编码后的BC1解码，不是仅保存绘制图。

## 名称和署名

英文角色列使用当前已采用的中文名：修恩扎伊特、修亚伦、克蕾尔、凯汀等，不另造音译。terms.source_string_id可能指整段对白，不能把整段目标误贴到姓名位置；只取已采用且在该语境中存在的词名，保留source ID/hash与完整语境证据。职务Account Manager译客户经理，不误成财务经理。所有右列员工、公司、笔名、图标、上部品牌Logo、70底部版权、完整71法律图原字节受保护；两家公司标题保留，只译其职务说明。

## 跨页完整短语

原61末行/62首行共同组成Battle and Balance Designer。serialized Scene.EndingCredit.CreditTextures明确按60..71排列，两个WidgetCredit及1024px纹理范围均保留。引入通用显式render_window：在有界336×32画布渲染完整战斗与平衡策划，再分别取20/12像素高窗口写入既有两个物理区域，不把整句重复写两遍，不清掉半句后留空。源图连续性与序列声明已验证；真实滚动间距/时序仍未游戏验收。

默认无窗口路径保持；canvas/crop形状、整数/范围和输出矩形严格检查，实际完整canvas面积纳入16Mi像素预算，不按小crop绕过。允许完整画布有墨迹而某个显式窗口为空，用于真正跨边界的空白尾部；缺字、完整文字过大、无墨迹、重叠、块/保护区及全部旧边界仍拒绝。

## BC1颜色与alpha证据

明确采用opaque-rgb，即授权矩形内RGBA按黑色底混合RGB并写成不透明BC1，绝非109的灰度mask转换。Source59黑底RGBA为(0,0,0,255)，BG的UITexture186指向59；191/192分别绑定Softmax73/NBGI72。五页60/61/65/72/73的DDS解码alpha确有0，不宣称全源不透明；背景主色为不透明黑，透明解码样本RGB均黑，原文字区也有这种样本。新模式明确重绘授权文字区域的alpha，所有区域外原始BC块、原alpha和保护crop保持；不声称复现游戏shader的所有alpha选择。旧opaque-luma仍拒绝混合alpha来源，不能静默放宽109的mask契约。

初版把新RGB模式也套全源alpha255守卫，实际源图审计使其失败；保留本地失败与逐区域alpha审计，随后明确RGB黑底作者模式，未对未知格式自动fallback。作者/员工白字检查排除待翻译caption自身的暖白字芯，否则Producer高亮会被误判成员工姓名；源caption外样本逐像素保持，姓名/公司还独立受块及crop双重保护。

## 构建与验收边界

沿用tools.build_texture_overlay、compose_locale_resources、build_locale_comparison，首次写全新输出目录，复核使用verify-root；只显式纳入一个UI_Credit原资源并hash保护刷新既有测试目录，不制作ISO或完整游戏副本。保留原件、配置、存档、runs和全部活动依赖。基线/隔离旧源码1932测试，修改/清洁源码1952测试及277资源检查点回滚以本轮VERIFICATION.txt实际结果为准。

没有启动游戏；完整滚动、视觉混合/UV和流程由用户验收。原盘实际各有51个Tutorial_和191个UI_资源，旧789导出只覆盖12个源包，并非全部UI。后续扩为全部484个双盘UI/Tutorial资源的hash/纹理清点及逐图判断，并重新核查教程截图/背景内真实烘焙语言、原生未知UI和성쇄新一手证据，而非把素材类别直接当作无字证明。片尾13图完成不是全游戏完成。

## Derived-output storage preservation

To keep sufficient working space without deleting prior evidence, 3,348 byte-identical generated comparison candidate/raw-control files from phases 289 through 295 now share NTFS hardlinks with the same phase and disc composition candidate/control files. Every original pathname and SHA-256 remains intact. Original game inputs, texture bundles, rollback snapshots, configuration, saves, runs and the live test tree were not deduplicated. These derived outputs are immutable: materialize an independent copy before any later write. The local `build/phase-296-verification/storage-cleanup{,-extra,-earlier}/pairs.json` records the exact allowlist and hashes; `materialize_storage.py` provides hash-guarded physical separation. An actual-resource isolated fixture verified separation with identical bytes; the current historical output sharing remains in place. This changes inode sharing, not localized data.

## Follow-on complete prefix census

The read-only follow-on census freshly hashed all 484 physical UI_/Tutorial_ resources (242 unique full-package hashes). It found 3,720 physical first-mip Texture2D exports, decoded 3,704, and retained 16 unresolved exports (eight UI_Battle_Master exports repeated on both discs) as errors rather than no-language evidence. This is not a census of all world packages, later mip levels or native text. A contact-sheet review of 376 textures in 13 additional UI families already identified further visible language; it is queued for actual source adoption after this credit cohort closes. No decoded count is treated as a localization completion percentage.
