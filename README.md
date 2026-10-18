# 《真名法典2》Xbox 360 简体中文汉化工程

目标语言 `zh-Hans`，保留原版 Xbox 360 游戏结构，以 Xenia 为首选验证环境。当前是**研究与工具初始化**，不是可安装汉化补丁；未开始批量剧情翻译。

- [当前进度](docs/STATUS.md)：里程碑、已验证与未知项。
- [字体绑定审计与双盘候选构建](docs/FONT_BINDING_AUDIT.md)：原型/CDO、forced-export 命名空间、4145 包类表调查及未部署的三别名对照/geometry 探针。
- [双盘版本与资源清单](docs/RESOURCE_SURVEY.md)、[FILEMAP](docs/FILEMAP.md)。
- [系列术语固定来源](docs/SERIES_TERMS.md)、[术语表](GLOSSARY.md)。
- [源值锁定与字面字体覆盖](docs/TEXT_FONT_COVERAGE.md)：版本化两字文本探针、双盘源/标记/逆向检查及全部显式字体覆盖；非游戏显示证明。
- [三别名最小补字可复现装配](docs/FONT_BUNDLE_BUILD.md)：双盘版本计划、源/语义指纹防护、原始对照和备份恢复检查；不部署。
- [两字补字原型](docs/FONT_SUPPLEMENT.md)、[纹理解析](docs/TEXTURE_RESEARCH.md)、[LZX 构建](docs/LZX_RESEARCH.md)。
- [字体结构研究](docs/FONT_RESEARCH.md)、[包表解析](docs/UE3_PACKAGE_RESEARCH.md)、[容器回写与原版基线](docs/COALESCED_REBUILD.md)。
- [当前 Coalesced 实测](docs/COALESCED_SURVEY.md)、[构建命令](BUILDING.md)、[来源与许可](NOTICE.md)。

```powershell
python -m unittest discover -s tests -v
python tools/check_repository.py
```

只读工具使用 Python 3.12+ 标准库；CI 使用自制样本，不需要游戏。原版资源、Xenia、本地规范与生成报告均不进入 Git。原生重编译路线已排除；不依赖 ReXGlue 或宿主运行时。

## 长期目标：双盘合一与单一启动

优先调查真正资源合一；分别验收单入口、单目录、单容器。自动换盘保留为备选，但尚无本作实际换盘通过证据。三个同路径冲突不自动覆盖；不修改原 ISO、不启动大型 XEX 改造，也不把合盘当作汉化前置条件。详见 [双盘技术研究与验收门槛](docs/MULTIDISC_RESEARCH.md)。

## 原始通用文档模板（保留规范）

下列通用示例不是已实现功能、安装步骤或兼容性承诺；当前事实以前述实测文档为准。

---

# Game Localization Project

This repository contains the source, translation data, tools, documentation, and reproducible build workflow for a game localization project.

Replace the placeholder sections in this template with project-specific information.

---

# Project

**Game:**  
**Localized title:**  
**Target locale:**  
**Platform:**  
**Supported version:**  
**Status:**  

Short project description:

> Describe what this localization covers, what version it targets, and whether it is complete, in progress, experimental, or maintenance-only.

---

# Download

Player-ready builds should be published through GitHub Releases whenever appropriate.

Example:

```text
Releases:
https://github.com/<owner>/<repository>/releases
```

Do not use the source repository root as a release-package storage area.

---

# What This Localization Includes

List the localized content.

Examples:

- menus
- UI
- dialogue
- subtitles
- item names
- item descriptions
- tutorials
- system messages
- credits
- pre-rendered video subtitles

Also list intentionally unsupported or incomplete areas.

---

# Supported Game Version

Document the exact supported version.

Example:

```text
Platform:
Region:
Distribution:
Game version:
Executable:
File size:
SHA-256:
```

Do not describe untested versions as supported.

For detailed build verification, see:

```text
BUILDING.md
```

---

# Installation

Provide player-facing installation instructions.

Keep this section short and practical.

Example:

1. Prepare a clean supported version of the game.
2. Download the latest localization release.
3. Extract the package into the game directory.
4. Follow any project-specific launcher or language-selection instructions.
5. Start the game.

If installation differs significantly by platform or version, document each case separately.

---

# Uninstallation

Explain how to remove the localization safely.

Document:

- files added
- files replaced
- backups created
- settings changed
- generated files

If restoring original files is required, state that clearly.

---

# Technical Overview

Briefly explain how the localization works.

Possible topics include:

