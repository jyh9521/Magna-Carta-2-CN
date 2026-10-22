# 第292阶段：主菜单、队伍名与盘号图片实际回填

## Verified / 已验证

在第291阶段64图/65层上新增完整14图/27层，累计78图/92层。双盘实际纹理别名400处（D1 198、D2 202），来源28资源并集；每盘新增5资源，不仅三个独立UI包，还包括TitleMap_MSPT六resident导出及UI_Pillar两套三导出。52新增别名全部真实Texture2D、单mip、Format7，完整扫描4145原包重查hash，见[别名证据](PHASE_292_FRONT_PARTY_ALIASES.md)。

主菜单两态：新游戏、读取游戏、选项、附加内容、影片、语音剧；返回两态、按START键；游戏名沿用最终显示覆盖“真名法典2”，不倒退旧草稿品牌。阿尔戈/塞蕾丝汀/朱特/洁菲各白字与红字态完整采用既有INT角色名。Guest短标签“临时”沿用“临时同伴”语义，原教程明确对应GUEST。两盘号均实际替换“第1盘/第2盘”。来源与词义置信分类见[逐图映射](PHASE_292_FRONT_PARTY_LABELS.md)。INT仍14159、batch121；七Font/315字幕不改。

## 区域、风格与实现

复用既有通用多区域BC3工具，无新增游戏专属代码。Menu_tex六菜单项两态+标题共13层；版权原块[0,92,256,20]逐字节及解码crop hash保护。保留两态白色/橙色发光区别与角色名红色状态、临时标签青色。START标识保留，按钮功能/UV/脚本未改。所有4像素对齐替换区之外原块及padding保持。

原Disc文字与下部盘形重叠。仅承诺上部[0,0,64,36]原块/像素保持；下部[0,36,64,28]为替换区。16号字采用默认居中，实际解码预览已审看，无需offset_y扩展。Guest原建议64x24在18号字下不满足8像素余量，实施使用完整64x32；28高菜单项缩至16号字，其余18号字。所有层通过字体cmap与ink-fit检查，图像实际编码再解码后审看，不拿绘制前预览代替。

## 可复现构建

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-292-verification/disc1-texture-bundle
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/ui-labels.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-292-verification/disc2-texture-bundle
```

首次构建换为全新--output-dir。恢复原资源使用第290阶段按清单从原镜像精确提取的通用配方，本轮ui-labels.json选中28资源；已有文件必须hash匹配不覆盖，禁止整盘复制。D1/D2纹理组件分别24/22资源，组合与对照包各50资源。构建输出、字体和原包不入Git。

## 收尾与未完成

复用现有D1测试根，hash保护显式增量纳入5原件；只刷新5候选+TOC和三元数据，共9文件。隔离恢复旧45资源检查点，另恢复28纹理资源与旧64图/65层locale JSON；当前保留78图/92层。基线1862、修改及清洁源码1868测试，原图输入复核、400别名预览一致、保护区、独立构建回读和远端身份结果记录在build/phase-292-verification/VERIFICATION.txt。

Guest精确widget消费与动态加载优先级尚未运行验证。大量角色/怪物名图、其他UI/教程、111格式缺口、原生可见硬编码、未知UI/성쇄仍待后续离线证据和实际回填；不宣称全部结束。不启动游戏、不生成ISO/整盘副本，最终游戏验收由用户完成。
