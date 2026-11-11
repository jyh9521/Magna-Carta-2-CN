# 阶段369：23项未解码图片的逐项原生闭合

## 输入与结果

本表针对阶段366明确留下的 **13个resident＋10个historical** 未解码对象，不把这23项称为全游戏图片总量。输入为阶段368真实recipe，SHA256：

`7fc7aca33b52a1f2cbf0c9d70e90181de26aafecd4b2362a49f52f8a9224a0fc`

**Verified：**23个完整Texture2D导出、72个逻辑mip现已从该recipe对应的实际数据重读、解码、逐图审看。每个原生导出精确读到结尾；每个mip的可见单元地址唯一且在物理分配内，共享tail单元不重叠；全部提取／逆变换字节恒等，PNG重开RGBA恒等。另一盘同成员／同完整对象身份的23个payload逐项完全相同，不根据叶名称或相似像素合并身份。

实际像素确认：**0个韩文漏译，1个B控制器键、6个光效、1个Latin品牌Logo、15个透明／色块／渐变填充**。这些图全部保留；不是按`blank`、`Test`或`eff`名字排除。新增只读工具没有修改游戏资源，没有开放这些格式的生产写入。

当前resident包`MC2Game.xxx` SHA256：
`9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7`

实际路径、导出序号、完整对象路径、包及payload SHA、全部mip的tile／linear／RGBA／PNG SHA和外置数据源锁见本地 `build/phase-369-coverage-closure/visual/native-decodes.json`。输出后再次读取所有输入包或原盘成员区间，摘要未变。候选图与研究报告留在忽略的build中，不提交完整游戏资产。

## 逐项结论

V01–V13的包均为`MC2Game/CookedXenon/MC2Game.xxx`；其余表中的短包名位于同一CookedXenon目录。所有行都分别保留源锁，不以同名合并。

| ID | 包／export | 完整对象 | 格式／尺寸／mip数 | 实际像素与处理 |
|---|---|---|---|---|
| V01 | MC2Game／55499 | UI_Battle.Tex.Battle_Bbutton | 2／64×64／1 | 红色B按钮，输入键标识保留 |
| V02 | MC2Game／55503 | UI_Battle.Tex.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V03 | MC2Game／55548 | UI_Battle_Master.Tex.od_eff_aa01 | 7／64×64／7 | 蓝色旋涡，各级无文字，保留 |
| V04 | MC2Game／55549 | UI_Battle_Master.Tex.od_eff_aa02 | 7／64×64／7 | 橙白旋涡光晕，各级无文字，保留 |
| V05 | MC2Game／55550 | UI_Battle_Master.Tex.od_eff_aa04 | 5／16×128／8 | 洋红双端竖光束，各级无文字，保留 |
| V06 | MC2Game／55551 | UI_Battle_Master.Tex.od_eff_aa05 | 5／256×64／9 | 金色横向火光，各级无文字，保留 |
| V07 | MC2Game／55552 | UI_Battle_Master.Tex.od_eff_aa06 | 5／128×32／8 | 紫色横向电弧，各级无文字，保留 |
| V08 | MC2Game／55558 | UI_Battle_Master.Tex.stagage_hline02 | 5／16×32／6 | 青色竖光柱，各级无文字，保留 |
| V09 | MC2Game／55579 | UI_Core.Textures.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V10 | MC2Game／55610 | UI_Field.Textures.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V11 | MC2Game／55637 | UI_Field_2.Textures.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V12 | MC2Game／55665 | UI_InternalTest.Textures.Field_Dialogue_body | 2／2×2／1 | 4像素均不透明黑色，保留 |
| V13 | MC2Game／55704 | UI_Store.Tex.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V14 | UI_Title.xxx／72 | Global.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V15 | UI_Title_Jpn.xxx／72 | Global.blank | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V16 | UI_GameStart.xxx／10 | Textures.Logo_Line | 2／1024×256／11 | MagnaCarta II品牌Logo，各级无韩文，保留 |
| V17 | UI_Battle_08_Jp.xxx／6 | Test.Skill_Bundle | 2／2×2／1 | 4像素alpha均0，透明填充保留 |
| V18 | UI_Battle_08_Jp.xxx／10 | Tex.Battle_BG_copy_2 | 2／2×2／1 | 4像素均不透明白色，保留 |
| V19 | UI_Battle_08_Jp.xxx／11 | Tex.Battle_BGcopy-3 | 2／2×2／1 | 灰白3种RGB、alpha均239，无文字，保留 |
| V20 | UI_Battle_08_Jp.xxx／147 | Tex.Skill_choose_BG_1 | 2／256×2／1 | 灰蓝渐变／边界像素，无文字，保留 |
| V21 | UI_Battle_08_Jp.xxx／154 | Tex.Skill_Kan_Quantity | 2／32×2／1 | 绿色量条与透明边缘，无文字，保留 |
| V22 | UI_Battle_08_Jp.xxx／155 | Tex.Skill_Kan_Quantity_translucent | 2／32×2／1 | 同类绿色量条，绿色alpha128，无文字，保留 |
| V23 | UI_Credit.xxx／59 | Tex.BlackBg | 2／2×2／1 | 4像素均不透明黑色，保留 |

