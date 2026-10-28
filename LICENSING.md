# 当前项目许可边界（2026-10-18）

项目工具 MIT，原创新译文 CC BY-SA 4.0，见 LICENSE / LICENSE-translations.md。独立迁移工具来源与版权保留见 NOTICE.md。系列术语只读缓存保留上游许可和原文状态，不把系列关系待核词条标为本作定稿。

游戏镜像、XEX、UE3 包、原版文字全集、字体、音视频及 Xenia 本地二进制均不进入仓库。公开报告只包含结构、路径、散列和必要的短字段定位。所有完整提取结果位于忽略的 build/。

## 原始通用许可规范

---

# Licensing

This document describes the licensing boundaries of the localization project.

A game localization repository may contain multiple categories of material with different legal and licensing requirements.

Do not assume that one license automatically applies to every file in the repository.

---

# 1. Project-Owned Code and Tools

Original code written specifically for this project should use the license declared in the repository's main `LICENSE` file, unless a file or directory explicitly states otherwise.

Possible choices include:

- MIT
- MPL-2.0
- Apache-2.0
- GPL-compatible licenses where appropriate

The selected license should match the project's technical and upstream constraints.

Do not relicense upstream code incompatibly.

---

# 2. Translation Text

Original translation work may be licensed separately from program code.

A common option for translation data is:

```text
CC BY-SA 4.0
```

This allows reuse for:

- Traditional Chinese versions
- ports
- remasters
- additional platforms
- derivative localization projects

while requiring attribution and share-alike distribution.

If another license is used, document it explicitly.

---

# 3. Source-Language Game Text

Source-language text extracted from the original commercial game remains copyrighted by the original rights holders.

Including original strings in translation tables does not mean this project grants rights to those original strings.

Use original game text only to the extent reasonably necessary for:

- translation
- interoperability
- patch construction
- technical analysis
- context preservation

Do not treat original game text as project-owned material.

---

# 4. Original Game Assets

Unless redistribution is explicitly permitted, do not commit or redistribute complete proprietary game assets such as:

- executables
- ELF files
- DLLs
- full archives
- audio
- video
- textures
- models
- proprietary fonts
- complete original data directories

Users should normally provide their own legally obtained original game files.

---

# 5. Binary Patches and Transformation Data

Transformation data may be distributed when appropriate.

Examples include:

- xdelta patches
- IPS patches
- BPS patches
- byte-diff descriptions
- patch scripts
- build scripts
- binary patch manifests

Prefer distributing transformation data instead of complete modified proprietary binaries.

A patched full executable may still contain substantial copyrighted original code and should be treated accordingly.

---

# 6. Upstream Open-Source Code

Files derived from upstream open-source projects remain subject to their original licenses.

Document all upstream components.

Example:

| Component | Upstream | License |
|---|---|---|
| Runtime patch | project URL | MPL-2.0 |
| Archive library | project URL | MIT |
| Font | project URL | SIL OFL 1.1 |

Do not remove required copyright notices.

Do not relicense upstream code under incompatible terms.

---

# 7. Upstream EULA or Source-Available Code

Some projects expose source code under an EULA, source-available license, SDK agreement, or other non-open-source terms.

Such code may require separate treatment.

Document:

- source
- governing agreement
- redistribution limits
- modification limits
- whether derivative patches may be shared
- whether full modified source may be redistributed

Do not label such code as open source unless the license actually qualifies.

---

# 8. Fonts

Fonts must follow their own licenses.

Common examples include:

- SIL Open Font License 1.1
- Apache License 2.0
- other font-specific licenses

Do not copy proprietary operating-system fonts into the repository merely because they are installed locally.

If the build uses a system font, document that dependency.

Prefer redistributable open fonts when practical.

---

# 9. Third-Party Tools

External tools may have their own licenses and redistribution restrictions.

Document:

- tool name
- source
- version
- license
- whether the tool is bundled
- whether the user must obtain it separately

Do not redistribute third-party binaries without confirming permission.

---

# 10. Reverse-Engineering Notes

Original technical documentation written for this project may use the same license as project documentation or another explicitly declared license.

Examples include:

- format descriptions
- diagrams
- offset tables
- rendering notes
- reverse-engineering summaries
- implementation notes

Document factual discoveries without unnecessarily embedding copyrighted game content.

---

# 11. Generated Files

Generated output inherits licensing constraints from its inputs.

A generated file is not automatically freely redistributable merely because a project tool created it.

Examples:

- rebuilt archives may contain original copyrighted game assets
- patched executables still contain original executable code
- subtitled videos remain derivative works of original videos
- generated font atlases may include glyphs from third-party fonts

Treat generated files according to their actual contents.

---

# 12. Repository Source vs Release Artifacts

The Git repository should preferably contain:

- original project code
- scripts
- translation data
- patch definitions
- documentation
- legally redistributable assets

GitHub Releases may contain:

- ready-to-use patch packages
- installers
- redistributable prebuilt tools
- large generated artifacts
- optional subtitle packs

Release packaging does not override copyright or license restrictions.

---

# 13. Game-Derived Resources

Be cautious with files derived directly from original game assets.

Examples:

- edited textures
- modified videos
- rebuilt archives
- extracted fonts
- modified executable sections

If redistribution status is uncertain, prefer generating them locally from user-supplied originals.

Do not assume that changing an asset makes it freely redistributable.

---

