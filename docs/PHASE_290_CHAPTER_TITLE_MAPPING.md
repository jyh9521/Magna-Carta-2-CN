# Phase 290: complete chapter-title image mapping

## Scope and status

**Verified offline source evidence:** all 47 `UI_Title` chapter-title texture exports 25–71 were read visually at native 512×64. Both `UI_Title` and `UI_Title_Jpn` were independently decoded from manifest-hash-locked original packages; all 47 paired RGBA images match. These Japanese-named packages still carry Korean chapter labels. Neither a package name nor an English object name supplies the translation.

**Result:** 40 exact existing field names (only Korean whitespace ignored), 4 exact adopted phrases extracted from sentences, and 3 explicit new image translations supported below. No item remains held. Existing INT data is unchanged. This is a mapping decision, not proof of any runtime loading, in-game clipping, whole-game image coverage, or successful resource reinsertion.

The full machine evidence is [`build/phase-290-title-mapping/mapping.json`](../build/phase-290-title-mapping/mapping.json). Each row includes original alias package hashes, export/object/payload identity, decoded RGBA and PNG hashes, native Korean transcription, complete stable ID, source UTF-8 hash, original context, cumulative translation, and every matching adopted batch with file SHA-256. The row references are the primary citations for the table below.

## Locked primary inputs

- Original INT: `179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`; path `build/disc1-selected/MC2Game/Localization/Coalesced.int`.
- Adopted cumulative plan: `c65a193ffdc25f997fba59b142681b5560c410574f4c4258b0dc900ded1c2f9c`; path `build/cumulative-locale-workspace/plans/179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c.json`. All source values are rehashed and must match that plan before evidence is accepted.
- Original JPN: `fb99602a9ff5f081857efa7389d6d2b6ecfc6765946f0bba2fbde4cdbf962a90`; path `build/disc1-selected/MC2Game/Localization/Coalesced.jpn`, additionally checked against `build/disc1-hashed.json`.
- `build/disc1-hashed.json` owns the original package identities. The script fails on mismatching original bytes, decoding failures, image dimensions, paired image inequality, missing stable IDs, unmatched source hashes, or unadopted batch translations.

## Full reviewed family

