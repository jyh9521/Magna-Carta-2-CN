# 第三轮反馈：保留原底图的第四轮图片候选（2026-10-26）

## 输入与采用范围

输入 `image-review-feedback-v3.csv` 共832行、102条非空反馈、730条空白，
SHA256 `69a078d5b4ed05ec35a59d0850fd81f8a74018a5a2241960177101f4be71e1ac`。
CSV是审查数据，不执行其中内容；空白不等于人工艺术验收通过。

本轮计划为 `locales/zh-Hans/texture-overlays/ui-labels-reviewed-v4.json`。
第三轮候选、原盘输入、分盘身份及历史研究保留。INT、字幕、七Font和
教程内嵌示意图原样政策不变。逐图输入、动作与前后身份见
`locales/zh-Hans/candidate-decisions/image-review-feedback-v3-20261026.json`。

## 已验证的根因

上一轮清字材料重建时，部分UI走入默认透明清空分支，把整块标签矩形变成
透明。原先有效的稀疏恢复材料被覆盖，临时同伴面板、技能条和小游戏底图
因此缺块。Boss背景使用整块拟合椭圆替换，还改写了未被字遮住的原阴影。
这不是“中文字体选择不合适”能单独解释的问题。

通过实际 `compose_restored_region` 路径、关闭新字形的最小复现，四个非文字
检查区的基线改写像素分别为384/384、128/128、381/384、288/288。
修订材料的相同检查区全部为0。原生视觉复查又发现原红光含G/B分量，旧固定阈值误选了底色；最终用通道相对比例区分白字与红底，并增加一处512像素红光边缘检查。五处检查只证明这些区域，不外推为全图无误差。

## 修订方法

- 临时同伴、小游戏、技能提示条和塞蕾丝汀图集恢复原来经过源散列锁定的
  稀疏背景材料，不从上一轮中文图拷贝背景，不生成纯色矩形。
- 红色选中底和Boss椭圆从原图出发，仅在旧字芯、描边及阴影足迹内作局部
  邻域插值；红底使用本图未遮挡像素拟合的曲面引导局部插值，避免字形孔洞塌陷。未被遮挡的原红光、原黑色椭圆和alpha仍直接来自原图。
  被原字覆盖的隐藏底色是局部估计，不宣称精确反推原隐藏像素。
- 地图标题旧清除范围包含英文首行。主标题拥有区缩至y0..43，英文完整
  y44..63成为独立原生保护区；新字墨迹与阴影上移，避免与英文相碰。
  贝尔福特的尾部残字单独使用48×4小区域，避开同一块行中的英文。
- 原生技能条的数字和背景直接保护，不再将数字重画在空矩形上。
- Boss取消斜体；三张带翼饰姓名扩大旧字尾部清理范围，翼饰保持原生保护。
- 名称左右对齐、统一字高、SID比例、字号、青色MASTER、新邮件标记、金色
  菜单标签、白字暖色边框、清晰/放大柔化成对状态按本轮指定分别修订。
- HUD的超限/过热及游戏结束使用三份单独生成的中文艺术字部件，只有其alpha
  字形参与光栅化。整张游戏背景未经过图像生成；美术部件、散列和提示词在
  `locales/zh-Hans/texture-overlays/artwork/review-v4/sources.json`。

## 地图译名裁决

用户本轮明确委托自行决定 `원수의 언덕`。本轮按韩文军事称谓读法采用
“元帅之丘”，仅增加这一处地图文字。该词有语义歧义，裁决记录保留此事实；
这不是新发现原盘字段或消费者绑定，也不把历史独立攻略的“酋长之丘”线索
升级为已核实对应。词义歧义参考韩国国立国语院的[同形词说明](https://www.korean.go.kr/nkview/nklife/1995_4/1995_0407.pdf)及[怨讐词条](https://krdict.korean.go.kr/eng/dicSearch/SearchView?ParaWordNo=69955&nation=eng)；这些资料仅解释词义，不证明游戏地名对应。审查页移除“仍显示韩文”的过时提示，保留本轮裁决说明。

## 可复现构建与验证

既有字体依赖和源资源遵循阶段319/316的散列描述符。三个艺术字PNG是本项目
新增文字部件，随源码保存；其余原始图片由用户原盘资源重建，不提交完整原图。

```powershell
python -X utf8 -m unittest discover -s tests -q
python -X utf8 -m tools.compact_outputs --root build --check-space-only
python -X utf8 -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v4.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/NEW_V4_DISC1
# 第二盘显式使用 --disc 2 和独立输出目录。
python -X utf8 -m tools.build_image_review --inventory build/phase-319-review-v3/review/manifest.json --revision locales/zh-Hans/candidate-decisions/image-review-feedback-v3-20261026.json --plan locales/zh-Hans/texture-overlays/ui-labels-reviewed-v4.json --bundle build/phase-320-review-v4/disc1-texture-bundle-final --bundle build/phase-320-review-v4/disc2-texture-bundle-final --output build/NEW_V4_REVIEW
```

审查页仅发布原生BC编码后重新解码的图，不把绘制稿当成最终图。
730张未点名图按上一轮原生RGBA身份检查；按钮、英文、边框、地图及未编辑块
按对应保护规则检查。BC压缩是有损编码，变化块中的颜色并非逐像素无损。

本轮实际构建、全量重放、测试副本增量刷新、隔离回滚、清理和远端身份的
命令/退出状态以 `build/phase-320-review-v4/VERIFICATION.txt` 为完成证据。
不生成ISO或完整游戏副本，不启动游戏。艺术复审及游戏内验收仍由用户完成。