审看入口为`contact-01.png`至`contact-03.png`。V03–V08及V16另有`Vxx-all-mips.png`，覆盖全部72个逻辑mip，而非只看最大层。2像素填充的RGBA统计也实际读取，不以缩略图中“看不见”作为透明判断。

## 新读法与复用边界

`tools/texture_inspection.py`是独立只读模块。现有`texture_layout.py`的生产单mip BC1/BC3 profile保持不变。

1. PF_A8R8G8B8／Format2：32位单元按dword反转，再按BGRA解释；不是BC纹理的16位word反转。
2. Format5／7分别为BC1／BC3，原始与LZX内联bulk均校验count、size、绝对指针和输出长度。
3. `flags=0x21,count=0,size=offset=0xffffffff`是packed-tail空bulk描述，不是4GiB图片，也不是损坏原图。共享tail所属层由已限定的二维power-of-two布局确定，并检查`MipTailBaseIdx`和所有单元不相交。
4. BC原生尾层尺寸钳到4，而实际逻辑mip可以是2或1像素。保留原生尺寸，解码整块后裁到逻辑尺寸，不误记为多个4×4图。
5. 外置`0x41`只接受调用者显式给出的源锁resolver；工具不猜文件名、扫描任意路径或自动选择同名纹理。源锁方必须先核对完整外置包／导出身份；通用模块仍复验LZX块结构、编码长度和解码尺寸。

V06／V07的三个高层外置mip已经实际回指到现行`UI_Battle_Master.xxx`的对应完整导出：`Tex.od_eff_aa05`的offset59066／65680，`Tex.od_eff_aa06`的offset68747。原生指针、count、size逐项相同，所有物理mip解码字节与resident完全一致，包括内联tail；不是根据图案相似推断。当前该外置包SHA256：`eb2ef63bb7581aa650cb88820167817428089f7dce594147a3f932774a45f76f`。

坐标来源是已固定并注明许可的Xenia `GetPackedMipOffset`；通道、枚举、bulk sentinel来源是固定UEViewer源码。沿用`references/texture-layout-research.lock.json`、NOTICE及既有许可证。阶段295原型是已有研究，不把它重述为本轮首次发现。本轮把有界只读实现纳入源码测试，并对历史111源锁纹理／121逻辑mip重新解码，全部RGBA SHA与阶段295研究相同。

**High-confidence deduction：**这些packed-tail坐标是游戏采样所用坐标，依据上游规则、地址约束及连续缩放图案；本轮没有观察游戏采样器或渲染调用。不将完整离线解码说成实际游戏验收。

## 开发测试

```powershell
python -m unittest discover -s tests -p test_texture_inspection.py
```

7项测试覆盖Format2通道、全mip布局及互不覆盖、原始／LZX解析、显式外置resolver、错误flags／sentinel／指针／尺寸／长度拒绝、缺失tail owner以及有限几何边界。新测试在模块加入前退出1（ImportError），模块加入后输出`Ran 7 tests ... OK`、退出0。调用接口为：

```python
texture = texture_inspection.read_texture(payload, names, serial_offset, decoder,
                                          external_resolver=locked_resolver)
image = texture_inspection.decode_mip(texture, index=0)
```

调用方在此之前核对包SHA、完整export身份和payload SHA。没有外置bulk时省略resolver。该接口不修改payload、包、源文件或任何生产格式开关。

## 独立章节卡与保留决策

这23项实际图像均不是韩文独立大章节卡；此前已证明的CSMB结束→EntranceTitle路线、入口／区域标题和volume路线并不自动等同用户所指章节卡。本次没有新增其实际出现帧、韩文原句或消费者绑定。**2026-11-11用户明确决定“这块没有就没有吧，别的不残留就行”，因此`UI-20261107-02`不再列为本轮继续追查待办。**保留此前未绑定的历史事实，不将撤销追查表述为已定位、已翻译或已修复。

已有教程嵌图、15张未绑定技能图和`Boss`字样的用户保留决定不变；本表也不把历史111中其余101项、243 resident候选之外的图片、电影或实际全流程自动判为审看通过。