| Export | Korean image | Chinese image label | Basis | Adopted batch / stable ID |
|---:|---|---|---|---|
| 25 | 높새바람 섬 마을 | 风息岛村庄 | exact field | batch-094; `coalesced:aaf3de80a0c70992b2c57285f156b61f7ce6bd78897c4bfc3de91ccf1bf3836a` |
| 26 | 높새바람 섬 해안 | 风息岛海岸 | exact field | batch-094; `coalesced:4a5a9a64962137f9d2a5f7b76b4273f9b6397c36d2c5803fb3208d70b369c6f3` |
| 27 | 바람노래동굴 | 风歌洞窟 | exact field | batch-003; `coalesced:fdf5f49e10cb2687e5b6c02045d923dde80cc0161e30c872cdf1b75e71c0638d` |
| 28 | 청령의 숲 | 青灵森林 | exact field | batch-004; `coalesced:244da57d30ff22525d5b5d210a7974b873f3fc9eb7155f26c943f954d5c50e0d` |
| 29 | 아바젯 | 阿巴泽特 | exact field | batch-094; `coalesced:f37571138dae7b712ae568fd2866a0df01d062e3267d1b804d81cb133c213dd3` |
| 30 | 아바젯 항구 | 阿巴泽特港口 | exact field | batch-007; `coalesced:dbdf6af8ff5325063e0e6d98181714d742a1e12fd12c25f5f70fc1cbd70bcbcc` |
| 31 | 아바젯 초원 | 阿巴泽特草原 | exact field | batch-006; `coalesced:0e87be90037abb832eede0c13d78629f0bfa737a41a8a3c80cb0915d4fdb95a3` |
| 32 | 야생의 숲 | 荒野森林 | exact field | batch-094; `coalesced:eaca6292688b9dff523cdb52026b2f990fe3aade6bdde02e1f717a0e455bc784` |
| 33 | 원수의 언덕 | 元首之丘 | JPN primary verdict | batch-021; `coalesced:b215b6ee2f4801d107b6716e40b80fc63c4235071b1d17ebacda74da5c79432a` |
| 34 | 라티족 동굴 | 拉提族洞窟 | exact field | batch-005; `coalesced:8e7aab11669605cb2fa14790c800e77e7cdb7c39dc891d9b386b6795734f6a18` |
| 35 | 웨어울프의 아지트 | 狼人据点 | exact field | batch-005; `coalesced:dd58b4eebd457b0086c561ac1051841519fa2e7d3fb00775f00ac746d45c5c01` |
| 36 | 남부군 총 사령부 | 南部军总司令部 | sentence phrase | batch-021; `coalesced:c44ea22cee4e258ad8db0b7b4f8c26d76a09857d48b2c89bc8ebd8a651db4bfb` |
| 37 | 늙은 여우 협곡 | 老狐峡谷 | exact field | batch-005; `coalesced:220a6319bce74e8f0a8077a11231c815efa98011e9d9e35a798ef77c45d0e672` |
| 38 | 임시 주둔지 | 临时驻地 | exact field | batch-094; `coalesced:602abd4ea248ba6cbabda58ad4ff1174e6ae91308c5af54b8db579b4ab2fc9ae` |
| 39 | 침묵의 황야 | 寂静荒野 | exact field | batch-012; `coalesced:0ccaf985aff709fb9e1e2e3296496a6958c61e15066e4ed0f8ce9e4889637b56` |
| 40 | 통곡의 문 | 恸哭之门 | sentence phrase | batch-110; `coalesced:ab212b81136afafa85408135bcc9c13393e477cbccf4836c66a6f19e383bb14b` |
| 41 | 침묵의 황야 | 寂静荒野 | exact field | batch-012; `coalesced:0ccaf985aff709fb9e1e2e3296496a6958c61e15066e4ed0f8ce9e4889637b56` |
| 42 | 물빛저습지 | 水色湿地 | exact field | batch-009; `coalesced:72c267b54e3d3aee005a91a6e96185c742017f9fb51c155b4ff710c1b546f7ac` |
| 43 | 북부군의 야영지 | 北部军营地 | exact field | batch-094; `coalesced:221aea13930225c316e2a92854f169d578cb5e8d48f6f7ebadb569f1b54af130` |
| 44 | 임시 주둔지 | 临时驻地 | exact field | batch-094; `coalesced:602abd4ea248ba6cbabda58ad4ff1174e6ae91308c5af54b8db579b4ab2fc9ae` |
| 45 | 늙은 여우 협곡 : 북부군 기지 | 老狐峡谷 : 北部军基地 | exact field | batch-094; `coalesced:a470bbf14ed207841cb973135caa65e82631366eabcbf1db6055cb4eb8bc6a5b` |
| 46 | 어둠의 은신처 | 暗影藏身处 | exact field | batch-092; `coalesced:3762d79af2e616721a27af01c27d054fe217a1826f74b22f1fb4180ecac3a310` |
| 47 | 남부 관문 | 南部关卡 | sentence phrase | batch-022; `coalesced:128bda6385ac029e3d204366b1d0da0e07258388d59098c94e031f49d3fb848b` |
| 48 | 마레족의 제단 | 马雷族祭坛 | exact field | batch-094; `coalesced:f1f4317103249f8e17d12d8a70461bdc2849def393b6410adcdddabb651735e8` |
| 49 | 코타마레 | 柯塔马雷 | exact field | batch-007; `coalesced:acf63e073dcc0a556c8e48fba0b71782e571a8988907f007d07d0e4b5a36fd60` |
| 50 | 마레의 숨겨진 서고 | 马雷的隐藏书库 | new composition | batch-094; `coalesced:ec3c6621188800e009b8c5f61dd14339125cb2b6de251c153c1f91f52a87fe0a` |
| 51 | 마레 광장 | 马雷广场 | new composition | batch-094; `coalesced:f1f4317103249f8e17d12d8a70461bdc2849def393b6410adcdddabb651735e8` |
| 52 | 스트라스의 묘 | 斯特拉斯之墓 | exact field | batch-016; `coalesced:6a54911dda017cf09b9cf7d15e41e32711ab039f85f09255bd546aa42235a78d` |
| 53 | 해저 동굴 | 海底洞窟 | exact field | batch-011; `coalesced:d06f0b5a5a1f129206470eede236562027163c8a827bf6e76fa298b674674cd8` |
| 54 | 듀난 언덕 제1초소 | 杜南丘陵第1哨所 | exact field | batch-094; `coalesced:697a3dccb5efeb8efbbf3c107103f24f2058ef492650381e02cae4df5c0a0255` |
| 55 | 듀난 언덕 제2초소 | 杜南丘陵第2哨所 | exact field | batch-094; `coalesced:2d38dad539d47f627e0e53cd4870b232d4bcd0b5a99af04d8a24bf190cf288e9` |
| 56 | 검은 칼날 요새 | 黑刃要塞 | exact field | batch-018; `coalesced:5e963db4a6f762384aa79f9014d8df28c060fef384fed530e6f9f14ce9e186d8` |
| 57 | 듀난 언덕 | 杜南丘陵 | exact field | batch-009; `coalesced:c9cabd24f5d5a0dbaf5f55d02a674da8b64ebee6fc461dd512d6b51d8d2c9b9e` |
| 58 | 듀난 평원 휴게소 | 杜南平原休息站 | sentence phrase | batch-037; `coalesced:5a24f3db8077c1e69867edbb7fda1778529f1ba558323b1926396d41d05db060` |
| 59 | 고대의 무덤 | 古代墓穴 | exact field | batch-045; `coalesced:c907861266eb24213f41bf9ce12fd8bb6af35cf6e84bc27fd85625c2cb9352dc` |
| 60 | 듀난 평원 | 杜南平原 | exact field | batch-012; `coalesced:543ee75abb3c9fe5fd503a9872a7cfd4ee9782339a138277920d909f53383f1b` |
| 61 | 라노아라 호수 | 拉诺阿拉湖 | exact field | batch-035; `coalesced:b5937bf02a6fcecf079f101659e1700a0f00841f96280b05103125ed028609f5` |
| 62 | 듀난 도적의 아지트 | 杜南盗贼窝点 | exact field | batch-037; `coalesced:e3975c3a9283f2a89b97a39515cb1c92918b45827281f23f0727e3abe03fded9` |
| 63 | 레인폴트 폐허 | 雷恩波尔特废墟 | exact field | batch-035; `coalesced:86befcd0b2a0bfef46e6ec4ca8018956331a716e5863ab651ff7be8d31c6f47e` |
| 64 | 루할트 분지 | 鲁哈尔特盆地 | exact field | batch-031; `coalesced:5db82d47783ae27168627b7691fd151b0f0b49fe12f5c455f7affdd8a2daee72` |
| 65 | 벨포트 시가지 | 贝尔福特街区 | exact field | batch-094; `coalesced:f88d65d77d95dd3af7456a577974b044573f9da830d209d58272408e3ba27597` |
| 66 | 벨포트 왕성 | 贝尔福特王城 | exact field | batch-094; `coalesced:ea48e3b32a9cb391ac7fb3e30683dedfda79006f49ca09cf6fa035190882da69` |
| 67 | 벨포트 시가지 | 贝尔福特街区 | exact field | batch-094; `coalesced:f88d65d77d95dd3af7456a577974b044573f9da830d209d58272408e3ba27597` |
| 68 | 벨포트 남부군 점령지 | 贝尔福特南部军占领区 | exact field | batch-094; `coalesced:fcb2b15d9f4e52c6d2d5a2296e1822ede8b873d77c6d06ff11467a73646568e1` |
| 69 | 별빛 평원 | 星光平原 | exact field | batch-041; `coalesced:7dd0e1eed546f85a048ead3e4a629385159f1a81570a7efa25f7f890efe1843a` |
| 70 | 라 스트라다 | 拉·斯特拉达 | exact field | batch-003; `coalesced:78dc2621dfe750f12268d057759f3fe0034694dd83715654b626561a438cce90` |
| 71 | 루할트 고원 | 鲁哈尔特高原 | exact field | batch-033; `coalesced:6f424e7ff1f00963b201e3071df5029143e9dc0d6d10c28513c841315c7bd3cf` |