- text extraction
- runtime text replacement
- archive rebuilding
- executable patching
- font replacement
- custom glyph rendering
- encoding conversion
- subtitle injection
- video subtitle generation

Keep this section high-level.

Detailed reverse-engineering notes belong in:

```text
TECHNICAL.md
```

---

# Repository Structure

Recommended high-level structure:

```text
README.md
BUILDING.md
TRANSLATING.md
TECHNICAL.md
LICENSING.md

docs/
  PITFALLS.md
  FILE_FORMATS.md
  KNOWN_ISSUES.md

locales/
  <locale>/

src/
tools/
tests/
assets/
```

Not every project needs every directory.

---

# Building From Source

This repository should support reproducible rebuilding whenever technically possible.

Typical workflow:

```text
clean repository checkout
+ user-supplied original game files
+ documented dependencies
→ build
→ validated localization output
```

See:

```text
BUILDING.md
```

for exact requirements and commands.

---

# Translation

Translation data should be structured and maintainable.

Preferred location:

```text
locales/<locale>/
```

See:

```text
TRANSLATING.md
```

for:

- translation format
- encoding rules
- placeholders
- control codes
- terminology
- line breaks
- length limits
- translation QA
- adding another locale

---

# Adding Another Language

When technically feasible, this project should allow other contributors to reuse the localization framework for additional locales.

Preferred structure:

```text
locales/
  zh-CN/
  zh-TW/
  ja-JP/
  ko-KR/
```

The exact supported locales depend on the game's engine, encoding system, font system, and current implementation.

If the technical framework can reasonably be generalized, prefer reusable localization infrastructure over one-language-only behavior.

---

# Known Issues

Player-visible limitations and compatibility problems are documented in:

```text
docs/KNOWN_ISSUES.md
```

Do not hide known limitations.

---

# Technical Research

Reverse-engineering findings and implementation details are documented in:

```text
TECHNICAL.md
docs/FILE_FORMATS.md
docs/PITFALLS.md
```

These documents should preserve both successful findings and meaningful failed approaches.

---

# Compatibility

Document compatibility with:

- game versions
- regions
- source ports
- modernizer patches
- mods
- emulators
- operating systems
- compatibility layers

If the localization uses a proxy DLL, runtime hook, or loader, document known conflicts.

---

# Development Status

Use this section to summarize the current state.

Example:

```text
Text extraction: complete
Font support: complete
UI translation: complete
Dialogue translation: in progress
Subtitle QA: in progress
Release packaging: complete
```

Keep status factual and current.

---

# Contributing

Contributions may include:

- translation improvements
- terminology review
- reverse-engineering research
- tool development
- compatibility testing
- bug reports
- documentation

Before contributing, read:

```text
TRANSLATING.md
TECHNICAL.md
LICENSING.md
```

Use issues or pull requests according to the project's workflow.

---

# Bug Reports

When reporting localization issues, provide as much of the following as possible:

- game version
- platform
- localization version
- locale
- level or scene
- screenshot
- exact text
- reproduction steps
- logs if available
- whether the issue occurs without the localization

This helps distinguish localization bugs from original-game or emulator issues.

---

# Licensing

This repository may contain material under multiple licenses.

Possible categories include:

- project-owned code
- translation text
- upstream source code
- third-party libraries
- fonts
- game source text
- game-derived resources

See:

```text
LICENSING.md
```

for the actual licensing boundaries.

Do not assume one license applies to every file.

---

# Copyright Notice

The original game, its source text, trademarks, characters, media, and other proprietary assets remain the property of their respective rights holders.

This project is an independent localization effort unless explicitly stated otherwise.

Do not include complete proprietary game files in the repository unless redistribution is explicitly permitted.

---

# Credits

Credit:

- original game developers and publishers
- upstream localization or reverse-engineering projects
- tool authors
- font authors
- translators
- testers
- contributors

Preserve upstream attribution requirements.

---

# Project Links

Replace these placeholders as needed.

```text
Repository:
https://github.com/<owner>/<repository>

Releases:
https://github.com/<owner>/<repository>/releases

Issue tracker:
https://github.com/<owner>/<repository>/issues

Project page:
<optional>
```

Remove unused links when adapting the template.

---

# Final Project Goal

The project should ideally allow:

- players to install a ready-to-use localization
- developers to rebuild the project from source
- translators to edit structured localization data
- researchers to understand the technical work
- maintainers to reproduce previous decisions
- future contributors to adapt the framework to another locale when feasible

The repository should preserve not only the finished translation, but also the knowledge required to maintain and extend it.
