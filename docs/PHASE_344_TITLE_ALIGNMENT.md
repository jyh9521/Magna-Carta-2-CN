# 阶段344：主菜单阴影残留与地图双行标题对齐

## 原图核对与已验证结论（2026-11-02）

本轮读取原盘来源锁中的资源，并与阶段343安装器使用的实际资源比较；
没有把反馈截图中的红线、箭头或用户的对齐回忆当作原图依据。
原图、当前版、修改版的原生解码对照及两张反馈图保存在
`build/phase-344-title-alignment/`。

- **主菜单**：两份 `Field_MainMenu_Big_Title0` 的文字清除框从 X=36 开始，
  而原韩文首字阴影延伸到 X=33..35，恰好落入旧图标保护区。
  两份实际字图合计194个残留像素；不是中文“主”的笔画或图标本身。
  在 `[32,0,4,36]` 的九个BC3块内，仅清除 RGB 最大分量不超过96的阴影alpha。
  所有RGB半块、X<32的图标、中文文字及其他行保持原字节/像素。
  X=32的弱光晕与阴影共用alpha调色板，保留值最大误差为3/255，未扩大写集。
- **地图**：检查49组地图/房间图、82份物理纹理。原作不是统一左对齐：
  风息岛、柯塔马雷、老狐峡谷、鲁哈尔特高原、贝尔福特为右对齐；
  杜南丘陵、杜南平原、鲁哈尔特盆地为左对齐；
  拉·斯特拉达及哨兵研究所为居中。阿巴泽特和两份海底洞窟为旁置英文，保持横排。
  上述方向由原图可见墨迹及相对位置核对；原图本身存在数像素的光学边距，
  新合同以汉字与英文的可见锚点对齐，中心允许半像素离散误差。
- **风息岛拼接**：标题跨 `Map_Highwind_Up` 或洞窟上图与 `Map_Highwind_Down`。
  两片同时向右平移37源像素，使中文右端从465移动到502，与英文右端502一致。
  两种地图/两份资源均覆盖；没有只移动标题的下半截。
- **覆盖结果**：41组物理双行组合中，基线3组通过、38组错位；
  修订后41组全部通过，菜单阴影归零。已正确的三组和三个横排组合不强制改动。

## 工程实现与保持项

`tools.translate_texture_regions` 的 `native-texture-translation-v1` 只处理
显式资源SHA、纹理tiles SHA、整数矩形和位移；语言数据在
`texture-overlays/title-alignment-v17.json`，审计在 `texture-alignment-audit-v17.json`。
不重绘字形、不改变文字、字号、Y坐标、字体、英文、地形或图标。

40份资源、42次操作中，2次为菜单alpha清理，40次为平移：
22次整块平移直接复制原生BC3块；18次非整块平移采用既有weighted-fit RGB和
adaptive alpha编码。编码前是严格整数像素复制，任何非零alpha裁出边界均拒绝；
原生回读最大alpha误差18/255、最大预乘颜色误差41/255，均小于显式预算24/48。
所有目标轮廓外零alpha保持零，写集外块、非目标export和英文保护区保持。
此方式保留此前修复过的渐变/暗行，不从旧覆字计划重新绘制而覆盖累计修正。

柯塔马雷、老狐峡谷左侧还存在极弱的旧黑色阴影（alpha最多9/3），
初始矩形平移会将其裁出。因此只向左扩展8像素的空白边界，完整保留该像素集合，
不放松“任何可见像素不得裁切”的守卫。老狐峡谷英文的实际上缘早于旧审计框，
本轮保护从Y=64开始，中文写集止于64，避免移动英文首行。

## 复现与三态检查

当前输入由阶段343的recipe解析并逐项核验，保存为本轮 `baseline/`，
`input-resources.json` 记录对应资源、原始输入与两盘身份。
它是44项稀疏检查输入，不是完整游戏副本。修改输出是新目录：

```powershell
$e='build/phase-344-title-alignment'
$p='locales/zh-Hans/texture-overlays/title-alignment-v17.json'
$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
python -B -X utf8 -m tools.translate_texture_regions --profile $p --profile-sha256 $h `
  --source-root "$e/baseline" --output "$e/rebuild"
python -B -X utf8 -m tools.audit_texture_alignment --root "$e/rebuild/candidate" `
  --fallback "$e/baseline" --contract locales/zh-Hans/texture-alignment-audit-v17.json `
  --report "$e/rebuild-audit.json"
# RESOURCES=40 OPERATIONS=42 RESULT=PASS
# GROUPS=41 ALIGNED=41 MENU_RESIDUE_PIXELS=0 FAILURES=0 RESULT=PASS
```

基线检查为 `GROUPS=41 ALIGNED=3 MENU_RESIDUE_PIXELS=194 FAILURES=40 RESULT=FAIL`，
退出1；修改后退出0。隔离回滚在另一目录先复制修改版，再恢复40项完整基线SHA，
要求重新出现同样的40项基线失败；当前修改候选与发布入口不回退。
完整源码测试基线2794项、修改版2806项，均有2项既定跳过；
新增12项包括边界、源/纹理hash、整块无损平移、非整块误差、英文保持及真实包读回。

## 同版本安装器、增量刷新与收尾

Disc1新增修改7项，Disc2修改39项；共享资源按原盘路径和SHA复用，
第二盘独有33项通过源锁定的 `resource_updates` 追加。recipe继续覆盖442/543项资源和2项DLC，
所有非本轮项保持阶段343身份。现有测试目录只刷新7项，不生成ISO或完整游戏副本。

单文件入口保持 `dist/MC2-CN-v1.0.exe`，两层显示版本仍为 `v1.0`，
PE数字版本仍为 `1.0.0.0`。从实际EXE审计全部payload、985项资源和DLC，
并运行安装器 `--verify-only`；这不启动游戏。
旧安装器、本轮源数据、隔离回滚、配置/存档/runs及活动依赖保留；
只清理经文件集合/摘要复核的可重建打包与已完成CI展开缓存。

本轮真实命令、成品SHA、独立重建、回滚、清理、提交及四组Actions状态记录在
`VERIFICATION.txt`。`MODIFIED_FILE.json` 指向实际安装器，另外保留
`DIFF_FILE.patch` 和可执行 `ROLLBACK.sh`；完整游戏资产不进入Git。
所有观感图均为原生资源离线回放，`game_rendering_verified=false`；
最终缩放和游戏画面仍从原测试入口由用户复测。