## Four sentence-phrase extractions

The Chinese label is an **exact substring** of each adopted translation, not a new paraphrase; the corresponding Korean phrase occurs in its original sentence (whitespace and the ordinary possessive particle are normalized only for this evidence check). The mapping JSON retains both full original and adopted sentence.

### Export 36: 南部军总司令部
- Source: `..\MC2Game\Localization\INT\MC2NpcTalk.int [Ch04_Abazet] 04_2241_00 #1`, `coalesced:c44ea22cee4e258ad8db0b7b4f8c26d76a09857d48b2c89bc8ebd8a651db4bfb`.
- Korean: 여긴 남부군 총사령부다.
- Already adopted Chinese: 这里是南部军总司令部。
- Source hash: `87eb9d774a8e273b54464efa9e3e7abc2a786f2dd5ee939ef64604307b6f10aa`.

### Export 40: 恸哭之门
- Source: `..\MC2Game\Localization\INT\MC2Compose.int [Chapter02] Chapter02_08 #1`, `coalesced:ab212b81136afafa85408135bcc9c13393e477cbccf4836c66a6f19e383bb14b`.
- Korean: 통곡의 문을 반드시 격파해주십시오.
- Already adopted Chinese: 请务必攻破恸哭之门。
- Source hash: `76c7b76b4b7e47a5f50d985d0dfd031bd82b26ffcb97b746df0e4062156c2c7d`.

