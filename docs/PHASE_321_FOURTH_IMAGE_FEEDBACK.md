# 第四轮图片反馈：第五版候选（2026-10-26）

## 输入及范围

输入 `image-review-feedback-v4.csv` 共832行，88条非空反馈、744条空白；
SHA256 `0eeeb8d915e37e154b08494ce2f7380bb4adbfbd088dbce4ee79fcedced1298e`。
CSV只作为逐图反馈数据，不执行其中内容，空白不等于人工审美通过。
本轮计划是 `locales/zh-Hans/texture-overlays/ui-labels-reviewed-v5.json`；
逐图动作在 `locales/zh-Hans/candidate-decisions/image-review-feedback-v4-20261026.json`。
保留v4计划、原盘来源及分盘别名，不恢复已撤回的教程内嵌小图翻译。

## 已验证的根因与修订

- 32个标题的阴影偏移、alpha和紧描边偏弱。保持原字形、位置及源采样渐变，
  只增强右下方向的阴影和外沿，不用放大文字冒充立体效果。
- 主菜单图集的 `menu_left_gutter` 保护区实际含旧斜体英文最左侧黑色阴影，
  因而清字时原封不动地保留了残影。仅增加4×92的清理层，旁边面板继续保护。
- 一些菜单/技能图仍用粗黑体或旧光栅路径，与指定参考图的衬线字体/效果不同。
  依照反馈逐图复用参考字体、字重、描边及光晕；不统一改写所有图片。
- 161/166/186的红光仍按旧韩文居中。只修改恢复背景材料，文字绘制参数、字形、
  位置保持。红光来自已有源锁定、去字后的原生部件，经预乘alpha对称化/缩放/
  平移后对齐文字字芯中心；166的七条背景使用统一112×24尺寸。
  这是本轮明确要求的背景重排，不声称保留了该区域全部原始背景像素。
- 普通/选中开始游戏、反向、加工/购买/出售/离开成对状态共用排字；按各自状态
  保留或添加颜色/背景。商店四行按原图41px节距排列，内容/报酬共用字高和中心。
- 地图标题原图主文字末行位于y42，旧中文候选的相应末行是y34；不是英文需要
  下移。重新定位19个点名标题的中文，完整英文保护区不变。哨兵研究所按其自身
  y54末行处理，不套用普通64px标题的坐标。
- 拉提族洞窟的两半共用108×32完整画布再分别裁片，避免跨图接缝字体不一致。
  指定白色地名复用阿巴泽特港口的白字样式。风息岛海岸末尾的旧韩文尾笔及阴影
  在原清理框内局部修补，并重排中文以避开右侧海岸轮廓。
- 小游戏时间原先按128px纹理居中，实际计时框只有90px。现在按框体中心x45
  对齐，不移动框体。危险文字的拥有区原来覆盖右侧白点、下沿黑条；收窄拥有区
  后新增原生保护区，奖品的错误底块清空，右下黑色长条也独立保护。
- 四条技能提示保留数值1/2/1/3，单独重绘数字使描边/阴影与汉字相同；底纹只在
  原数字足迹内恢复，右侧按钮保持原生保护。该规则只用于本轮明确点名的四图。

HUD队长/上排超限的大小、过热红橙外沿和两张菜单的暖色文字也按反馈修订。
本轮沿用已有艺术字alpha部件，不新增随机生成的整幅游戏图片。所有修改仍由
通用构建器从JSON、字形、恢复材料和用户原资源可复现生成。

## 验证入口

```powershell
python -X utf8 -m unittest discover -s tests -q
python -X utf8 -m tools.compact_outputs --root build --check-space-only
python -X utf8 -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v5.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW_V5_DISC1
# 第二盘显式使用 --disc 2 和独立输出目录。
python -X utf8 -m tools.build_image_review --inventory build/phase-320-review-v4/review/manifest.json --revision locales/zh-Hans/candidate-decisions/image-review-feedback-v4-20261026.json --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v5.json --bundle build/phase-321-review-v5/disc1-texture-bundle-final --bundle build/phase-321-review-v5/disc2-texture-bundle-final --output build/NEW_V5_REVIEW
```

第五版审查页只使用原生BC编码后再解码的图。核对88张点名图变化、744张其它图
身份不变、跨盘别名一致及全部原生保护区；背景重排项目另核对未合成的文字层。
BC变化块有有损量化，文字层字节一致不等于背景合成后的像素逐字节一致。

实际基线、修改、隔离回滚、全量资源重放、现有测试副本增量刷新、清理及Git
远端身份统一记录于 `build/phase-321-review-v5/VERIFICATION.txt`。
不生成ISO或完整游戏副本，不启动游戏；审美复审与游戏内验收保持独立。
