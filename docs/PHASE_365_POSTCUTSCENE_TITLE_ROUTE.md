# 阶段365：过场结束标题的实际消费者路线调查

## 状态与输入身份

本轮**找到了真实的剧情过场结束→大字标题显示路线**，但尚未确认它就是用户另行指出的“大章节名称”。这不是WorldMap动画调查，也不以入口地名的中文状态代替用户报告的验收。

调查起点为源码`b2473bc689993e0b854bf8addd0aed7c1a15fe00`；资源检查显式锁定阶段363的recipe：

- recipe SHA256：`38d60784f0179ebb6f1a94a8b8cec65ba9aef8aab6ee68af04ee308b5f610049`。
- 原盘双盘`MC2Game.xxx`：`13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641`。
- recipe当前`MC2Game.xxx`：`6a5d568d93a75083df6188dddc628a36e62d5c1c549055bba8567172a7c83bad`。
- 当前Engine：`67ad212cb85233b1c1524c11ac7ad6bbbf393c61fdfbb399430130fd0c07aef9`。

只读原盘和recipe实际指向的候选文件；未启动游戏、修改资源、运行GPU模型或复制完整游戏。研究脚本、逐成员／逐字段摘要及原生图保留于`build/phase-365-chapter-research/`。

## Verified：真实的结束事件与显示消费者

这次不是根据韩文Sequence文件夹名字猜用途，而是解析实际`OutputLinks[].Links[].LinkedOp/InputLinkIdx`：

```text
源CSMB：MC2SeqAct_FinishCSMB 的 Finished输出
  → SeqAct_ActivateRemoteEvent(EventName)
配套关卡：SeqEvent_RemoteEvent(相同EventName)
  → [实际序列化连线]
  → MC2SeqAct_OpenEntranceTitle.TitleTex
```

六个源结束信号已绑定源生产者和配套关卡消费者：

| EventName | 实际源CSMB包 | 标题字图当前译文 |
|---|---|---|
| `csmb00_10_end` | `ChinookIsland_CSMB00_10.xxx` | 风息岛村庄 |
| `CSMB04_01_end` | `Abazet_CSMB04_01.xxx` | 阿巴泽特草原 |
| `CSMB04_91_end` | `Dunan_CSMB04_91.xxx` | 杜南丘陵 |
| `CSMB03_80_End` | `Ucave_CSMB03_80.xxx` | 海底洞窟 |
| `CSMB02_50_End` | `Oldfox_csmb02_50.xxx` | 老狐峡谷 |
| `CSMB02_51_End` | `Oldfox_csmb02_51.xxx` | 老狐峡谷 |

五个配套关卡的连线解析均无错误。另见到`csmbQ06_10_end`消费者指向黑刃要塞；本轮六源生产者证明不把这一未闭合源信号计入。静态连线证明控制流合同，不声称观察过真实运行触发。

## Verified：HUD、字图参数与实际材质

独立的有界表达式读取器验证了两个完整HUD调用表达式及整个`SetRegionalTitle`函数：

```text
MC2HUDUI.NotifyShowRegionalTitle(Action)
  → EntranceTitle.SetRegionalTitle(Action.TitleTex)

MC2UIScene_EntranceTitle.SetRegionalTitle(a_Texture)
  → Title.Opacity = 0
  → TitleMatInst.SetTextureParameterValue('TitleTexture', a_Texture)
  → DoOpening()
```

`Action.TitleTex`和`a_Texture`均由真实声明绑定为Texture2D，不是字符串表键。`NotifyShowRegionalTitle_Direct(TitleTex)`的同族调用也已验证。

实际序列化显示对象为`UI_title.Global.Scene_EntranceTitle`：Title字段→`Bundle.Base.Title`的MC2UIImage→ImageComponent→UITexture_5→`UI_title.Global.Title_MatInst`→父材质`UI_title.Global.Title_Mat`。父材质的`MaterialExpressionTextureSampleParameter2D_0.ParameterName`确为`TitleTexture`，与脚本设置的参数完全一致。父材质默认字图也另行回读，当前像素与已独立验证的中文“风息岛村庄”完全一致。

尚未从静态序列化值证明原生初始化如何把运行时`TitleMatInst`字段缓存到此材质实例；不把同名参数和静态对象链冒充这一原生赋值过程或游戏渲染实测。

## Verified：所有实际行动字图别名当前均已中文

新的精确消费者查询复用旧包头身份，但查询不同的实际类；没有重做已关闭的SubTitle定格图／GetChapterStr语音键调查。