### Export 47: 南部关卡
- Source: `..\MC2Game\Localization\INT\MC2NpcTalk.int [Ch04_Abazet] 04_2280_00 #1`, `coalesced:128bda6385ac029e3d204366b1d0da0e07258388d59098c94e031f49d3fb848b`.
- Korean: 이곳은 남부 관문입니다.
- Already adopted Chinese: 这里是南部关卡。
- Source hash: `620f9684737e049ef755b6e92f306f005e0de33ed3508a4bc29f10eeff2ce075`.

### Export 58: 杜南平原休息站
- Source: `..\MC2Game\Localization\INT\MC2Quest.int [06_605_0] DES #1`, `coalesced:5a24f3db8077c1e69867edbb7fda1778529f1ba558323b1926396d41d05db060`.
- Korean: 듀난 평원의 휴게소를 상습적으로 털어가는\n도적들을 물리쳐야 합니다.
- Already adopted Chinese: 打退反复洗劫杜南平原休息站的\n盗贼
- Source hash: `78ea784375a2da5882e853efb2dea0a74cb0010ef0ccca76f685c0be4a5a2aba`.

## Three explicit new image translations

### Export 33: 원수의 언덕 → 元首之丘

The Korean raster alone does not resolve the homophone 원수. The authoritative cross-locale **same quest context**, `MC2Quest.jpn [04_4222_0] 04_4222_yes_00` and `04_4222_in_00`, expressly names `沈黙の荒野の「元首の丘」`. The same section/key INT fields refer more generally to the werewolf remnants in the wilderness, so their already adopted Chinese lacks the hill name. Thus this is a new image-label translation based on an explicit first-party Japanese disambiguation, not a claim that an existing INT field already says 元首之丘. It is neither 元帅 nor 仇敌, and it does not rely on the English asset name.
- `..\MC2Game\Localization\JPN\MC2Quest.jpn [04_4222_0] 04_4222_yes_00 #1`, `coalesced:5542f0688f2b234d350eaf38cec869c37d9747a0aa50c7873bcdbc65b1e706a6`, source hash `d69f8e0c967e3d26abef0911d19a100d2004395c8967c67064c3027519dad613`: ウェアウルフの残党は\n沈黙の荒野の「元首の丘」に\n出没してるって。
- `..\MC2Game\Localization\JPN\MC2Quest.jpn [04_4222_0] 04_4222_in_00 #1`, `coalesced:c9c075e001065ddb62ee7b0e2a036b2ee0feab96e5f1ac7d6cda4530a39538d5`, source hash `d69f8e0c967e3d26abef0911d19a100d2004395c8967c67064c3027519dad613`: ウェアウルフの残党は\n沈黙の荒野の「元首の丘」に\n出没してるって。

