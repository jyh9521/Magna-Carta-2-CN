# 第286阶段：18项缺值装备说明的已知文字回填裁决

## 结论与边界

建议将以下18条INT说明直接纳入新批次，忠实翻译已知文字；原值缺数值不等于文字含义未知。日文相同字段也缺数值，未发现任何可导入数值。此报告不补数字、不增加抗性行、不假设动态拼装已验证，也不表示游戏可达性或布局验收。主代理决定实际采用。

## 一手证据与完整语境

- `build/phase-286-item-research/extract.py` 从双盘原Coalesced提取7完整物品分区，`full-family-context.json` 保留219 INT + 219 JPN字段/盘的原值、源ID/hash和当前译文；两个盘对应源值逐条一致。源文件SHA256保留在该文件inputs数组。
- `Coalesced.kor` 每盘仅83字段，未含MC2Item；不能把不存在的韩文对照说成已复核。INT本身混合日文/韩文。
- 7分区为阿尔戈斧、克罗塞尔火球/拳套、露背包、塞蕾丝汀胸针、阿尔戈护手、朱特肩甲；合219字段，其中199已有草稿，18条本次建议，2条本次原值保留。
- `docs/PHASE_184_JUTO_ZEPHIE_EQUIPMENT.md`、`docs/PHASE_185_ARGO_CELESTIN_EQUIPMENT.md`、`docs/PHASE_186_RUE_CROCELL_EQUIPMENT.md`、`docs/PHASE_250_JUTO_ZEPHIE_ARGO_WEAPONS.md`、`docs/PHASE_251_CELESTIN_RUE_CROCELL_WEAPONS.md`及`locales/zh-Hans/consistency-reviews/armor-six-characters.json`明确历史保留原因是缺值/运行拼装未核，而非已知描述不可翻。历史观察不计作新增翻译。

## 术语与跨语差异

- 复用已有斧、火球、拳套、背包、胸针、护手、肩甲、攻击/精神/防御。407名称已为阿维斯拳套，125_sword_D已有“以阿维斯技术打造”，148_D的アビス族与NPC/邮件阿维斯族相符。349名称龙人护手保持，说明トレワ族仅译特雷瓦族，不宣称名称和族名同义。
- JPN `Default/North_mage` 北部軍錬換術師，与INT同名字段北部军연환술사、已有北部军连环术师直接对应，支持錬換術/術師沿用“连环术/连环术师”。完整JPN查询保存于`renkan-primary-crosswalk.json`；剧情台词日/韩分段不一致，不能把同ID当逐句翻译证据。
- 308_D“復活を阻む”按风味写阻止其复活，不当作已验证即死/禁复活机制；428_D保留“という”的据说；644_D雷の錬換術译雷属性连环术，不加数值效果。
- INT 308名无斧而JPN有斧，沿现有INT名称不改；INT句点与韩文.+、日文无句点之差按现有装备风味惯例译自然中文，不从JPN复制全角＋。

## 功能符号策略

18条均只有一个原样字面反斜杠n功能分隔和一个ASCII +；数字串均为空，继续为空。308_D的+后一个ASCII空格保留，其余17条+后无空格。未加入或移除统计行/TAB。译文不创造技能占位符/动态数值绑定。

## 逐ID/hash建议

