# 当前可执行流程（2026-10-18）

Python 3.12+，仅标准库；本次本地 Python 3.14.2。尚无汉化补丁构建命令。包表/字体只读解析和容器副本回写见 docs/UE3_PACKAGE_RESEARCH.md、docs/FONT_RESEARCH.md、docs/COALESCED_REBUILD.md；它们不等于完整补丁构建。

```powershell
python -m unittest discover -s tests -v
python tools/check_repository.py
python -m compileall -q tools tests
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 1).iso" --hash-image --output build/disc1.json --extract MC2Game/Localization/Coalesced.int --extract MC2Game/Localization/Coalesced.jpn --extract MC2Game/Localization/Coalesced.kor --extract MC2Game/Config/Xenon/Cooked/Coalesced.ini --extract-dir build/disc1-selected
```

Disc 2 同法指定独立输出及目录；首次解出后再次提取应使用新目录，工具拒绝覆盖。`--hash-files` 可为全部成员流式散列。版本、ISO SHA-256、XEX 身份见 docs/RESOURCE_SURVEY.md。

实际文本解析命令与 hash 见 docs/COALESCED_SURVEY.md；提取范围受 hash 和结构校验。现有 Coalesced 副本回写、字体候选和 TOC 大小更新工具见下文及对应研究文档；它们尚非可用汉化补丁，也没有 ISO 重封装。系列来源复现见 docs/SERIES_TERMS.md。

原件保持不变；派生资源在被忽略的 build/。最新约定为游戏测试全部由用户执行，开发阶段不自行启动模拟器或部署候选。未来中文验收应由用户在隔离副本中进行同场景前/后/回退录证。

## 字体使用方离线扫描

`tools/inspect_font_references.py --consumers` 枚举可解析 tagged 对象中的直接 Font/MultiFont ObjectProperty 引用，保留 import/export 身份、逻辑偏移与覆盖缺口。它与 `--inventory` / `--object` 互斥，不启动游戏、不修改资源。命令、62 包实测和组件前缀缺口见 docs/FONT_CONSUMERS.md。

## 最小补字原型（独立输出，未获游戏验收）

Xenia 测试必须基于用户提供的 `xenia/xenia-canary.config.toml`，不得静默替换为默认配置或覆盖画质、分辨率、时序及输入设置。`tools/launch_xenia.py` 保存逐字节配置快照，仅隔离 storage/content/cache/log；启动及加载核对见 [XENIA_TESTING](docs/XENIA_TESTING.md)。配置加载成功不代表中文显示通过。

可选依赖：`python -m pip install -r requirements-font.txt`。Noto 字体固定来源及 hash 在 references/font-sources.lock.json，字体原件只放本地 build/font-source。LZX 的本地构建、固定源码与许可见 docs/LZX_RESEARCH.md。

补字 CLI、hash 参数及两字计划见 docs/FONT_SUPPLEMENT.md；独立字体与 Startup 驻留对象都必须处理。补字输出只存 build，不覆盖原件。TOC 只更新明确验证的文件大小字段，见 docs/TOC_SIZE_REBUILD.md；它不证明所有运行索引均有效。四份候选文件的本地清单为 build/font-supplement/v2/deployment-plan.json，目前未部署中文试验。

## 双盘差异报告（只读）

在两份完整哈希清单准备后，执行：

```powershell
python tools/compare_discs.py build/disc1-hashed.json build/disc2-hashed.json --output build/multidisc-research/disc-comparison.json
```

输出包含双方身份、逐文件 SHA256/大小/位置及四种分类，不执行整合。已有输出拒绝覆盖。未来整合→汉化回写的规划见 docs/MULTIDISC_RESEARCH.md；目前没有正式合盘构建命令，汉化可以独立推进。

## 原始通用规范（下列命令仅示例）

---

# Building

This document defines how to rebuild the localization project from a clean repository checkout plus user-supplied original game files.

The build process should be reproducible, documented, and independent from private local working directories or undocumented manual steps.

---

# 1. Supported Game Version

Document the exact supported game build here.

Include when applicable:

- game title
- platform
- region
- distribution or store version
- executable or ELF filename
- version number
- file size
- SHA-256
- important archive hashes

Example:

```text
Game:
Platform:
Region:
Distribution:
Version:
Executable:
File size:
SHA-256:
```

Binary patches must not silently modify unsupported or unknown versions.

---

# 2. Requirements

List all required tools and dependencies.

Examples:

- Python 3.x
- Visual Studio Build Tools
- CMake
- Ninja
- Pillow
- ffmpeg
- external archive tools
- original game files
- specific redistributable fonts

Do not assume dependencies are already installed.

Where practical, provide exact installation commands or version requirements.

Example:

```bash
python -m pip install -r requirements.txt
```

---

# 3. Original Game Files

Clearly list all original files that the user must provide.

Do not include copyrighted original game files in the repository unless redistribution is explicitly permitted.

Example:

```text
original/
  GAME.EXE
  DATA.PAK
```

