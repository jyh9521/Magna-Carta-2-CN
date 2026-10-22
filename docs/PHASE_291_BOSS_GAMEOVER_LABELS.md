# Phase 291 — BOSS 与战败提示图片文字裁决

## 原始证据与复查边界

**Verified（原始资源离线）**：本轮实际读取 hash 锁定的 `UI_Title.xxx`、`UI_Title_Jpn.xxx`、`UI_GameOver.xxx`，恢复包、解析每个目标 Texture2D，并实际解码32个目标导出。每张新解码 PNG 与既存原始预览按 SHA256 精确相等，15对BOSS的RGBA分别相同。逐图原尺寸并排目视，而非用English对象名推断角色身份。主任务另行核验双盘全部别名；本文不把两个standalone包误称为全部消费者。未启动游戏，未修改任何原图片/工具/locale。

复查命令：`python build/phase-291-label-mapping/map.py`。退出0，字面输出：

```text
{"boss_images": 15, "gameover_images": 2, "total_images": 17, "held": 0}
PASS 32 original exports decoded and PNG hashes matched; both BOSS aliases pixel-equal; stable source hashes and adopted batch evidence matched; all input hashes unchanged; no game launch
```

完整[结构化映射](../build/phase-291-label-mapping/mapping.json)、[复查脚本](../build/phase-291-label-mapping/map.py)、[输入锁](../build/phase-291-label-mapping/input-lock.json)、[实际日志](../build/phase-291-label-mapping/verification.log)保留每个export对象、尺寸、payload/RGBA/PNG hash，原始INT稳定ID/source SHA256、累计已采用译文、采用该译文的真实批次文件hash，以及同embedded_path/section/key的JPN一手对照。证据包在忽略的build目录，原图不提交Git。

| 原包 | 原SHA256 |
|---|---|
| `UI_Title` | `b6826e68b5b6fc6401a4f0e2b738f8abbcff0897ddce234b3e0669336d2706b4` |
| `UI_Title_Jpn` | `f9c1648d7a76cee8766140d3533d938fd7ef51a7eed06d37b291c7b1ec997595` |
| `UI_GameOver` | `292da40a53ee2f9e3ebab0d4fe56d01d97a2bcefdae7d391c8bbe63bf0ac35af` |

