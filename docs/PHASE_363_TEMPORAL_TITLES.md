# 阶段363：过场特写字图重新制作

## 原因与实际显示路线

用户否决了首版“守护者阿蒙”：清字区域形成平滑色块，字形也过厚。该原型未刷新测试目录，标为 rejected；装备 v29/v30 和首批地图涂抹原型同样退役，不作为成品。

**Verified**：15张 Boss UI 模板、67个物理别名已经中文，并不覆盖过场电影中的像素。双盘81段 CSM 的有界抽样和逐段复核找到下列11段／10个名称。每个原盘成员的大小和 SHA 另由盘目录及实际资源核对；没有把地图目的地当作用户所说的“大章节标题”。章节路线仍单列在 [修复列表](GAMEPLAY_FIX_LIST.md)。

| 盘 | Bink | 中文 |
|---|---|---|
| 1 | csm00-35 | 守护者阿蒙 |
| 1 | csm02-52、csm02-54 | 恸哭之门 |
| 1 | csm02-61 | 阿斯塔罗斯 |
| 1 | csm03-122 | 修亚伦 |
| 1 | csm03-185 | 巨型安格勒 |
| 1 | csm04-111 | 利维坦 |
| 1 | csm05-82 | 贝里艾尔 |
| 2 | csm06-80 | 阿斯莫德乌斯 |
| 2 | csm11-50 | 普尔森 |
| 2 | csm13-40 | 斯特拉斯 |

## 背景不是整条抹平

原字与移动背景烘焙在同一 RGB 视频中。重做先独立审查原片的无字前后帧，再按实际遮挡选择时序重建；审查范围包含全部授权活动帧，而不是只看嵌字后的中间一帧。原字遮挡处属于重建，**不是找回原始无字底图**。

- 守护者等片段使用流／特征上下文重建。常规文字面板保留原翼饰；利维坦须排除两侧完整翼饰及内缘黑轮廓，不能只保护外翼。
- 贝里艾尔的牙齿、斯特拉斯的符文对整面板特征重建敏感。它们改用经有限值守卫的 RGB 传播结果和旧字支持域的稀疏 r6 蒙版；模型遮罩必须覆盖所有实际回填像素，不能把模型未处理的像素当干净底图。
- 原图支持域外 RGB 在编码前逐字节不变。视频重新有损编码后，这个保证不等于域外所有解码像素仍逐字节相等；报告分别列原始前缀的严格一致和后段量化误差。
- 新字体采用较轻的无衬线、原生字号和字距、细黑边与珊瑚至奶油色渐变。原生翼饰不重画。装备的14张立绘另采用 v31 稀疏 RGBA 修复，42段文字全部右倾 `italic=+0.18`，见 [阶段360](PHASE_360_EQUIPMENT_REMAKE.md)。

### Verified：结尾暗下去不等于旧字消失

早期拟合把场景整体淡黑当成标题 alpha 归零，错误选择仍有韩文阴影的结尾供体。逐帧原始解码复核后：

- csm02-52 的旧字到239帧，240起为黑；不是235帧。
- csm03-122 的旧描边到269帧，270为黑；269帧只清旧字，不再画中文。
- csm03-185 的旧字到539帧，540起为黑。
- csm02-54 保守采用173及以后为无字结尾；csm02-61 采用1415及以后。

后三类全局淡黑把字形透明度与曝光拆开：`frame_alpha` 控制字形／描边，`frame_exposure` 只缩放前景 RGB。曝光量化为零时关闭字形，避免黑色中文模板浮在淡出末帧。背景修复活动可比中文字形长一帧，审计据两者并集判定真正未活动帧。

## 可复现生产输入

入口为 `locales/zh-Hans/boss-intro-captions-v33.catalog.json`，引用11份独立、不可变源锁计划。小型稀疏 RGBA 帧修复及二值蒙版在 `locales/zh-Hans/video-repairs/boss-intro-v33/`；该目录的 `PROVENANCE.json` 保存逐片生产分支、上下文范围、模型及冻结输入散列。不提交完整电影、原始完整帧或神经模型。

