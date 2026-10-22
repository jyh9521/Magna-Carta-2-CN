# 阶段288：真实图片文字缺口及首个可执行纹理入口

## 结论与范围

**Verified（静态原版资源）**：现有INT草稿及字体补字并没有覆盖所有玩家界面图中文字。本轮实际解码并看到了章节入口条幅的韩文、战败提示的英文，以及独立日文战斗包内的日文帮助/队伍语句；这些文字来自Texture2D像素，不是仅凭资源名推测的“可能文字”。原始资源保持不变，本轮没有回填或生成纹理补丁，也没有启动游戏。

原双盘4145包调查只验证包表/字体候选，不能充当图片文字覆盖证明（见[FONT_BINDING_AUDIT.md](FONT_BINDING_AUDIT.md)）。本轮有意只选择已经存在的12个UI/教程源包，不重跑INT草稿统计。逐包D1 SHA与既有原始盘清单相符；随后直接读取D2 ISO对应12个资源，分别重新计算SHA，12/12与D1相同。没有重算整盘ISO SHA，也没有遍历4145包的全部纹理。

本轮对789个Texture2D export尝试严格解析，678个完成像素解码，111个明确保留为未支持（49个非Format7、43个packed lower mip或尺寸限制、19个非当前inline LZX bulk profile）。**678是成功解码的纹理数量，不是文字数量、已译数量或逐张人工看图数量。** 实际看图范围包括UI_Title、UI_GameOver、UI_Pillar_Title、UI_Textures和UI_Battle_08_Jp的接触表，以及下述原尺寸样本。教程和Credit未成功解码，不能由失败推断它们没有文字。

## 可定位的确切缺口

| 原版包 / export / path | 画面观察 | 尺寸 / 原始逻辑serial offset |
|---|---|---|
| UI_Title / 25 / Chapter01.ch01_01_vill | 原尺寸图清晰显示韩文`높새바람 섬 마을` | 512×64 / 165965 |
| UI_Title / 29 / Chapter02.ch02_01_Abazet | 原尺寸图清晰显示韩文`아바젯` | 512×64 / 详见texture-scan.json该export |
| UI_GameOver / 3 / GameOver_Tex | 烘焙英文`Game Over` | 512×64 / 109785 |
| UI_GameOver / 6 / Notice_tex | 烘焙英文`Press A Button`，中间保留控制器A按钮图形 | 256×64 / 140494 |
| UI_Battle_08_Jp / 58 / Tex.Communication_Text_Request_Emergency | 原尺寸图显示3行日文求助语句，不是Font atlas | 128×128 / 详见texture-scan.json |
| UI_Battle_08_Jp / 161 / Tex.Speech_Argo_0 | 透明底灰字，合成到黑底后可读日文队伍/核心相关语句 | 256×128 / 详见texture-scan.json |

UI_Title接触表中还可辨识大量章节地名条幅及混合日文、韩文的BOSS名字。UI_Pillar_Title接触表有DISC1/DISC2/GUEST图标；UI_Textures接触表主要是人物头像与边框。这里不将后两者当作必须翻译的漏译计数。UI_Battle_08_Jp的包名及像素证实它含日文，但**没有证明当前INT路线会加载该包**；不能把其全部文字当作当前必现漏译，也不能只因Jp命名而删去。

原尺寸PNG、接触表、完整源payload位置及hash全部只在忽略目录`build/phase-288-asset-research/`保存，不提交完整游戏图片或包。`speech161-black.png`只是为了观察透明层的黑底合成，不是修改候选。

## 章节条幅已有真实序列化消费者

`build/phase-282-verification/MC2Game-logical.bin` SHA256：
`e2a49cdd67c2b49f9b91fb517a49de33262ada4f3ec5a65c776a7d3126d1ecf4`。

使用原Engine/Core类表解析组件前缀及属性（不是盲搜4字节引用），得到MC2Game内以下链：

1. export44929 `UI_title.Global.Scene_EntranceTitle` 的 `Title` ObjectProperty指向43863。
2. export43863 `MC2UIImage` 的 `ImageComponent` 指向59695；静态宽高为512×64。
3. export59695 `UIComp_DrawImage.ImageRef` 指向83386。
4. export83386 `UITexture.ImageTexture` 指向37951 `Title_MatInst`。
5. export37951的 `Parent` 指向34835 `Title_Mat`。
6. 该材质下export37693 `MaterialExpressionTextureSampleParameter2D_0` 的 `ParameterName=TitleTexture`，`Texture` ObjectProperty明确指向55740。
7. export55740 `UI_title.Chapter01.ch01_01_vill` 为resident raw Format7纹理，512×64，原逻辑offset53366174，serial_size65914；实际解码呈现上表第一行韩文。

