# 增量 comparison 阶段视图

`tools.compose_incremental_comparison` 为已有提取测试目录提供完整受管资源清单，
但不重新生成全部UE3包或复制完整游戏。它复用既有资源验证器、TOC第一列更新器
和 `refresh_oneclick_probe` 的合同。工具只生成新视图或只读验证，不部署、不运行游戏，
也不处理ISO目录sector。

## 输入与复用边界

1. 旧packet必须是已锁定的 `offline-disc-locale-raw-comparison`。三个阶段所有
   成员的大小、SHA、行/成员索引、TOC大小列均重新核对，包括未选中的成员。
2. 未改变的旧 `controls`、`raw-controls`、`candidate` 文件使用同卷硬链接。
   这些文件从不通过本工具写入，源packet不改名、不覆盖、不设只读属性。
3. 改变的candidate和新增成员的原始文件采用有界独占复制；供应文件不成为
   新候选的可写别名。新增raw-controls硬链接视图内已经复制的controls。
4. 新增成员必须在原TOC中已有原始大小，且原始文件由调用者显式锁定。
   新旧集合按实际路径差集处理，不硬编码资源数量或语言。
5. 不对输入 `.xxx` 做解压、重编码或运行时归一化；调用者提供最终合成后的
   候选字节。它不会把v6提取目录未选资源暗中替换为阶段324 ISO的归一化版本。

这里的“不可变视图”是一次性创建、只读重验的工具合同，不是文件系统写保护。
共享成员的链接计数会增加，内容保持；外部原地写入任何硬链接都会改变共享
字节，下一次哈希验证会失败。不要在视图内继续手工编辑；下一轮生成新视图。

## replacement manifest

```json
{
  "schema_version": 1,
  "kind": "incremental-comparison-replacements",
  "disc": 1,
  "toc_path": "MC2Game/Xbox360TOC.txt",
  "resources": [
    {
      "path": "MC2Game/CookedXenon/EXISTING_PACKAGE.xxx",
      "before_sha256": "OLD_EXTRACTED_CANDIDATE_SHA256",
      "file": "final-candidates/EXISTING_PACKAGE.xxx",
      "size": 12345,
      "sha256": "FINAL_SUPPLIED_FILE_SHA256"
    },
    {
      "path": "MC2Game/Movies/NEWLY_ENROLLED_EXISTING_MOVIE.bik",
      "before_sha256": "ORIGINAL_FILE_SHA256",
      "file": "final-candidates/movie.bik",
      "size": 23456,
      "sha256": "FINAL_SUPPLIED_FILE_SHA256",
      "original": {
        "file": "original-inputs/movie.bik",
        "size": 21000,
        "sha256": "ORIGINAL_FILE_SHA256"
      }
    }
  ]
}
```

大写名称、SHA和示例大小是类型占位符。实际SHA须为64位小写十六进制。

- `disc` 必须与旧packet一致；目前沿用既有双盘比较合同的整数1/2。
- `resources` 包含1–512项，完整新集合也最多512项；不删除旧受管路径。
- 既有资源的 `before_sha256` 必须等于旧提取packet的candidate哈希，且不得附加
  `original`。这不是ISO delta中的before哈希。
- 新增受管资源必须提供 `original`，其SHA必须等于before；原始文件大小和
  controls/raw-controls/candidate三种前置TOC中的原始大小同时核对。
- 所有 `file` 相对于replacement manifest的父目录，必须位于该根内，禁止
  `..`、绝对路径和路径重定向。需要跨源目录时，选择真实公共根或只物化所需
  的新增原始成员，不能绕过根约束。
- 供应文件正大小上限512 MiB。已声明的TOC和 `.xex` 不接受直接替换；TOC由
  构建器重建。大小写折叠重名、错误原始身份、错盘或哈希冲突在输出创建前失败。
- 已有资源的新字节等于旧candidate时，继续硬链接旧成员；完全没有变化或
  新增的选择被拒绝，不生成多余视图。

## CLI

在仓库根目录运行，输出父目录须已存在、输出目录须全新且与旧packet互不包含。
输出和旧packet必须同卷，工具不会自动改用全量复制来掩盖硬链接失败。