### Export 50: 마레의 숨겨진 서고 → 马雷的隐藏书库

The raster expressly contains 숨겨진 (hidden); blindly copying `MC2FieldName [Ucave] Library` would drop it. Reuse the adopted `마레의 서고` → `马雷的书库` and the existing `숨겨진 문` → `隐藏的门` descriptor, retaining the Korean possessive and every semantic component. This produces a new image translation; it is not labelled an exact existing full INT name.

### Export 51: 마레 광장 → 马雷广场

Reuse the existing `마레족의 제단` → `马雷族祭坛` proper-name component and `MC2UI [Navigation] abazet_vil` `광장` → `广场`. The raster itself supplies the combination. Do not replace it with 柯塔马雷广场 just because another narrative names that longer place. The new composed label preserves the actual image wording.
- Export 50 component evidence: `..\MC2Game\Localization\INT\MC2FieldName.int [Ucave] Library #1`, `coalesced:ec3c6621188800e009b8c5f61dd14339125cb2b6de251c153c1f91f52a87fe0a`, source SHA `8e1907e4358abd10fe231d6dc27e09362d6a5f2058df40e68ba1613478e86a90`: 마레의 서고 → 马雷的书库.
- Export 50 component evidence: `..\MC2Game\Localization\INT\MC2CSMB.int [CSMB11_05] voc_csmb_1105_03 #1`, `coalesced:70873fc90fe4cfd8d7f3ac87a0ab6370e2a4edd70d7b8a88d8eb8f77f6db1e08`, source SHA `8ce7443a294d5d917d127ef2f6e7c5909f3aa77ec21bfe5ad9240c519d22e845`: 동굴 안에는 숨겨진 문이\n하나 더 있다네. → 洞窟里，还有一道隐藏的门。.
- Export 51 component evidence: `..\MC2Game\Localization\INT\MC2FieldName.int [Ucave] Altar #1`, `coalesced:f1f4317103249f8e17d12d8a70461bdc2849def393b6410adcdddabb651735e8`, source SHA `07d0993fa63eaf5d4f0c9a4303d5217f8083daf8acb47d85f60a4a1eddcfc4b5`: 마레족의 제단 → 马雷族祭坛.
- Export 51 component evidence: `..\MC2Game\Localization\INT\MC2UI.int [Navigation] abazet_vil #1`, `coalesced:ce1e07ce9d9fa2015995bf17548b53ae2a78b41c5ff68d295f4566dfcaf143b6`, source SHA `afbb411c2c9e3884febdd63a1d484029e69475e34255774caeac650b8cc42b46`: 광장 → 广场.

## Reproduction

Run from the repository root, with the retained original-resource and prior preview dependencies present:

```powershell
$env:PYTHONIOENCODING='utf-8'
python build/phase-290-title-mapping/map.py
```

Observed exit status: `0`. Literal result:

```text
{"total": 47, "exact_field": 40, "phrase_extraction": 4, "adopt_existing": 44, "new_image_translation": 3, "held": 0}
PASS original package decode and both alias PNG/RGBA equality; stable source hashes; cumulative adoption; matching batch hashes; all input bytes unchanged
```

The script reopens all locked inputs after the analysis. It writes only this phase’s ignored mapping evidence. Original packages, locale plans and translation batches remain unchanged. Source proprietary PNGs and packages are not included in this document or committed. The separate whole-disc alias inventory remains responsible for linking every cooked consumer; these 94 standalone exports alone do not prove that wider coverage.
