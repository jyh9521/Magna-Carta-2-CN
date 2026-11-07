# 阶段364：动画、图片与实际文本的遗漏筛查

## 本轮结论（2026-11-08）

本轮针对阶段363的**实际成品资源视图**，不是只检查译表或计划是否存在。
基线源码 `28778aca197dbd4f88e509393717232ac5195c00`，双盘 recipe SHA256
`38d60784f0179ebb6f1a94a8b8cec65ba9aef8aab6ee68af04ee308b5f610049`。

**Verified：共有29项确认仍需处理：13段电影、8种图片标签、8个文本字段。**
其中18项为本轮新增发现，另11段地图目的地电影是已知未部署项的重新核实。
此计数按影片／标签／字段分别统计，不把其跨盘副本当成新的内容。
结构化清单为 `locales/zh-Hans/omission-findings-v34.json`，包含资源／导出／字段身份、双盘来源、当前散列与证据等级。

本轮只筛查和登记，**没有改游戏资源、刷新安装器或生成ISO／完整游戏副本**。
“已分类”不等于“已翻译”；下面的已确认资源残留，也不冒充本轮游戏运行时观察。

## 一、动画：13段／20个物理成员

| 家族 | 唯一影片 | 双盘成员 | 当前成品结果 |
|---|---:|---:|---|
| WorldMap目的地 | 11 | 16 | 仍为韩文；旧重制原型被否决，确实没有进入当前recipe |
| 换碟提示 swapdisc01／02 | 2 | 4 | “请放入第1／2张光盘”仍为韩文，本轮新增发现 |

覆盖分母：原盘139个Bink成员／113种唯一内容全部重新绑定源SHA；26个当前电影输出全部核对recipe。
43种影片新做原生抽样，54次独立解码退出0，共156帧RGB样本（含Boss原版／当前对照）。
11段WorldMap每段检查0／90／180／270／359帧；两段换碟循环的30帧文字行逐帧相同，另有原生出现帧证据。
当前11段Boss参考帧、15段载入中点可见中文；4种厂商Logo作为品牌标识单列，不机械计为漏译。

其余70段CSM复用了源身份匹配的前轮定时筛查，**没有在本轮逐帧重看全部电影**。
WorldMap普通目的地不是用户所报“剧情过场后的独立大章节名称”，不得互相替代。

本地逐项原生证据、命令和覆盖账本：
`build/phase-364-omission-screen/animations/{FINDINGS,COVERAGE,SAMPLES,UNCHANGED}.json`。

## 二、图片：8种正常流派树属性标签／32个normal别名

确认对象为 `Style_Tree_Resources.Style_Skill_Status_*_normal`，共
`DEF、DEX、ESP、ESR、HP、SRV、STA、STR` 八种，原生128×32。
当前 `MC2Game.xxx` SHA256
`6a5d568d93a75083df6188dddc628a36e62d5c1c549055bba8567172a7c83bad`。
两盘MC2Game与独立Style_Tree_Resources包的32个normal物理别名，源／当前RGBA相同，仍有韩文。
42个匹配导出是**32个normal＋2个攻击副本＋8个空白／选择背景**，不是42张韩文字图。
独立包的 `Style_Skill_Status_STR_normalcopy` 双盘两处也有韩文，但本轮没有正常UI绑定证据，另列用途待查，不漏出记录，也不混成第9种正常标签。

本轮不是按文件名猜测：当前候选存在60条实际 `UITexture.ImageTexture` ObjectProperty引用，
并复核240条组件关系。例如：

```text
owner export79833:
Style_Tree_00_Juto.Scene.StyleTree_Juto_Main.TreePanel.JutoMainBundle.Box_2.Box_Normal.ImageComponentTemplate.UITexture_2
property ImageTexture, logical offset57914487 -> Texture2D export55422
Style_Tree_Resources.Style_Skill_Status_DEF_normal
```