# 14. Translation Licenses and Original Text

Translation files may contain both:

- original game text
- project-created target-language text

These two parts may have different legal status.

Where practical, document that:

- source-language text remains property of the original rights holders
- target-language translation is licensed by the translation contributors under the project's chosen translation license

A translation license does not grant rights over the original game text.

---

# 15. Contributor Licensing

If the project accepts contributions, make licensing expectations clear.

Contributors should understand that their contributions may be distributed under the licenses declared for the relevant part of the project.

If code and translation text use different licenses, document that distinction clearly.

---

# 16. Attribution

Preserve attribution for:

- upstream developers
- reverse-engineering researchers
- translation contributors
- font authors
- external tool authors
- original game developers and publishers

Recommended locations include:

```text
README.md
LICENSING.md
NOTICE.md
```

Do not remove legally required notices from upstream components.

---

# 17. Recommended License Split

A common project structure may use:

```text
LICENSE
```

for project-owned code and tools,

and:

```text
LICENSE-translations.md
```

for original translation work.

Example:

```text
Code and tools:
MIT

Original translation text:
CC BY-SA 4.0

Fonts:
their own licenses

Upstream code:
its original license

Game text and assets:
copyright remains with original rights holders
```

This is only a recommended pattern.

Actual licensing must follow the real upstream and project constraints.

---

# 18. Directory-Specific Licensing

Where different directories use different terms, document them explicitly.

Example:

```text
src/
  MIT

tools/
  MIT

locales/
  CC BY-SA 4.0 for original translation text

patches/upstream-engine/
  governed by upstream license or EULA

assets/fonts/
  governed by each font's license
```

Do not rely on contributors guessing which license applies.

---

# 19. License Files

Common files may include:

```text
LICENSE
LICENSE-translations.md
LICENSING.md
NOTICE.md
```

Their roles should be:

- `LICENSE` — formal license for project-owned code
- `LICENSE-translations.md` — formal license for original translation work
- `LICENSING.md` — explanation of licensing boundaries
- `NOTICE.md` — attribution and third-party notices where useful

Not every project needs all four, but the distinction should remain clear.

---

# 20. Uncertain Licensing Status

If the licensing status of a file or upstream component is uncertain:

- do not guess
- do not silently mark it as redistributable
- document the uncertainty
- avoid redistribution until clarified

Prefer omission over accidental unauthorized redistribution.

---

# 21. Project-Specific Licensing Notes

Use this section to record the actual licensing arrangement for the specific project.

Template:

```text
Project-owned code:
[license]

Project-owned translation:
[license]

Upstream project:
[name / URL / license]

Fonts:
[name / license]

Third-party tools:
[name / license]

Game source text:
copyright retained by original rights holders

Game assets:
not redistributed unless explicitly permitted
```

Replace this section with project-specific information when adapting the template.

---

# 22. Final Licensing Standard

A mature localization project should make it clear:

- what the project authors own
- what contributors may reuse
- what requires attribution
- what must remain under an upstream license
- what must not be redistributed
- what must be generated locally from original game files

If the licensing boundary is not obvious, document it explicitly.

## 2026-10-18 可选字体开发依赖

本地可选 LZX 动态库来自固定 libmspack，LGPL-2.1，未进入 Git；MIT 适配器与独立存储块写入器不改变该库许可。UEViewer tiling 函数的 MIT 完整声明保留于工具。Noto Sans CJK SC 字形源采用 OFL-1.1，许可与版本锁已保存；生成的补字数据不能笼统视为纯 MIT。完整原版字体/图集和补字后的完整游戏包均不公开分发，只在本地从原件构建。


## Native-image research follow-up

The public XEX platform constant/format research preserves Xenia BSD-3-Clause provenance in NOTICE.md and licenses/Xenia-BSD-3-Clause.txt. No Xenia runtime/SDK is integrated. Complete decoded PE/XEX images, restored original containers and native data/assembly reports remain local under ignored build/. A reconstructed native image is still game data, not a distributable localization source artifact. The Git hygiene check also inspects ELF/PE signatures independent of filename suffix.

CE/PPC packed-function format research additionally cites hedge-dev and
contributors / XenonRecomp (MIT), pinned in references/pdata-research.lock.json;
the upstream license is retained in licenses/XenonRecomp-MIT.md. The Python
reader is independent; no recompiler, SDK, runtime or complete game bytes are
redistributed. Local static instruction/metadata reports remain ignored.


## 2026-10-26 图片复审艺术字部件

`locales/zh-Hans/texture-overlays/artwork/review-v4/`保存三份本轮新生成的中文
艺术字透明部件与制作提示词，仅alpha字形供构建使用，不包含原游戏UI底图、
图标或完整源纹理。原图用作风格参照，不把整幅原图或生成整图放入仓库。
稀疏背景修复仍遵守既有游戏派生材料边界，不宣称被覆盖的原像素由项目拥有。

## 朱雀仿宋动态字库（阶段328）

沿用阶段326锁定的朱雀仿宋v0.212及OFL-1.1来源/许可，不提交完整TTF或游戏字体图集。
合成500使用原始Regular400轮廓作0.006em扩张；不修改字体内部名称/字重声明。
两个新增控制图修复PNG是既有稀疏修复块/蒙版的有界修订，不含完整游戏底图。
所有完整包、原图、字幕容器和测试ISO只保留在忽略的build/dist目录。