Document where each file comes from and how its version is verified.

If the game requires files from multiple regions or releases, document each source separately.

---

# 4. Repository Preparation

A clean build should start from a fresh clone.

Example:

```bash
git clone <repository-url>
cd <repository-directory>
```

Do not require the user to copy undocumented private work directories into the repository.

If local configuration is necessary, provide a documented file such as:

```text
config.local.json
```

and include a safe template such as:

```text
config.example.json
```

Local-only configuration should normally be excluded through `.gitignore`.

---

# 5. Preferred Build Entry Point

The build process should expose one obvious entry point whenever practical.

Examples:

```bash
python build.py --locale <locale>
```

or:

```powershell
./build.ps1 -Locale <locale>
```

or:

```bash
cmake --build build
```

Avoid requiring contributors to manually run a long undocumented sequence of unrelated commands.

---

# 6. Recommended Build Pipeline

Where applicable, the build system should perform the following steps:

1. verify dependencies
2. verify original game files
3. extract source resources
4. import localization data
5. validate translations
6. collect required characters
7. generate fonts or glyph tables
8. patch executable or runtime code
9. rebuild archives or containers
10. verify rebuilt resources
11. assemble final output
12. generate checksums or manifests
13. package release files

Not every project needs every step.

The build pipeline should reflect the actual technical requirements of the game.

---

# 7. Version Verification

Before modifying original files, verify one or more of:

- SHA-256
- file size
- expected version metadata
- expected byte sequences
- archive identifiers

Example behavior:

```text
Expected:
GAME.EXE SHA-256 = ...

Found:
GAME.EXE SHA-256 = ...

Result:
Supported
```

If the version does not match, stop with a clear error message.

Do not silently continue on unknown binaries.

---

# 8. Build Output

Generated files should go into a dedicated output directory.

Preferred directories:

```text
build/
dist/
out/
```

Example:

```text
dist/
  <project-name>-<locale>/
```

Generated files should not be scattered across source directories.

Temporary intermediate files should be placed under a build directory and should normally be excluded from version control.

---

# 9. Validation

Before producing a usable or release build, validation should check as many of the following as applicable:

- unsupported original game version
- missing dependency
- missing input file
- invalid translation encoding
- unsupported characters
- missing glyphs
- placeholder mismatch
- control-code mismatch
- malformed markup
- fixed-slot overflow
- invalid string lengths
- duplicate IDs
- linked-string inconsistencies
- broken archive structure
- invalid offsets
- unexpected file sizes
- missing generated resources
- failed binary patches
- checksum mismatch

If a validation error can cause corruption or crashes, the build must stop.

Warnings may be used for non-fatal issues such as possible UI clipping.

---

# 10. Rebuilding From Scratch

A future developer should ideally be able to:

1. clone the repository
2. obtain the required original game files
3. install documented dependencies
4. place original files in the documented location
5. run the documented build command
6. obtain a functional localization build

The project should not depend on:

- old private build directories
- manually modified intermediate files
- deleted binaries
- undocumented local tools
- chat-only instructions
- one developer's filesystem layout

Any unavoidable manual requirement must be documented explicitly.

---

# 11. Locale Selection

If the project supports multiple locales, the build system should accept the locale as a parameter.

Preferred example:

```bash
python build.py --locale zh-CN
```

Potential future usage:

```bash
python build.py --locale zh-TW
python build.py --locale ja-JP
python build.py --locale ko-KR
```

Generic tooling should not assume one locale unless the game itself requires that limitation.

---

# 12. Dependency Management

Document all project dependencies.

Where practical, include standard dependency files such as:

```text
requirements.txt
pyproject.toml
CMakeLists.txt
vcpkg.json
package.json
```

Pin versions when reproducibility requires it.

If an external proprietary tool is required, document:

- tool name
- required version
- download source
- whether redistribution is allowed
- where the user should install or configure it

Do not bundle third-party tools without confirming redistribution rights.

---

# 13. Fonts

If the build requires external fonts, document:

- font name
- source
- license
- required style or weight
- expected file location
- fallback behavior

Prefer redistributable open fonts when practical.

Do not commit proprietary operating-system fonts merely because they are installed locally.

If the build uses a system font, document that dependency clearly.

---

# 14. Archive and Resource Tools

If the project depends on custom extraction or repacking tools, document whether they are:

- included in this repository
- built from source
- provided by an upstream project
- external dependencies

If a tool is custom, include enough documentation to rebuild or replace it.

Do not make the project depend on an unexplained executable with unknown provenance.

---

# 15. Binary Patching

Binary patching must be deterministic and defensive.

Patch tools should:

1. verify the target version
2. verify expected original bytes
3. patch only intended ranges
4. fail on mismatch
5. verify patched output

Where practical, generate a report such as:

```text
Patched file:
GAME.EXE

Verified version:
SHA-256 ...

Applied patches:
- text decoder
- glyph lookup
- line width calculation
```

Do not rely on undocumented manual hex editing for release builds.

---