`tools.build_video_repair_assets` 只负责把已经审阅的原生裁剪冻结成源裁剪散列绑定的稀疏补片；它不执行修复模型，也不判断美术质量。输入逐帧 SHA、画布、活动帧、蒙版像素数和所有路径均受限；非授权位置必须为全零 RGBA，授权位置 alpha 必须255。生产重建只需原片、补片、固定字体和已授权编码器，不需要再次运行机器学习模型。

先用 `tools.materialize_resource_sources` 从用户原盘提取版本化描述符列出的11个资源：

```powershell
python -B -X utf8 -m tools.materialize_resource_sources `
  --descriptor locales/zh-Hans/source-resources/boss-intro-movies.json `
  --project-root . --inventory 1=build/disc1-hashed.json --inventory 2=build/disc2-hashed.json
$catalog=Get-Content locales/zh-Hans/boss-intro-captions-v33.catalog.json -Raw | ConvertFrom-Json
foreach ($item in $catalog.entries) {
  python -B -X utf8 -m tools.build_worldmap_captions `
    --plan $item.plan.path --plan-sha256 $item.plan.sha256 --project-root . `
    --source-root build/boss-intro-source-originals --output-dir ("build/boss-intro-codecs/"+$item.id) `
    --ffmpeg <固定FFmpeg绝对路径> --ffmpeg-sha256 <已核对摘要> `
    --encoder <授权RAD编码器绝对路径> --encoder-sha256 <已核对摘要>
  if ($LASTEXITCODE -ne 0) { throw "电影重建失败: $($item.id)" }
}
```

`build_worldmap_captions` 名字沿用最初的地图研究，但其音轨运输层是通用 BIKi 工具，不会把影片分类为地图。固定字体及栅格库身份由每份计划锁定；字体获取来源见 `references/font-sources.lock.json`，Sans Regular 身份必须匹配计划，不能以 Serif 替代。输出目录必须新建，失败产物先核对再换新输出重试。

### Verified：原片前缀、音轨与编码帧数

`encode_from_frame` 只对显式源锁的时序标题启用。第一处修复以前保留原始视频包，并在拼接后独立回解核对全部前缀 RGB。后段从独立关键帧起编码，再重新组装 BIKi 帧表／文件长度／最大帧字段；整个原片的6条音轨元数据和逐帧压缩包保持不变。

RAD 的原生 AVI 读取在部分时长下会少读最后一帧。`encoder_guard_frames=1` 显式补一个重复原始尾帧；只在编码器多出0–1个声明的保护帧时按严格结构裁除。仍缺少实际目标帧、超额数量、音轨、几何或帧率不符都失败，不以修改帧数头掩盖缺帧。每个成品再全帧独立解码，与预编码渲染及视频运输结果交叉检查。

## 研究来源与未采用路线

可选研究使用 Zhou、Li、Chan、Loy 的 [ProPainter](https://github.com/sczhou/ProPainter)，固定提交 `326782529a63d997cab80ab21439b92ed422b3d3`，遵循其 S-Lab License 1.0。模型、权重、CUDA环境与完整研究帧仅在忽略的 build 中；本仓库不再分发或重新许可这些内容。生产补片冻结后不要求此依赖。

原生512×192裁剪不缩放。特征上下文变体只在官方推理流程中把图像传播结果替换为 masked frames／原始 mask，再进行流、特征和 transformer 处理；RGB传播变体保留原流程。两者都在 uint8 转换前断言预测有限。工具版本、三份模型 SHA、命令、裁剪范围及选定补片 SHA 保存在本轮研究凭证。

失败研究包含单／多层 homography、短步稠密光流和双锚点，均在多深度移动结构处出现接缝。FP32 复跑仍有同类黑块，因而“单纯 FP16 精度问题”已被实验排除；不能把有限值检查通过当成画面合格。完整失败结果保留在忽略目录供复查。

## 验证与交付边界

逐帧原生检查、实际 Bink 回解检查、源锁／音轨／时序测试、隔离回滚及现有测试目录的摘要增量刷新记录在 `build/phase-363-title-rework/VERIFICATION.txt`。继续复用原有测试入口和 v1.0 安装器，不生成新 ISO／完整游戏副本，不改变用户补丁开关、配置、存档和 runs。

这些证据证明离线资源及有界画面检查，不代表游戏播放、换碟、全流程或用户美术验收。大章节标题单独追踪，不以这11段过场特写的完成替代。