- 双盘4145个包成员、2551个唯一源／包头身份。
- `OpenEntranceTitle`共89实例：两份CDO及87个实际关卡行动；87行动均有非空TitleTex。
- 实际绑定覆盖36个完整纹理namespace／35个译文ID，包括`UI_Title_Jpn`及地图驻留forced exports；没有发现落在既有47图族之外的另名纹理。
- 87引用解析为66个物理别名成员：D1为29，D2为37。每个均读取原盘完整成员并核对源SHA、导出payload SHA、压缩／原始bulk及原始tile SHA，再读取recipe真正选择的当前文件。
- 用当前审核版的锁定字体、稀疏修复图及原生BC编码独立重放：**66/66当前tile逐字节相同，66/66原生alpha相同，保留原韩文字像素的别名为0**。
- 其中56个直接匹配审核版v9；另外10个属于五个已有RGB暗带修订标题，按v15记录的前置tile摘要重放后同样完全匹配。不是只比较包SHA或计划成员身份。
- 两张原生源／当前联系表覆盖全部36个namespace，逐行确认当前为中文；其余重复物理别名由完全相同的原生RGBA摘要验证。

独立重放使用：

| 输入 | SHA256 |
|---|---|
| `ui-labels-gameplay-v9.json` | `7b42c56dd392e65fdc419c2b53dfb8cd1f447f9f50ea5d4534fb4da3938e80e9` |
| `text-dark-bands-v15.json` | `60186820f5e54eacd34da8370e3e29c101484c514dbc56335bacc47250d53de5` |

历史`chapter-entry.json`采用旧NotoSans样式；拿它直接重放当前审核版Serif／修复背景会产生66项样式差异。该失败比较保留为`historical-phase290-plan-comparison.json`，**不是66项漏译**，也未据此回退当前字图。

## Verified：MC2Text线索的有界结果

原包中的MC2Text与MC2EventText只找到双盘各一份CDO，没有序列化TextList正文。TextList确为StrProperty元素的ArrayProperty，flags为`0x400001`；ChapterNum／SceneNum为可编辑IntProperty。这里没有找到可直接修订的章节名称表。此结论不排除原生动态构造、外部数据或反射访问。

## Verified：新增的volume／动态入口与文本消费者

实际脚本调用者还包括`MC2FieldLevelNameVolume.Touch`，它把自己的Texture2D `TitleTex`
传入`NotifyShowRegionalTitle_Direct`，不经过上述87个Kismet行动。
新的精确类查询找到154个实例（152个实际volume及两份CDO）；全部源／当前对象payload一致。
77个非空TitleTex引用覆盖37个物理别名、21个namespace／21个既有译文ID；其中8个
`UI_title`namespace未被行动路线使用（对应行动使用`UI_Title_Jpn`）。全部37别名再次按
锁定审核字体、修复图和RGB修订独立回放，**37/37当前原生tiles完全相同、原韩文像素别名0**。
另外逐行查看了两张volume原生源／当前联系表，当前21个namespace均显示中文。
没有落在47图族之外的另名字图。Touch的完整条件控制流／真实运行触发未被这一局部调用证明替代。

volume的另一个真实字段`FieldLevelName`是StrProperty，而不是字图。
152个实际字段对应34个`<Strings:MC2FieldName.section.key>`宏；按包／section／key唯一绑定
原始和当前主Coalesced值，当前34个值均无韩文。原始主Coalesced SHA256为
`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`，
recipe当前值为`b7bb76bc8b07dcf217511cdbbebe69be19a99025530ae1ff57223e1ca576eadd`。
属性ID、宏、表键及原先40项pending状态均未改动。
Touch将此字段传给`MC2DataManager.SetFieldLevelName`；该原生setter实际复制到存储字段的
C++实现未被解码，不把命名对应冒充原生数据流证明。

还找到了真实UI读取者：`MC2UIScene_Field.InitWidgets`读取
`MC2DataManager.FieldLevelName`到`strLoc`，然后五个完整、有类型声明的
`UILabel.SetDataStoreBinding(strLoc, ...)`表达式分别绑定MyLocation和四份MyLocationShadow。
实际序列化场景为`UI_Field_Core.FieldMenu`。因此该文字支线归属**场地菜单的位置标题及阴影**，
并非已确认的另一个过场大章节卡。WorldInfo外层上下文的网络属性metadata仍有解析边界，
当前证明分别保留完整callee／UILabel表达式与已验证的存储字段引用，不宣称完整函数／运行时证明。