# 16. Build Logs

Build output should clearly show:

- detected game version
- selected locale
- validation results
- generated character count
- generated files
- patch status
- archive rebuild status
- final output path

Errors should explain what failed and how the user can fix it.

Avoid vague failures such as:

```text
Build failed.
```

Prefer:

```text
Unsupported executable version.
Expected SHA-256: ...
Found SHA-256: ...
```

---

# 17. Release Build

Document a dedicated release build command when appropriate.

Example:

```bash
python build.py release --locale <locale>
```

A release build may additionally:

- clean previous output
- run strict validation
- build optimized binaries
- generate checksums
- generate manifests
- copy documentation
- assemble installation instructions
- create an archive

The exact process should be reproducible.

---

# 18. GitHub Release Packaging

The source repository should normally contain:

- source code
- translation data
- build scripts
- documentation
- patches
- reproducible assets

GitHub Releases may contain:

- ready-to-use localization packages
- installers
- prebuilt redistributable tools
- large generated files
- optional media subtitle packages

Do not use the repository root as a storage area for release archives.

---

# 19. Clean Build Test

Before a major release, perform a clean build test.

Recommended procedure:

1. create a fresh clone in a new directory
2. do not copy any old build output
3. provide only documented original game files
4. install only documented dependencies
5. run the documented build command
6. compare the result with the expected release output

This test helps detect hidden dependencies on the developer's local environment.

---

# 20. Reproducibility Notes

Perfect byte-for-byte reproducibility may not always be possible.

Possible causes include:

- archive timestamps
- compiler version differences
- non-deterministic compression
- external proprietary tools
- media encoders
- file ordering

If output is not byte-identical, document what level of reproducibility is expected.

Examples:

- byte-identical output
- functionally identical output
- identical translation resources but different archive timestamps

Do not claim deterministic output unless it has been verified.

---

# 21. Troubleshooting

Document known build failures and solutions here or in:

```text
docs/PITFALLS.md
```

Typical issues include:

- incorrect game version
- missing dependencies
- wrong file paths
- encoding failures
- font coverage failures
- archive rebuild errors
- compiler architecture mismatch
- missing external tools
- antivirus interference
- path length problems

Important troubleshooting knowledge should not remain only in chat history.

---

# 22. Project-Specific Build Notes

Use this section for project-specific information that does not belong in the generic sections above.

Examples:

- required regional assets
- special disc extraction steps
- emulator-specific testing requirements
- console image rebuilding
- source-port dependencies
- unusual asset conversion steps

Remove unused template notes when adapting this document to a real project.

---

# 23. Final Build Standard

A mature project should make it possible for another developer to rebuild the localization using:

- a clean repository checkout
- documented dependencies
- documented original game files
- documented build commands

The build process should not depend on the original author's memory or private local environment.

## Experimental runtime diagnostic copies (2026-10-18)

These commands require locally supplied originals and an explicitly built native
LZX decoder (see docs/FONT_RESEARCH.md). They are not a release pipeline:

```powershell
python tools/decompress_package.py INPUT_PACKAGE --sha256 ORIGINAL_SHA256 --lzx-library PATH_TO_DECODER --output NEW_PACKAGE --report NEW_REPORT
python tools/launch_xenia.py --exe xenia/xenia_canary.exe --config xenia/xenia-canary.config.toml --game build/poc-game/disc1/default.xex --run-dir build/UNIQUE_RUN --keyboard-test-input --launch
```

`decompress_package.py` defaults to zero-padding to 32768 bytes, accepts only the
verified profile, preserves decoded object tables/payload and clears all three
compression states. `supplement_font.py --raw-atlas` is opt-in raw bulk output.
Neither command implies Chinese display or console compatibility. For table/TOC
updates and exact runtime boundaries see docs/RUNTIME_TEXT_BINDING.md. Keep all
originals and restore deployed resource copies before another control test.

### Existing-glyph binding probe

`tools/probe_font_mapping.py` is an opt-in same-size diagnostic for an existing
remap entry, not a font supplement or translation builder. Require the original
package hash, Font object path, codepoint and expected glyph. Never target an
unknown version. See docs/RUNTIME_TEXT_BINDING.md for the exact CLI shape and
negative-result boundaries; generated game packages remain local under build/.

### Duplicated geometry diagnostic

`probe_font_mapping.py --geometry` opts into same-size donor-metric copying in
both tagged/native records while preserving remap and texture bytes. Original
hash/mapping/donor bounds remain mandatory. Reports carry old/new patch bytes for
an independent inverse-copy check. See docs/FONT_REFERENCES.md; no diagnostic
candidate should be mistaken for Chinese display acceptance.


For embedded Font discovery, `tools/inspect_font_references.py --inventory`
accepts the same hash/decoder/output arguments as the default inspector and lists
Font/MultiFont class candidates without assuming a font-named package. It is
exclusive with `--object`. See docs/FONT_REFERENCES.md for the newly identified
MC2Game.xxx copy and its still-pending raw-package interactive control.