### 308_ax_D
- ID: `coalesced:6bc43ca87553cea6cadd3f21584a89f5de7e68a15ddda0fc92aafeeb276e16b8`
- UTF-8源SHA256: `42a4fb6815387b97679dd53796348da8260346675fe915f37e6d8cb0b3c73065`
- 原文: `敵に致命傷を与え復活を阻む究極の도끼\n공격+ `
- 建议: `能给予敌人致命伤并阻止其复活的究极斧\n攻击+ `
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 308_ax_S
- ID: `coalesced:50be14d45b57f11e72df4e309976908c4e5b0c02c259678ed397b9eed03782e7`
- UTF-8源SHA256: `1541cb095ca6664e84762f6adc7755a58ac98767043024b3a07c8d5209af7f60`
- 原文: `도끼\n공격+`
- 建议: `斧\n攻击+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 428_fireball_D
- ID: `coalesced:3fa3c42dd25dc248a5c296348b89d2e980580e5b88d6d89f6de182c63fc80121`
- UTF-8源SHA256: `4edfe627e7996e48967a80e8e0445164f9a4823a17daff4a8e1c204c0a2ef3cf`
- 原文: `炎を自在に操った天才錬換術師が使ったという화염구.\n정신+`
- 建议: `据说曾由一位能自如操纵火焰的天才连环术师使用的火球\n精神+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 428_fireball_S
- ID: `coalesced:45b6832869646ba35fe07b2ddf9b881577fb74800031bd8ba0956a64850a10d0`
- UTF-8源SHA256: `43848c65d4377e6d2dec7c90f17bfd316f381a332ca94e976ca89c86c6fbd4ce`
- 原文: `화염구\n정신+`
- 建议: `火球\n精神+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 407_knuckle_D
- ID: `coalesced:353750a6cd4fd2b8e2798a7e2becaa2f6b19b19a3411a8c52dd3acd9edc37533`
- UTF-8源SHA256: `3c09ca0b83c60fae00de71120e13a5d3e424ef1ee6dfbd472a279d34696e08aa`
- 原文: `아비스의 기술로 만든 정교한 너클.\n공격+`
- 建议: `以阿维斯技术制成的精巧拳套\n攻击+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 407_knuckle_S
- ID: `coalesced:a9c6a80fff879613ea3fea1785ccbb6e16fd1fc45275baac3f53fb45b85c58fc`
- UTF-8源SHA256: `80dd0b7c0b2e8797bb3ea559898381f9b5cbd3315778d7e92758309e58b08f7c`
- 原文: `너클\n공격+`
- 建议: `拳套\n攻击+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 644_backpak_D
- ID: `coalesced:eeed08543c5b7642ded59a82485dc108ca7095d74c46fc12f5237c418f339268`
- UTF-8源SHA256: `ce958b4c2bf72c9562bc1f98f60312f6ca6afe1199e981d20de890478a6127dd`
- 原文: `雷の錬換術を補助する便利な배낭\n방어+`
- 建议: `能辅助雷属性连环术的便利背包\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 644_backpak_S
- ID: `coalesced:4a4ce071324eec9f82afaa47fbae51b81eb65bec77151e86dd5eb3aa6a452236`
- UTF-8源SHA256: `831794cac54ff48dd282b7926492b8525baca398182903e59f61be9c2dd6bd7b`
- 原文: `배낭\n방어+`
- 建议: `背包\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 646_backpak_D
- ID: `coalesced:2fefb5c30e8d06cd343458de739b96ed072a71a2d9648dc2ce321537acdfbb8f`
- UTF-8源SHA256: `674934f23fd7b714c191a1565a6ad2ae7e30e946090b283b7706478038674007`
- 原文: `使用者以外は絶対に開けられない배낭.\n방어+`
- 建议: `除使用者以外任何人都绝对打不开的背包\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 646_backpak_S
- ID: `coalesced:2e170407cef919c03cdd1c952f047de9d1941c037e7bd794c4360c10109fb7e9`
- UTF-8源SHA256: `831794cac54ff48dd282b7926492b8525baca398182903e59f61be9c2dd6bd7b`
- 原文: `배낭\n방어+`
- 建议: `背包\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 547_brooch_D
- ID: `coalesced:a3f573d75cf287324dbf6f59f3bb7ffd8d92b1e06603bf95419c9ff87c19b275`
- UTF-8源SHA256: `5fcf449e1af011701c1868d303970bec2e75fbc8859922587b65a0041990e73a`
- 原文: `希望を象徴する文様が刻まれた브로치.\n방어+`
- 建议: `刻有象征希望纹样的胸针\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 547_brooch_S
- ID: `coalesced:d42679fc3a33ee59a9300dead30ec2f2a2439aade30199b63059cf1b8bf51eb0`
- UTF-8源SHA256: `8663907c67747e41bcc690c2e45ac226a59e8753427af5a346812cd3531a703e`
- 原文: `브로치\n방어+`
- 建议: `胸针\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 349_guantlet_D
- ID: `coalesced:33628fb00022f73f22eefba60fd10022df94f42ca553e5d3b4b8f7fd7322656f`
- UTF-8源SHA256: `5c5b697d4757277281a8d8ab9e3ee818a253d5f660bb372ef2c9e302bb00055a`
- 原文: `トレワ族の戦士が愛用した伝説の건틀렛.\n방어+`
- 建议: `特雷瓦族战士爱用的传奇护手\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 349_guantlet_S
- ID: `coalesced:fb92f81f0fca945f69dbf8031f641862dd8847cc19328d464888af2aab889711`
- UTF-8源SHA256: `00267a072af9152824b5db23a29b3008900a3a97fc29f55e06927c914db7ffe8`
- 原文: `건틀렛\n방어+`
- 建议: `护手\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 148_pauldron_D
- ID: `coalesced:0b2fed137ee42a23db64a2b1436bc55f5954941d3f24b2144611bfcade44ead0`
- UTF-8源SHA256: `f94b92002325ce2bb3728ecefac58e53e0ed2c45f20dc63955b5bd55289b4565`
- 原文: `アビス族により作られた高級材質の견갑\n방어+`
- 建议: `阿维斯族以高级材质制成的肩甲\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 148_pauldron_S
- ID: `coalesced:c3e87c38d0e08b359639f6eb3c3dc3231d04aba62d3d7f1d2b5e404eb95cf19e`
- UTF-8源SHA256: `f231f0e77789c6c7d80934b9d1d39b976637a865d7738a7716239edc5985a648`
- 原文: `견갑\n방어+`
- 建议: `肩甲\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 151_pauldron_D
- ID: `coalesced:1a27de65f91a9ba1858c84a4122639c508bdbb0f42fcb92d4567bac01fb688a7`
- UTF-8源SHA256: `f7421b52a340fd2375fcfa5ca0ca4fd58737cad5306b8553ac9aacc331c87287`
- 原文: `모든 공격에 대해 최강의 방어력을 자랑하는 견갑.\n방어+`
- 建议: `面对一切攻击都拥有最强防御力的肩甲\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

### 151_pauldron_S
- ID: `coalesced:5fed2bcefe11b408d60af066be447e6158f9554c0feb4dbc89f9471957b849cc`
- UTF-8源SHA256: `f231f0e77789c6c7d80934b9d1d39b976637a865d7738a7716239edc5985a648`
- 原文: `견갑\n방어+`
- 建议: `肩甲\n防御+`
- 等级: 源值/双盘一致/缺数值为Verified；语义翻译为High-confidence deduction；运行拼装/布局为Unverified。

## 明确保留且不计新译

- `424_fireball` 原值“毒炎球”已经可直接中文阅读，未改即不计新增翻译。
- `424_fireball_S` 原值空字符串，不填词、不补数值、不计新增翻译。
- 606_katana_S不在本次7分区范围；历史原值“刀”加功能换行已经中文可读，不计新增翻译。

## 生成建议与验证边界

候选计划为`build/phase-286-item-research/MODIFIED_FILE.json`，只作主代理回填输入，不改现有计划、审阅锁、字体、玩家包或暂存区。完整回填/双盘重建/字体检查/隔离回滚/增量刷新及推送由主代理统一完成。