这是**正常UI已序列化绑定的残留**；尚未观察游戏运行时的实际状态选择或最终可见性。
两盘4145包的该前缀查询未找到可替代的同名 `_Jpn` 组。

其他本轮覆盖与边界：

- 核查当前核心包中未纳入基础图片计划的243项UI候选：230项解码概览，13项保留unknown。
- 历史111项解码缺口：当前101项可解码，10项仍unknown；未将“未解码”写成“没有文字”。
- `UI_WorldMap.xxx / Textures.WorldMap_Whole` 的**32／32个现行标注都有中文覆盖**。旧“剩21处”属于历史状态，不能沿用为本轮新漏译。
- 4个原生BMP成员分别是纯黑Splash及服务器品牌Splash，不计为普通UI语言遗漏。
- 阶段311取消翻译的教程内嵌小图、保留合同和15张保留技能图不误报为漏译；`Boss`字样继续遵守明确保留规则。

本地记录：`images/FINAL_IMAGE_SCREEN.{md,json}`、`CONFIRMED_FINDINGS.json`、
`stat-pill-current-bindings.json` 与 `stat-pill-effective-aliases.json`，均位于本轮build目录。
这些分母不是全游戏所有纹理的逐像素检查。

## 三、文本：8条混合大小写Quest前缀

实际主线 `Coalesced.int` SHA256
`b7bb76bc8b07dcf217511cdbbebe69be19a99025530ae1ff57223e1ca576eadd`，
18176个物理字段中14159个不同于原版。
44份独立字幕、315个cue全部重新解析并核对时间／class身份，当前没有韩文／假名残留。

新增确认以下8个字段仍保留 `Quest` 前缀：

| MC2Quest.int节 | key | 当前值 |
|---|---|---|
| Ch02_252_0 | Success | Quest: 精华提取成功！ |
| 03_360_0 | get_item | Quest%s: 获得马雷的吊坠 |
| 05_112_0 | result | Quest: 护送完成 |
| 05_209_0 | Kill | Quest: 击败不死怪物 |
| 07_703_0 | Get | Quest: 获得红色宝石 |
| 11_303_0 | get1 | Quest%s: 神奇蘑菇 (%s/%s) |
| 11_303_0 | get2 | Quest%s: 毒蘑菇 (%s/%s) |
| 11_307_0 | get | Quest%s: 采集海底洞窟香料 (%s/%s) |

其中7条已经属于v27任务通知范围；之前只替换大写 `QUEST` 的规则没有覆盖混合大小写。
本轮只登记，`%s`、字段ID、控制符及现有译文均未修改。

主线另有63个韩文字段，全部保留独立分类：20个编辑器文档字段、24个原始“删除”标记、
10个尚未闭合拼接消费者的UI片段，以及旧测试／占位／损坏结构／语义待查项等。
它们不作为63个“新发现玩家漏译”合计；分类中23项排除出自动玩家漏译计数，40项继续pending，
不凭未找到引用宣称未使用。`Chapter11_27` 的 `성쇄` 仍待原始语义证据。

JPN／KOR是独立的替代语言库，INI是配置；分别保持来源和角色，不把其中日韩文机械合并为当前主线漏译数。
`KAN、SID、Boss、ChainBreak`、按键图标和品牌名按已有明确约定保留，不能用全局替换误伤。
尤其 `ChainBreak` 已有教程一致性复核中的显式原标签保留决定。

## 四、序列化／动态文本与真正章节标题

- 核心包3160个类型化FString中发现34个未变韩文字段：31个 `MC2Item.Comment`、3个Kismet `ObjComment`。
  原始字节、精确范围及原／当前owner payload一致已证实；按字段、位置和内容，高置信为编辑／制作注释。
  标志 `0x400001` 只证明可编辑等属性，不是“运行时不读”的证明；原生fallback仍未排除，不计为34个新玩家漏译。