```powershell
$Base = 'ABSOLUTE_OLD_COMPARISON_PACKET'
$BaseHash = 'TRUSTED_OLD_MANIFEST_SHA256'
$Delta = 'ABSOLUTE_REPLACEMENT_MANIFEST'
$DeltaHash = (Get-FileHash -LiteralPath $Delta -Algorithm SHA256).Hash.ToLowerInvariant()
$View = 'ABSOLUTE_NEW_VIEW_DIRECTORY'
python -B -X utf8 -m tools.compose_incremental_comparison --base-packet $Base --base-manifest-sha256 $BaseHash --replacement-manifest $Delta --replacement-manifest-sha256 $DeltaHash --output-dir $View
if ($LASTEXITCODE -ne 0) { throw 'comparison view build failed' }
python -B -X utf8 -m tools.compose_incremental_comparison --base-packet $Base --base-manifest-sha256 $BaseHash --replacement-manifest $Delta --replacement-manifest-sha256 $DeltaHash --verify-root $View
if ($LASTEXITCODE -ne 0) { throw 'comparison view verification failed' }
```

`build` 输出 `status=BUILT`、完整资源数和新manifest SHA；`verify` 输出
`status=PASS` 并重读所有输入、成员、目录集合、硬链接关系和证明文件。
验证拒绝额外文件、额外空目录、路径链接和输入身份变化。

## 输出与回滚材料

- `manifest.json`：保持现有comparison消费schema，包含完整三阶段资源集合。
  `composition_manifest_sha256` 和 `comparison_plan_canonical_sha256` 绑定下面的
  本轮真实证明，不伪装为旧全量composition重建。
- `reports/view-plan.json`：前置manifest、replacement manifest及复用策略的规范身份。
- `reports/composition.json`：实际复制/链接操作、变化candidate集合、动态 `additions`，
  原始/原文对照保持结论；明确 `full_composition_replayed=false`。
- `reports/toc.json`：只改第一列的大小变化及 `inverse_changes`、源/结果SHA。
- `rollback/candidate-toc.txt`：旧candidate TOC的硬链接，保持旧全部列/行结尾。

只从当前提取candidate TOC计算合并后的第一列。TOC自身0大小、sector、其他列
和行结尾保持；反向变化必须精确还原原TOC。原文对照TOC不改。

所有输入在创建前和输出核验后重验。复制受声明大小约束，中途变大/变短都会
失败。manifest最后发布；失败仅清理本次确认创建且文件身份仍相同的路径，
不递归删除目录。外来文件、被替换的路径或系统拒绝删除的成员可能留下失败
目录，供核查；工具不删除这些内容，也不修改原始/旧/raw输入去强制清理。

## 接入既有提取目录

先用旧PREPARED的packet完成前置核对，再将新视图作为
`tools.refresh_oneclick_probe --packet`。如果新旧集合不同，必须生成
`explicit-resource-enrollment`：

- `prepared_sha256` 锁定当前PREPARED；
- `old_packet_manifest_sha256` 和 `new_packet_manifest_sha256` 锁定两代packet；
- `additions` 取 `reports/composition.json` 的实际新增集合，每项包含
  `path/original_size/original_sha256`；
- `disc` 与视图一致，`schema_version=1`、`game_rendering_verified=false`。

未新增路径时不传enrollment。刷新器仍要求新增文件在live的candidate和
raw-controls中都是原始字节；视图构建通过不替代这一现场前置验证。
刷新器备份实际改变成员和入口元数据，原文对照、配置、XEX、runs和存档保持。

## 已验证与待实测

Verified：自写小夹具覆盖旧成员共享且不写入、原始/原文/候选区分、TOC精确
逆向、前置冲突零输出、途中增长有界、失败清理隔离、两代视图，以及现有
folder refresh/enrollment/rollback实际消费。测试不包含完整游戏资源、ISO或编码器。

未作运行声明：包内字体/纹理/字幕正确性来自各组件自己的证明；BIK播放及
游戏画面仍属于运行验收。本工具不新增这类已验证结论。