原INT SHA256：`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。累计计划SHA256：`c65a193ffdc25f997fba59b142681b5560c410574f4c4258b0dc900ded1c2f9c`。同字段JPN仅作跨语言身份核对，不用JPN的不同字形无证据推翻已采用中文。

## 完整17图

| 包 / export | 目视主字 | 目视英文小注 | 采用中文 | 依据 |
|---|---|---|---|---|
| UI_Title / UI_Title_Jpn 10 | エルガ | Elga | **艾尔加** | batch-004.json |
| UI_Title / UI_Title_Jpn 11 | ガーディアンアモン | Guardian Amon | **守护者阿蒙** | batch-110.json |
| UI_Title / UI_Title_Jpn 12 | アスタロス | Astaroth | **阿斯塔罗斯** | batch-119.json |
| UI_Title / UI_Title_Jpn 13 | レヴィアタン | Leviathan | **利维坦** | batch-024.json |
| UI_Title / UI_Title_Jpn 14 | メリッサ・ティス | Melissa Tiss | **梅莉莎·蒂丝** | display-fix.json, opening-batch.json, readability-fix.json, readability-revised.json |
| UI_Title / UI_Title_Jpn 15 | シュエンザイト・バーレン | Schauenzeit Baren | **修恩扎伊特·巴伦** | batch-004.json |
| UI_Title / UI_Title_Jpn 16 | 베카스 | 无 | **贝卡斯** | batch-024.json |
| UI_Title / UI_Title_Jpn 17 | ベリアル | Belial | **贝里艾尔** | batch-119.json |
| UI_Title / UI_Title_Jpn 18 | 제바사 | 无 | **杰巴萨** | batch-030.json |
| UI_Title / UI_Title_Jpn 19 | クレア・セティアン | Clare Setian | **克蕾尔·塞蒂安** | batch-009.json |
| UI_Title / UI_Title_Jpn 20 | ギガンティックアングラー | Gigantic Angler | **巨型安格勒** | 原图直译 / 新音译 |
| UI_Title / UI_Title_Jpn 21 | ヒュアレン・ジャース | Huaren Jass | **修亚伦·贾斯** | batch-009.json |
| UI_Title / UI_Title_Jpn 22 | ルタン・ロイド | Rootan Roid | **鲁坦·罗伊德** | batch-012.json |
| UI_Title / UI_Title_Jpn 23 | 시온 레그럴 | 无 | **希昂·雷格拉尔** | batch-112.json |
| UI_Title / UI_Title_Jpn 24 | 攻略目標：嘆きの門 | Wailing Gate | **攻略目标：恸哭之门** | batch-110.json |
| UI_GameOver 3 | Game Over | 无 | **游戏结束** | 原图直译 / 新音译 |
| UI_GameOver 6 | Press [A button image] Button | 无 | **按 A 键** | 原图直译 / 新音译 |

## 已采用正字与新译范围

7张图只复用已采用名字正字（10/12/13/16/17/18/23）。12从已采用恢复句抽取阿斯塔罗斯，18从击败目标抽取杰巴萨，不能把恢复了/击败写进图片名字。其他8张BOSS存在可见全名、前缀或未收录完整名，属于真实新图片翻译，而非声称累计INT已经采用完整全名。

| export | 裁决说明 |
|---|---|
| 11 | Guardian reuses 守护者; アモン / Amon adds 阿蒙. No existing adopted Amon complete field. |
| 12 | Extract 阿斯塔罗斯 from adopted recovery clause; do not retain 恢复了. |
| 14 | Short name 梅莉莎 is adopted; visual surname ティス / Tiss newly transliterated 蒂丝. |
| 15 | Short name 修恩扎伊特 is adopted; visual surname バーレン / Baren newly transliterated 巴伦. |
| 17 | JPN same-field ベリアル validates image Belial against Korean 베리엘; preserve already adopted 贝里艾尔, not a new conventional demon-name spelling. |
| 19 | Short name 克蕾尔 is adopted; visual surname セティアン / Setian newly transliterated 塞蒂安. |
| 20 | ギガンティック / Gigantic means 巨型; アングラー / Angler transliterates 安格勒. No claim about creature species or invented identity. |
| 21 | Short name 修亚伦 is adopted; visual surname ジャース / Jass newly transliterated 贾斯. |
| 22 | Short name 鲁坦 is adopted; visual surname ロイド / Roid newly transliterated 罗伊德; image sublabel Rootan differs from adopted INT key Rutan, not evidence to change 鲁坦. |
| 24 | 攻略目标 is direct translation of visible 攻略目標; 恸哭之门 reuses adopted phrase. Do not erase 攻略目標 prefix. |

### 稳定ID与source hash

- export10：`coalesced:1b0de89908471eea1002b1fda2add9e70c16a803e4475f1821fd30549f4eae6f`，source SHA256 `b3e1c36d36cbb39eebcf0e1906d5f11a1b8846b7040cd11b85633b256aba8c7f`，`Default` / `Elga`：엘가 → 艾尔加。
  - 原JPN同字段：エルガー；source SHA256 `a8741a418ae60b0d1e3dc450e88287397af7802e4a7364b2430ffb437fac46ea`。
- export11：`coalesced:1d0d61693623741e1d0ab34111b6d0990bf555b92380a359c75b4e4442428a56`，source SHA256 `5c540350ab635c3680fb5f59c5c663451ae95af91a36f31c837b8eb68f91c9ea`，`Chapter01` / `Chapter01_28`：동굴에 있던 가디언의 사체는 회수했습니다.\n군선이 도착하는 대로 아바젯으로\n이송할 예정입니다. → 洞窟里的守护者尸体已经回收了。\n军船一到，就会运往\n阿巴泽特。。
  - 原JPN同字段：ガーディアンの残骸は回収した。\n本部から船が到着したらすぐに\nアバジェットに移送する。；source SHA256 `bbc7e6dff7c796805cc12c62fe97d4a6f93f2ee4ed6e653463996d9ec5077abc`。
- export12：`coalesced:e66f42d564e6a6a8fe73e7f141686d8075a859fa8b3c25688b867779819e5706`，source SHA256 `fbc45ca87f723b034295d449192a90022169e436d3139cd1f740fc1aacd60319`，`Battle_Log` / `AstarotRecover_1`：아스타로스가 → 阿斯塔罗斯恢复了。
  - 原JPN同字段：アスタロスがＨＰを；source SHA256 `ad8012d194ace5f97694e4af7e1267f4c3c383cb8da4a98c33b4e2659f79c682`。
- export13：`coalesced:13602819568bcd4ca21f522191956af518ca6def66febf2f15188a9575fd3bd5`，source SHA256 `76219d4e59ab0dc3a81783a3b8fe1df750a23499cb70e5bbde236528767eeecc`，`B04_002` / `B04_002_Sub`：레비아탄 → 利维坦。
  - 原JPN同字段：レビアタンについて；source SHA256 `420c02ef48045f7969f84325713d07fd2f57b3869c36f29a647ae12522c6e9e3`。
- export14：`coalesced:7454c5c8449ba9d96de45d682d2d3894234d6fbd690cea1380259ee1dfe60a9a`，source SHA256 `5bceec993838f179eba8d049b9617b2f2efd3f26980dc867a03728bea7afa6e5`，`Default` / `Melissa`：멜리사 → 梅莉莎。
  - 原JPN同字段：メリッサ；source SHA256 `1730cd19a396010846c8f2b9332f4da96610cbe9990f0f423f18a79b97b72525`。
- export15：`coalesced:cb193c45203708ee5f3dbb876dd54e26bbbcbc10809bcb027e36980e4425e2e0`，source SHA256 `6b31a46aa1b4a861efbc15a143494c9817e21cf856adc8da8b0397cef7e55f67`，`Default` / `Schauenzeit`：슈엔자이트 → 修恩扎伊特。
  - 原JPN同字段：シュエンザイト；source SHA256 `ac07b655a0b386d4827b4805f5cd370480f270563ed587abf8e7508f2cdfebb7`。
- export16：`coalesced:1139969c1b4b55f2b947cedcf3b057d621cb6385630991423eb44eefddc70ceb`，source SHA256 `36144fdc90c24171218f1ebd265048509f30a1096267f19aa44faa5d2ea8bb5a`，`B04_001` / `B04_001_Sub`：베카스 → 贝卡斯。
  - 原JPN同字段：ベカスについて；source SHA256 `eb8c6e3c5e10abd561f647d611c31f2d28de9a1a39213fdef13ab9a41c77ed18`。
- export17：`coalesced:532aa3295bef1540db9ff69a4934b04af6f1926cdbd49392c94fa6c980453b26`，source SHA256 `d92730809da15a11743e598d12157eb1e333886aa9f2228fe407cec8adcb9738`，`Battle_Log` / `BelielRecover_1`：베리엘이 → 贝里艾尔恢复了。
  - 原JPN同字段：ベリアルがＨＰを；source SHA256 `bd1347b90e6b2f6143bb8e33badc4fe308704c96f06a2c948d6dcef05dd62eb1`。
- export18：`coalesced:4625d8114843d3ee54d01a9e326f9162f63416b53994ee57d4836312a699a63f`，source SHA256 `4fab9f8b6fcaf1a12ea37ed11cc121e0e14b6f3e54f6f48928ca491a2a64fbfb`，`05_136_0` / `goaldesc`：제바사 처치 → 击败杰巴萨。
- export19：`coalesced:5afcb5c9e296971e253b232e5e0a5eecf830d51ada15c9072ea4c39f72e080c6`，source SHA256 `c1308fcb43ef6eedc017a1d46e4f8ab081402ce51157440b08242f4f2198299c`，`Default` / `Clare`：클레어 → 克蕾尔。
  - 原JPN同字段：クレア；source SHA256 `468e0701947f5619195cc2fdc4824ae454cabb859bc505d67b488f9662b7c3f8`。
- export21：`coalesced:e78332d97bb940187fed4ebd3053d2e816e0a912ed299d8f61151c553c95ad79`，source SHA256 `9d69f26f7676b68ef47bbc153ae708ce5b9a612da85b6523455e033fe92e025f`，`Default` / `Huaren`：휴아렌 → 修亚伦。
  - 原JPN同字段：ヒュアレン；source SHA256 `e69e97719f51ff06a78bbb19cb5b1273b0201c7253605a5d0734d7c6d6cf5072`。
- export22：`coalesced:325ca9b1ce65009c134ae6b749972c9df795304ac673b07c59a7b78ae94da7ff`，source SHA256 `0df037a143a403842dba76318d002a9226d79dcc66f0ec023467aab01c75f122`，`Default` / `Rutan`：루탄 → 鲁坦。
  - 原JPN同字段：ルタン；source SHA256 `e18438eed558724bd2e44d368864a04118bd56535907ddd8fe44267584dd890a`。
- export23：`coalesced:808f9378d023ec66c698c20e97492fb57dc0c5567493179dfabeafc722171111`，source SHA256 `fc3511c5ada3eb3c83487822d98582e61666ecef0524341106f8dee924060dfb`，`B02_004` / `B02_004_Sub`：시온 레그럴 → 希昂·雷格拉尔。
  - 原JPN同字段：シオン・レグラルについて；source SHA256 `4f2e7e2b8da6fd5bc78b0f296a4995e96e601491689e112886c5e029e4eb9949`。
- export24：`coalesced:ab212b81136afafa85408135bcc9c13393e477cbccf4836c66a6f19e383bb14b`，source SHA256 `76c7b76b4b7e47a5f50d985d0dfd031bd82b26ffcb97b746df0e4062156c2c7d`，`Chapter02` / `Chapter02_08`：통곡의 문을 반드시 격파해주십시오. → 请务必攻破恸哭之门。。
  - 原JPN同字段：「嘆きの門」を\n必ず突破してください。；source SHA256 `304bf3fd8f247e77893730f4da7e9f9217e424e2ee2bf80d44ee9a362f35018b`。

## GameOver按钮原块保留

原`Notice_tex`为256×64。目视为`Press` + 绿色圆形A按钮 + `Button`。实际解码绿色像素bbox为`[112,18,138,43]`（xyxy，右下排除）；建议保护更大的4×4对齐块矩形`[108,12,36,36]`（xywh，覆盖到x144/y48），保留圆形按钮、A字与边缘阴影的原BC3块，**不得用字体重画A或整张重新压缩**。两段文字可分别在`[40,12,68,40]`与`[144,12,80,40]`替换为“按”与“键”，组成“按 A 键”。原RGBA非零alpha bbox为`[42,15,223,46]`。主任务应验证保护块逐字节相等、修改块只落在左右文字矩形，并查看真实BC3解码候选图；此处只是原始坐标调查，不冒充已打补丁。

`GameOver_Tex`目视明确为`Game Over`，译为“游戏结束”。不把名字推导为额外菜单/继续功能；实际继续动作由玩家验收。

## 覆盖与验收限制

本调查一次完成15个BOSS + 2个战败文字图的译法；未据此声称游戏其他图片文字清零。新音译明确来自目视日文主字及同图英文小注，已采用短名来自hash锁定真实INT数据，未查无关外部百科。补丁发布仍须主任务的完整别名写入、字段/包结构/字体保留、双盘构建、隔离回滚、hash保护现有测试目录刷新、远端核对，以及最终实际游戏显示验收。
