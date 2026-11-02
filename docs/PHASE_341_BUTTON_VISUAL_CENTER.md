# 阶段341：按钮可见中心、信息标签残影与辅助装备微缩

## 当前修订及用户纠正

本轮先处理三张截图，随后用户指出首轮预览中**辅助装备选中态**仍未在按钮中间，
并确认其他修改没有问题。因此第二次只调整辅助装备同一个消费者的 X/Y，
普通和选中态共用该消费者；文字、缩小后的字形、其他按钮与信息标签均保持。
证据和四张反馈图位于 `build/phase-341-ui-polish/`，最终构建位于其 `centered/`。

## Verified：原生资源与采样几何

### 快捷菜单

`style_ui.Base.StoreButtonBox` 的 StyleID 与三个父按钮的 AssignedStyleID 一致；
启用态 `DefaultImage` 指向 `UI_Store.Tex.Style_buttonBOX`。
128×64 的贴图含不对称的底部阴影，可见边框的中性字节阈值边界为
`[3,3,125,56]`（右/下为排他坐标），中心是 `(64,29.5)`，不是 `(64,32)`。
映射到96×41按钮，视觉中心为 `(48,18.8984375)`。

三个 `UI_Core.Scenes.QuickMenu...Category_0/1/2.Position.Value[1]`
各减少 `1.6015625`；X、字图、字体、UV、选中效果不变。
正常态字芯中心准确重合；选中态的 BC3/抗锯齿边界差异仍最多0.5源像素。
不以整张含阴影贴图的矩形中心替代按钮面板中心。

### 游戏时间与 SID

两份 `Field_MainMenu_Info_Tex04` 分别在 `MC2Game.xxx` 和 `UI_Field.xxx`。
文字单元为 `[152,16,80,16]` 与 `[152,32,80,16]`。
旧蒙版未清掉 SID 的原字及阴影；首行32还有57个非零 alpha 像素。
真实 `PlayTime_Title.ImageComponentTemplate` 的 UV 为 `[134,17,96,16]`，
**会读到第32行**，因此 SID 首行残留显示成“游戏时间”右下角的横线。

本轮以完整透明底恢复两个文字专用单元，再各绘制一次既有标签。
保留共同 em 缩放、字号、底线、渐变、样式与 UV；不全局过滤暗像素。
边框、位置标题、圆形标记、图集右侧和所有非目标纹理块保持。
逐像素比较必须忽略双方 alpha=0 的 RGB，以及视觉等价的 BC 编码差异；
纯存储字节不同不是可见残影。修正后第32行在实际时间采样窗内为零残留。

### 辅助装备：缩小与精确定位是两个独立步骤

两种状态 × 两份原生副本（`Startup_int.xxx` / `UI_Name_Jpn.xxx`）
的辅助装备字芯高由18降到17，成品解码宽度由73降到68。
只改变该层 `appearance.ink_box[3]`，不是只修改不会控制此绘制分支的名义字号。

首轮只缩小字图，沿用消费者 `(1,5)`，实际字芯偏右0.5、偏上1.3203125源像素。
新增真实消费者检查对首轮成品产生 `CHECKS=20 FAILURES=4 RESULT=FAIL`，
覆盖普通/选中态和两个物理副本，而不是修改预览图来掩盖游戏资源问题。

最终只调整
`UI_Field_2.Scenes.Item.ItemListPannel.CategoryBundle.CategoryBox_3.Category_3`：

| 字段 | 首轮成品 | 最终成品 |
|---|---:|---:|
| `Position.Value[0]` | 1 | 0.5 |
| `Position.Value[1]` | 5 | 6.3203125 |

父按钮为87×43，视觉中心为 `(43.5,19.8203125)`。
该字图单元起点为88，但消费者 UV 为 `[0,90,88,29]`，必须计入这2像素差。
实际 UV 内的字芯为 `[9,5,77,22]`；最终两轴中心与父按钮视觉中心相等。
两个状态、两份纹理的中心误差均为0。字号及纹理与用户确认的首轮成品逐字节相同。
`correction-only.json` 将本次纠正限定在该对象两个 float 字段，其他包/字节不变。

上述均为离线原生资源证据。最终游戏缩放、双线性采样与着色器合成仍由用户实测；
预览明确标注为资源回放，不是游戏截图。

## 复现与回滚

语言数据为 `texture-overlays/ui-polish-v14.json`、`ui-polish-fields-v14.json`、
两盘 `ui-polish-revision-v14-disc*.json` 与 `ui-polish-audit-v14.json`。
通用构建复用 `build_ui_ink_revision`；审计为 `audit_ui_texture_polish`。
完整透明蒙版可由 `Image.new('L',(80,16),255)` 重建，透明修复片为
`Image.new('RGBA',(80,16),(0,0,0,0))`，二者均按 PNG 哈希绑定。
仍采用 restored BC3 + unchanged-block preservation，不放松 adaptive-alpha 门禁。

```powershell
$p = 'locales/zh-Hans/ui-polish-revision-v14-disc1.json'
$h = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.build_ui_ink_revision --profile $p --profile-sha256 $h `
  --source-root build/phase-341-ui-polish/baseline --output build/phase-341-ui-polish/rebuild-disc1 `
  --lzx-library build/lzx/native-verified/ue3_lzx.dll
python -B -X utf8 -m tools.audit_ui_texture_polish `
  --root build/phase-341-ui-polish/rebuild-disc1/candidate `
  --plan locales/zh-Hans/ui-polish-audit-v14.json --report build/phase-341-ui-polish/recheck.json
```

Disc2以相同原盘身份的四份资源重建，并核对最终两盘 recipe 中的8项哈希。
全轮写集为四包、六份字图、五个 Position float；不改正文、动态字体、存档和配置。
新原生中心合同取代阶段340针对快捷按钮的容器中心合同；其余地图、数字与同伴
回归继续保持，不能要求两个互斥的旧/新中心合同同时通过。

最新三态以用户指出的首轮成品为基线：20项检查中4项失败，最终20项全部通过；
隔离回滚恢复四份资源哈希（其中仅一包相对首轮改变），并重新出现同样4项失败。
`ROLLBACK.sh`只接受新建的本轮隔离目录，不回写正在使用的候选或用户数据。
首轮三项修订自身的原始基线与独立回滚证据另行保留。

收尾沿用 `compose_incremental_comparison` → raw-envelope 门禁 → 双盘recipe
→ 现有测试目录hash增量刷新，保留必要的依赖和回滚，不生成新ISO或整盘副本。
完整测试、源码身份、提交、四组CI及安装器验证以 `VERIFICATION.txt` 的实际记录为准。