这是一条真实序列化入口/默认图像链；**不证明运行中一定采用此默认值、最终渲染、动态材质更新或其他地图标题的加载优先级**。本轮未擅自把静态Opacity=0等初始属性解释为运行时不可见。

完整带属性类型、逻辑位置和引用值的记录：`cooked-consumer-chain.json`。最初缺少Engine/Core包造成的解析失败已通过加载hash锁定原包并重建完整StyleGraph解决，最终记录无该类缺包错误。

## cooked/standalone别名是纹理补丁的必要对象

已独立解码并逐PNG字节比较，下列不是文件名猜测：

| MC2Game resident export | 对应standalone export | 完整PNG SHA256 |
|---|---|---|
| 55740 | UI_Title/25、UI_Title_Jpn/25 | `db9bf9b13841324de804b54edadda7ce92e06ca4d66a2f0d263281cbff6192ed` |
| 55656 | UI_GameOver/3 | `1e2c08a4a657c041b6a9a725558654f7a484340f4add70ad196d274927f04b02` |
| 55659 | UI_GameOver/6 | `450b036228dcf5b0380ec8e557ea0abb475958422f20780ed7ebf0181a145d02` |

resident与standalone序列化payload hash不同，不能据此否定像素同一；前者raw bulk flag0，后者inline LZX flag0x40，属性表局部引用也不同。像素同一也不证明对象加载优先级。当前字体补字已重建MC2Game资源并不意味着这些Texture2D已被替换；字体glyph atlas与章节条幅是不同对象。

## 下一可执行实现入口（尚未实施）

首个应实现的完整小组是上述章节入口一张图的3个已确认别名，或战败2张图的resident/standalone成组，而不是重复扫INT。执行步骤：

1. 在locale数据中用canonical对象路径和每个原始源/逻辑payload SHA锁定选择；中文标题沿用已审定地名，按现有512×64边界生成独立透明字层。`Press A Button`必须保留按钮图形或等效控制器符号，不把A当可任意更换文本。
2. 用独立纹理候选合成器替换完整指定图或明确字层区域，保留尺寸、mip数、像素格式、材质和对象身份；这不是font glyph补字。现有`ue3_textures`已能解出这些Format7，`supplement_font.parse_atlas_payload/atlas_tiles`已能校验其resident raw变体。现有白色BC3编码仅适用于新白色字层，不能未经证明便重编码原有彩色按钮和阴影；一般RGBA重编码器或无损旧块保留需单独验证。
3. 把同一候选像素写回独立LZX及cooked raw的各个已确认别名；长度变化走现有append/rebase工具，不盲改固定offset。保留原export大小、bulk绝对位置、指针等版本断言；TOC变化走当前构建器。还需查Startup/其他cooked副本，不能假设仅这3个就是全部。
4. 离线要求原图重放完全同一、汉化图实际看图、未选纹理/导出表/材质字节不变、解码与指定像素一致、逐别名反向回滚精确恢复原文件；再接双盘现有资源比较与hash保护增量刷新。
5. 静态完成后由用户在对应地点入口或战败画面实际验收；当前还存在离线实现工作，研究没有取代汉化完成门槛。

## 重放与证据

PowerShell在仓库根目录，设置`$env:PYTHONIOENCODING='utf-8'`。脚本只读取原版并输出忽略目录，既有产物可能被重新生成；正式重放应先另存证据或使用新研究目录，不覆盖源包。

```text
python build/phase-288-asset-research/scan.py
PASS resource SHA locked;all target exports attempted;originals read only
python build/phase-288-asset-research/consumer.py
python build/phase-288-asset-research/disc2_check.py
PASS disc2 12 source resources rehashed, identical=12
python build/phase-288-asset-research/summarize.py
```

本轮上述命令exit0；`consumer.py`输出真实属性链，`summary.json`汇总789/678/111及4组像素别名比较，`input-lock.json`记录2盘清单、原逻辑映像/表、LZX DLL和所有复用解析器SHA，`dual-disc-identities.json`记录12个D2实际资源复核。扫描后12个D1输入重新hash，全部仍为原值。

解析技术沿用已记录的一手UEViewer MCARTA分支及Xbox BC3布局研究，固定upstream commit、MIT归属和验证限制见[TEXTURE_RESEARCH.md](TEXTURE_RESEARCH.md)及[FONT_SUPPLEMENT.md](FONT_SUPPLEMENT.md)。本轮没有引入未归属第三方实现。

**仍未覆盖**：4145包其余纹理、111个不支持导出、未实际看图的已解码纹理、其他cooked/locale别名、动态载入/优先级、非Texture2D图片格式、xxx内嵌其他可见文本、原生硬编码以及全部实际游戏显示。不存在“扫描零命中所以完成”的结论。