- 5个实际独立UI消费者包共134个字符串，经正确宽串解码后没有韩文；31处 `initial text／Item Name／Quest Title／NO DATA／Level UP` 等默认值，继续作为动态覆盖与可见性候选，而非直接宣称漏译。
- `MC2Pawn.GetChapterStr` export6161 的完整返回为 `"ch" $ string(nChapter)`；8700个可解析函数内，
  两个声音消费者中的4段完整拼接均以 `Cue` 结尾。它是声音键构造器，不是已经定位的章节标题。
- 真正“剧情过场后大章节名”的显示路线仍未闭合；15个函数metadata profile、39个原生非UI载荷等边界保留。

重要格式发现：这些StrProperty的FString长度为BE，负长度字符载荷却是UTF-16LE。
`StyleGraph.scalar` 的BE显示会乱码、漏掉韩文或拒绝某些字节对；本轮用精确计数／终止符／原始范围独立复核，
没有在筛查期间修改共享解析器。最小真实样本：逻辑offset11878646、18字节、
`fffffff90cc75cb854b304c7a4c204d50000`，源／当前字段SHA256
`0737e63d61d5160ec382c36ff49cd1e85f31d3e6de9c0218819cb1521b2d7e3c`。
核心严格解析49176对象，另有8个已知结构缺口通过有界研究解析恢复；不能把未解析原生载荷当作无文本。

完整范围证明及剩余限制见本轮 `serialized-text/REPORT.md` 与35项散列索引。

## 可复用文本筛查

通用工具与语言数据分离：

- `tools.prepare_text_screen_inputs` 从锁定原盘、盘目录与当前recipe生成**仅文本子集**，全盘SHA前后复核。
- `tools.audit_text_residuals` 做脚本范围／限定前缀筛查与逐ID、逐值SHA、逐盘保留项分类，不翻译任何字段。
- locale选择器为 `omission-screen-inputs-v34.json`；规则与63项分类为 `omission-screen-v34.json`。
- 同路径不同盘内容不得合并；只有原／当前SHA及角色均相同的成员才共享审计工作。
- 新脚本残留必须显式分类；旧分类的字段值漂移或消失会报错，不把旧排除记录悄悄套到新内容。

从仓库根目录运行，使用现有双盘recipe与用户原盘：

```powershell
$recipe='build/phase-363-title-rework/prepared/recipe.json'
$selectors='locales/zh-Hans/omission-screen-inputs-v34.json'
python -B -X utf8 -m tools.prepare_text_screen_inputs `
  --recipe $recipe --recipe-sha256 (Get-FileHash $recipe).Hash.ToLower() `
  --selectors $selectors --selectors-sha256 (Get-FileHash $selectors).Hash.ToLower() `
  --inventory ("1=build/disc1-hashed.json="+(Get-FileHash build/disc1-hashed.json).Hash.ToLower()) `
  --inventory ("2=build/disc2-hashed.json="+(Get-FileHash build/disc2-hashed.json).Hash.ToLower()) `
  --project-root . --output-dir build/omission-screen/text-inputs
$inputs='build/omission-screen/text-inputs/inputs.json'
$policy='locales/zh-Hans/omission-screen-v34.json'
python -B -X utf8 -m tools.audit_text_residuals `
  --inputs $inputs --inputs-sha256 (Get-FileHash $inputs).Hash.ToLower() `
  --policy $policy --policy-sha256 (Get-FileHash $policy).Hash.ToLower() `
  --project-root . --require-classified --output build/omission-screen/text-screen.json
```

输入选择49个唯一文本视图／52个物理成员；分类结果为63个已分类脚本残留、8个已确认前缀遗漏，0个新未分类项。
`RESULT=CLASSIFIED` **不等于没有漏译**：`PREFIX_GAPS=8` 明确保留在同一行。
本轮三态／隔离恢复验证针对**审计策略副本**，不是回滚游戏；基线／恢复策略重现63个未分类项，当前策略保留8个真实遗漏。
四项产物及逐条命令在 `build/phase-364-omission-screen/VERIFICATION.txt`，所有原版／当前游戏资源保持不变。