volume的HasStack Actor前缀由独立的446/25版本守卫读取器解析，未更改共享parser；
28字节是空class-state结构读取的结果，不是通用偏移。字段、失败条件、上游固定版本及
5项guard测试见[格式说明](FILE_FORMATS.md#ue3-actor空class-state前缀阶段365只读有界profile)。
最终从原盘物理包头再次读取版本后，对152个源／当前完整volume对象重新验证，
全部对象payload一致、结构前缀与已记录字段完全一致；没有从解压后的逻辑视图误读压缩包summary。

新增证据：`typed-volume-touch-proof.json`、`volume-consumers.json`、
`volume-title-native-readbacks.json`、`volume-fieldname-string-table-proof.json`和
`fieldname-owning-ui-consumer-proof.json`。

## 仍未闭合与下一支线

**未将用户的大章节标题报告标成修复完成。** 已闭合的路线确实在CSMB结束后显示大字，但其资源内容是区域／地点名，不能自动等同用户指的另一类章节卡。

直达HUD的实际volume调用者及其菜单文字支线本轮已经追到。余下应转向其他HUD／电影入口、
原生事件／数据驱动纹理选择或尚未解析的函数profile，寻找真正不同于已验证入口卡及菜单
位置字段的标题生产者，而非重复查同一volume／入口族。原生PE的REA深度入口返回
unsupported PE architecture，本轮只保留只读的原生身份／有限字符串地址检查，不声称已得到
PPC反编译或原生纹理参数数据流。不得重跑GetChapterStr语音键、SubTitle37张定格图，
或拿尚未消歧的银行／性状残词充作章节名。先前15个函数元数据profile和39个非UI原生
资产payload的解析边界继续保留。

## 本地证据及重放

完整摘要索引为`build/phase-365-chapter-research/artifact-index.json`。关键证据：

- `entrance-consumers.json`：全部行动、类型、源／当前身份及TitleTex绑定。
- `end-signal-producer-proofs.json`与`postcutscene-kismet-links.json`：实际生产者和连线。
- `typed-entrance-renderer-proof.json`：完整函数／表达式及类型声明。
- `entrance-serialized-scene.json`、`title-parent-material-parameters.json`：显示对象与材质参数。
- `current-title-native-readbacks.json`：全部66别名的原生独立重放及原始像素检查。
- `volume-title-native-readbacks.json`：另一动态入口的全部37别名独立重放。
- `stateframe-profile-validation.json`：152个版本守卫结构前缀及源／当前完整对象摘要。
- `volume-fieldname-string-table-proof.json`、`fieldname-owning-ui-consumer-proof.json`：34个宏值及真实菜单控件。

```powershell
python -u -B -X utf8 build/phase-365-chapter-research/query_entrance_consumers.py
python -u -B -X utf8 build/phase-365-chapter-research/trace_postcutscene_links.py
python -u -B -X utf8 build/phase-365-chapter-research/trace_end_signal_producers.py
python -u -B -X utf8 build/phase-365-chapter-research/prove_entrance_renderer.py
python -u -B -X utf8 build/phase-365-chapter-research/verify_title_readbacks.py
python -u -B -X utf8 build/phase-365-chapter-research/verify_volume_readbacks.py
python -u -B -X utf8 build/phase-365-chapter-research/validate_volume_prefixes.py
python -u -B -X utf8 build/phase-365-chapter-research/test_cold_stateframe.py
python -u -B -X utf8 build/phase-365-chapter-research/prove_volume_touch.py
python -u -B -X utf8 build/phase-365-chapter-research/resolve_volume_fieldname_strings.py
python -u -B -X utf8 build/phase-365-chapter-research/prove_fieldname_ui_consumer.py
```

最终字图重放输出：`FINAL_READBACK_ACTIONS 87 ALIASES 66 NAMESPACES 36 LABELS 35 FAILURES 0`，exit0。所有结果为离线证据，不替代游戏内播放、艺术或用户验收。

volume与文字支线的最终输出分别为`FINAL_READBACK_VOLUMES 77 ALIASES 37 NAMESPACES 21 LABELS 21 FAILURES 0`、
`FRESH_VERSION_GUARDED_VOLUME_PREFIXES=152 SOURCE_CURRENT_OBJECTS_IDENTICAL=152 RESULT=PASS`、
`VOLUME_FIELDNAME_MACROS 34 BINDINGS 152 CURRENT_HANGUL 0 TYPED_DATAMANAGER_SETTER=1`及
`FIELDNAME_UI_CONSUMER MC2UIScene_Field.InitWidgets COMPLETE_LABEL_DATASTORE_BINDING_CALLS 5 SCENES [('UI_Field_Core.FieldMenu', 5)]`，
均为exit0。5项结构guard测试全部通过；它们不增加对真实游戏触发的证明范围。
