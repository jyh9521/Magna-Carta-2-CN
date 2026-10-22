# 第289阶段：章节入口图片实际汉化

## 实际采用

`locales/zh-Hans/texture-overlays/chapter-entry.json` 将章节入口 `ch01_01_vill` 的韩文图片文字替换为既有字段译名 **风息岛村庄**。不是新增INT草稿：batch121、14159条、七Font、315字幕保持。每盘同时处理 MC2Game export55740、UI_Title export25、UI_Title_Jpn export25；两盘独立原件验证，精确名称调查见 [别名调查](PHASE_289_CHAPTER_TITLE_ALIASES.md)。仅这一组图片完成离线替换，不代表全部图片文字完成。

## 可复现技术

通用 `tools.texture_overlay` 从结构化locale文字与hash锁定Noto字体生成文字层；Pillow/fonttools版本写入计划。BC3颜色/alpha有损确定性量化，预览从实际编码结果重新解码，不以原始绘制图冒充输出。512×64图片只授权 `[116,0,276,64]` 区域的4×4块；区域外块和对齐padding逐字节保持，区域内部旧文字和局部辉光被替换，不宣称区域内所有装饰像素原样。

工具锁定包、导出payload、tiled数据、尺寸、单mip结构，追加payload并修正SourceArt/mip绝对指针和对应导出size/offset；原logical前缀仅允许选中导出表8字节变化。压缩包重建仅更新压缩头块/追加尾块，保留其他压缩块。独立解压回读校验正确纳入压缩chunk-count字段变化。合成测试覆盖raw/LZX包和raw/LZX bulk四组合，错误hash/对象/区域/重复选择均拒绝。

MC2Game底包必须是既有Font candidate hash `5595562dab1233cbbf7979fff1b9c9ca031707b40f10adf75eb97ec1e999d425`，不是原始MC2Game；显式font→texture SHA链允许同资源连续变换，其他字幕/INT/TOC角色冲突依然拒绝。合成器在最终纹理包上重新验证七Font完整结构/ink/覆盖，一次计算统一TOC。纹理rollback恢复Font底包，不撤销此前字体工作。

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/chapter-entry.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-289-verification/texture-bundle
python -m tools.compose_locale_resources --plan locales/zh-Hans/locale-compositions/disc1.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --verify-root build/phase-289-verification/disc1-composition
python -m unittest discover -s tests -q
```

首次构建用新目录与`--output-dir`替换`--verify-root`；字体底包按原有cumulative-font-route流程先构建。字体来源和OFL见 [字体补充](FONT_SUPPLEMENT.md)。所有原图/候选包/解码预览只在忽略的build目录，不入Git。

## 收尾与接续

双盘comparison纳入两项独立Title资源，资源数29/31。第一盘旧测试目录通过prepared/旧包/新包/原始新增资源hash锁定的explicit-resource-enrollment计划增量刷新；默认同集合保护不变。保留旧27资源包与隔离恢复证据，不生成ISO或整游戏副本。四项交付及精确命令/输出/退出码见 `build/phase-289-verification/VERIFICATION.txt`。

**下一实际工作**：其余章节/BOSS入口图片和GameOver双图及别名；未知动态UI字段/성쇄只凭新证据推进。精确名称4145包调查不排除其他名字同图或动态路径，不等于全游戏图片覆盖。离线验证与游戏内验收分开；本轮不启动游戏。
