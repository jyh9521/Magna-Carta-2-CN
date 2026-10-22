# 第290阶段：完整章节入口图片族实际回填

## 本轮结果与边界

章节标题exports25–71共47张成套采用：沿用上一轮1张、新增46张；两盘273个真实Texture2D别名全部处理（D1 132导出/13纹理资源；D2 141导出/16资源，资源并集17）。不是把全部纹理当三包处理：地图resident同时含UI_title和UI_title_jpn forced exports，使用实际完整导出path。两盘4145个原xxx逐件重新hash与精确叶名调查见[完整别名调查](PHASE_290_CHAPTER_TITLE_ALIASES.md)。精确名称范围仍不排除不同名字同图、动态生成及未来DLC。

结构化采用/源hash/稳定ID及JPN关键片段另存 `locales/zh-Hans/candidate-decisions/chapter-image-labels.json`；“元首之丘”的跨locale定位标记High-confidence deduction，不宣称官方中文。47图译文的证据见[全族映射](PHASE_290_CHAPTER_TITLE_MAPPING.md)：40既有字段、4已采用句内词组、3新增图像译文。“元首之丘”采用原JPN同任务两句“元首の丘”消歧，不按英语对象名猜元帅或仇敌；“马雷的隐藏书库”“马雷广场”由已采用马雷专名和普通场所词组成。图片新增译文与INT草稿分别计数，INT仍batch121/14159，七Font与315字幕不变。

## 数据与通用基础设施

- `locales/zh-Hans/texture-overlays/chapter-entry.json` 保留47个显式文字/字体大小/4像素对齐矩形、来源hash/稳定ID及17资源discs声明；通用代码不识别地名。每张仅替换其声明文字矩形，区域外BC3块和padding原样，区域内文字及部分辉光重建；不宣称所有区域内装饰像素相同。47张编码后预览全部逐图目检，长标题按实际字框选择显式字号；恸哭之门保留暖金文字/红描边，其他默认灰白。
- `--disc 1/2` 是显式筛选，不靠目录名混用来源。含discs声明的计划未指定disc即拒绝，manifest记录disc；composition必须同盘并独立重放全部包。每资源原件仍由对应原ISO读取核对，两盘相同hash只共享语言/编码，不混合来源。
- 文字层上限由32到128，仍受16M总像素/32源资源/单包128导出等界限保护；两个纹理bundle分别13/16资源。单轮内BC3编码cache按完整RGBA与宽高复用，不跨原图修改块，独立重放从新cache计算。颜色参数仅接受明确RGBA字节和三个已知键。
- 完整资源包为D1 39、D2 44成员。resource phase检查与raw comparison共享显式64上限；65仍拒绝。只为已证明地图别名扩容，不删除角色/path/hash/TOC检查或默默漏资源。新增测试覆盖64通过/65拒绝、disc声明、palette与cache等。
- MC2Game仍从已验证Font底包叠加上一轮同一village图片，最终MC2Game字节与上一轮相同；两个Title独立包增补46图，地图包在各自原件上append/repoint。未选导出payload与metadata及所有Font继续保持。

## 可复现构建

先按既有字体流程生成锁定Font底包，再在新目录执行：

```powershell
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/chapter-entry.json --disc 1 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/chapter-disc1-textures
python -m tools.build_texture_overlay --plan locales/zh-Hans/texture-overlays/chapter-entry.json --disc 2 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output-dir build/chapter-disc2-textures
```

把实际manifest路径/hash写入对应locale-compositions后按原合成流程构建。当前已采用路径为 `build/phase-290-verification/disc1-texture-bundle` / `disc2-texture-bundle`；独立重放将`--output-dir`换`--verify-root`，仍须指定disc。原包/字体/PNG仅留忽略目录；可从用户原盘按清单精确提取17个选中小资源，不复制整游戏。字体来源与OFL沿用[FONT_SUPPLEMENT](FONT_SUPPLEMENT.md)。

## 原始小资源的精确恢复

以下仓库根目录脚本恢复计划声明的17个输入，不依赖本机研究脚本。先按BUILDING.md生成两盘hash清单并保留用户原ISO；不提取整个游戏。仅在来源成员hash匹配后写新文件，已有文件必须hash相同，不覆盖未知字节；Font底包仍按字体构建流程重建。

```python
from pathlib import Path
import hashlib, json
from tools.disc_inventory import Disc
from tools.font_binding_plan import confined_path
root = Path.cwd().resolve()
plan = json.loads((root / 'locales/zh-Hans/texture-overlays/chapter-entry.json').read_bytes())
hash_bytes = lambda data: hashlib.sha256(data).hexdigest()
discs = {}
for source in plan['sources']:
    number = source['discs'][0]
    if number not in discs:
        inventory = json.loads((root / f'build/disc{number}-hashed.json').read_bytes())
        discs[number] = Disc(root / inventory['image'])
    disc = discs[number]
    entry = next(e for e in disc.inventory() if e['path'] == source['path'] and not e['directory'])
    data = disc.read(entry['offset'], entry['size'])
    ref = source['original']
    assert hash_bytes(data) == ref['sha256']
    target = confined_path(root, ref['path'])
    if target.exists():
        assert hash_bytes(target.read_bytes()) == ref['sha256']
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    assert hash_bytes(target.read_bytes()) == ref['sha256']
print('PASS 17 selected original resources; no full game copy')
```

## 增量与两种回滚

复用原测试目录，D1显式enrollment增加10个地图资源；D2只构建离线包。D1默认同集合保护保持，新增资源在candidate/raw-controls必须原件hash匹配才纳入，raw-controls原字节不变；不启动游戏、不生成ISO/整游戏副本。

bundle的`rollback-check`恢复本次重建输入底包（Font或原件），它不等同上一轮运行检查点。迭代回滚另行锁定phase289 candidate：三个已纳入资源恢复旧中文village，新增地图恢复原件；执行ROLLBACK.sh在另一份目录恢复并验证，完整旧29资源也另行回验。当前canonical和live仍保留47图，不把恢复测试覆盖到当前候选。

基线/修改/旧源回滚、清洁源码测试、完整包回读、47逐图预览一致、273别名像素一致、hash守护增量刷新和推送证据见 `build/phase-290-verification/VERIFICATION.txt` 与本轮四项交付。

**接续**：BOSS标题15图和GameOver双图及其完整别名，然后其他UI/教程/已知111个不支持纹理导出、原生可见文本与未知UI/성쇄新证。47章节图族完成不是所有图片或游戏验收完成。
