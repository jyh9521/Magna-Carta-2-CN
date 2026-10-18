# UI component prefix and warning style graph — 2026-10-18

## Verified offline result (not runtime acceptance)

Two TitleMap labels explicitly serialize
`<Strings:MC2UI_TCR.GameStart.LogIn_NewGame>` inside DataSource.MarkupString.
Both lead through renderer, style ID, six states and nested text-style objects
to Startup_int's resident General_15. This is a complete **serialized candidate
chain**, not proof of the active label/skin/state, linker resolution or drawing.
All game tests remain with the user. Nothing was launched or deployed.

## Component prefix

The previously unexplained bytes are **before NetIndex**, not padding after it.
The supported big-endian 446/25 profile has these branches:

| Object | Serialized prefix | Tagged offset |
|---|---|---:|
| Class-default object itself | int32 NetIndex | 4 |
| Ordinary Component | int32 TemplateOwnerClass, int32 NetIndex | 8 |
| Component inside a class-default outer chain | int32 TemplateOwnerClass, FName TemplateName, int32 NetIndex | 16 |

Class inheritance must reach Core.Component through explicitly supplied package
tables. The reader does not infer components from name suffixes or search for
plausible tag starts. TemplateOwnerClass must be Class/null; FName indices,
payload bounds, import/export class identity, duplicate paths and class/outer
cycles are guarded. Numbered template FNames retain their number. HasStack
prefixes are explicitly unsupported rather than guessed.

**Source basis:** Eliot van Uytfanghe's MIT Unreal-Library, fixed commit
`8236c39b79e30887a487ecf9b018204e430a5ebc`:
[UObject routing](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UObject.cs),
[version conditions](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Branch/PackageObjectLegacyVersion.cs).
See references/ui-style-research.lock.json for six source hashes. The Python
implementation is independent; no upstream runtime/source is integrated.

**Independent byte verification:** preserved object_flags contains **LO u32,
then HO u32**. ClassDefaultObject is HO bit 0x200. Thus
`0007000400000200` is class-default. Treating the eight bytes as one big-endian
uint64 and applying a conventional high-word flag mask gives the wrong result.

## Nested structures and StateMap

Known tagged structs: UIDataStoreBinding, UIStyleReference, StyleDataReference,
STYLE_ID and UITextStyleOverride. Each must consume its entire bounded value.
Unknown native structs/arrays remain opaque. Fields retain full property/index
paths and logical package offsets. Duplicate/indexed singular fields fail rather
than choosing one silently. Depth/property-count limits bound nested parsing.

STYLE_ID contains four tagged IntProperty fields A/B/C/D; it is **not raw GUID
bytes**. ID matching retains every supplied candidate, never choosing a skin by
filename or load order. Explicit override fields are reported; effective inherited
overrides are not inferred.

After UIStyle's tagged block, StateMap is an int32 count followed by int32
state/object pairs. The entire native tail, non-null unique state references,
reference bounds and UIStyle_Data targets are checked. All **109 non-default
Startup_int UIStyle objects / 614 state entries** pass, with zero errors.
The corresponding engine metadata is export20194, `UIStyle.StateDataMap`,
class Core.MapProperty. The shorter name StateMap is used by this report/tool.

## Exact warning chain

All offsets are logical decoded-package offsets, not compressed file positions.

1. TitleMap_MSPT exports **1151 / 1164** are
   `UI_GameStart.Scenes.Scene_GameStart.BoxPanel_0.Confirm_Box_0.Ask_0` and
   `...BoxPanel_5.Confirm_Box_5.Ask_5`. Their nested MarkupString FString values
   start at **1787800 / 1797830** and name the same localization key.
2. StringRenderComponent references exports **2191 / 2204**, UIComp_DrawString
   objects with **8-byte** prefixes.
3. StringStyle.AssignedStyleID is
   **9fe5e7d1-481e0c9d-c03b5f9f-40f3726d** in both renderers.
4. The supplied package index matches Startup_int export **3635**,
   `style_ui.Base.GeneralFont`. No duplicate ID appears in these four supplied
   packages; this is not a global loaded-object uniqueness claim.
5. Enabled/Active/Disabled/Focused/Pressed/TargetedTab StateMap records point to
   Combo exports **1813, 3738–3742**.
6. TextStyle.CustomStyleData points to Text exports **4300–4305**. Each explicitly
   serializes StyleFont -> Startup_int export **21, Font.General_15**.

Two labels yield **12 state-specific serialized paths**. These paths need no
inherited StyleFont value. Renderer customizations found here concern alignment,
not an explicit font override. Active widget/skin/state, inherited overrides,
dynamic changes and forced-export/linker precedence remain **Unverified**.
Earlier negative/inconclusive experiments are not converted into positive
runtime binding or Chinese rendering acceptance by these static findings.

## Broader regression

All 62 historically requested packages were re-read with original SHA256 guards
and explicit Engine/MC2Game/Startup_int class contexts; hashes stayed unchanged.

| Primary | Selected/parsed UI exports | offset4 | offset8 | offset16 |
|---|---:|---:|---:|---:|
| Engine | 152/152 | 60 | 0 | 92 |
| MC2Game | 13924/13924 | 4589 | 9176 | 159 |
| Startup_int | 994/994 | 994 | 0 | 0 |
| TitleMap_MSPT | 1209/1209 | 480 | 729 | 0 |
| Total | **16279/16279** | **6123** | **9905** | **251** |

**1327 class-resolution gaps** are listed separately; they are not failed UI
payloads. Unclassified objects and unrequested packages are not covered by the
zero selected-UI-parse-failure claim. Only TitleMap yields this warning token in
parsed UI fields. Reports remain local in build/ui-style-verification/deep-scan/.

## Reproduction and identities

New report destinations are required. Zero CLI exit means a report completed,
not full coverage or runtime success. Inspect classification_errors, unparsed,
style_errors and each match's unresolved list. Legacy UIStyle scanning is
unchanged without --deep; the three new arguments require deep mode.

```powershell
python tools/inspect_ui_fonts.py build/poc-game/disc1/MC2Game/CookedXenon/TitleMap_MSPT.xxx --sha256 e094df8399beac753e07a1ee388d5192b8f0a721fa854d786104de7439e98395 --deep --text-token LogIn_NewGame --reference-package Engine build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --reference-package MC2Game build/poc-game/disc1/MC2Game/CookedXenon/MC2Game.xxx 13f92622e2ae2920f6ce6dfc7b0edbbcbec7e83adeacbd56fed84a021739a641 --reference-package Startup_int build/poc-game/disc1/MC2Game/CookedXenon/Startup_int.xxx be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-warning-style-graph.json
python -m unittest discover -s tests -p 'test_ui_style*.py' -v
```

## Undeployed font-reference diagnostic

probe_ui_style_font.py selects an exact UIStyle on a hash-verified uncompressed
copy, validates every state's direct text chain and old font, then changes only
its four-byte StyleFont references to another existing local Font. It rejects
compressed inputs, null/inherited style data, cross-package patch fields,
duplicate paths, same-font requests, hash mismatches and existing/aliased output.
Reparsed object tables remain identical; fields and both outputs are reopened;
report-driven inverse restoration must reproduce the entire source buffer.

GeneralFont's six fields change **21 -> 20**, General_15 -> EngineMedium_Subtitle.
Only six actual bytes differ inside the six four-byte fields. Text, StateMap,
atlases, remaps, metrics, all other exports and total package size stay unchanged.
This is a diagnostic, not translation or a promise of a specific visible effect.

| Local output | Size | SHA256 |
|---|---:|---|
| Startup_int.raw.xxx (control) | 12845056 | 290f24985c8bbcf62f07fe8605e8ba2ff23c4f8d89140bb15f648e3e56b8f904 |
| Startup_int.style-font-probe.xxx | 12845056 | 67070d6537cfb598201a05758d3456c24326d9e9612fc69b02eac7f084643257 |
| Xbox360TOC.raw-style-probe.txt | 197990 | 5de894537c630dc8ed9bdee4837041584d65e217de3dc860adc6c5559c39c644 |

The control uses existing decompress_package.py with the original Startup hash
above. The shared TOC candidate changes only Startup_int's first size field
**1769472 -> 12845056**, using original TOC SHA256
`04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab`.
Both variants have the same size. TOC paths/sectors/other columns/CRLF stay
unchanged; inverse recovery equals the original. No generated game resource is
committed or distributed.

Rebuild the control and TOC as separate new outputs (from the repository root):

```powershell
python tools/decompress_package.py build/poc-game/disc1/MC2Game/CookedXenon/Startup_int.xxx --sha256 be264d1397e7fca36b5098e1f2b6ee4f8001f7a7216268bcf2c65edcd8de82c3 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-Startup_int.raw.xxx --report build/NEW-raw-control.json
'[{"path":"..\\MC2Game\\CookedXenon\\Startup_int.xxx","expected_size":1769472,"new_size":12845056}]' | Set-Content -Encoding utf8NoBOM build/NEW-toc-changes.json
python tools/update_resource_sizes.py build/poc-game/disc1/MC2Game/Xbox360TOC.txt --sha256 04f504dba0b7d74be0ffccbc0ce0d8ecf7f2dd1dc99af4273be5bb162ff8c9ab --changes build/NEW-toc-changes.json --output build/NEW-Xbox360TOC.txt
```

Use the newly generated raw path in the font-probe command below. These commands
generate local research outputs only; they do not install them.

```powershell
python tools/probe_ui_style_font.py build/ui-style-verification/Startup_int.raw.xxx --sha256 290f24985c8bbcf62f07fe8605e8ba2ff23c4f8d89140bb15f648e3e56b8f904 --style-object style_ui.Base.GeneralFont --expected-font Font.General_15 --target-font Font.EngineMedium_Subtitle --reference-package Engine build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-style-probe.xxx --report build/NEW-style-probe.json
```

Original/raw-control/probe graphs each retain two text matches and twelve paths;
only the final font target changes in the probe. Independent binary inverse
recovery equals the raw control hash. This is not game compatibility, visible
font change or visual rollback acceptance. All deployed resources remain original.

Next offline work: inherited customizations and linker/import object resolution.
The user's separate game gates remain same-warning control/probe/original
recovery and minimal Chinese display, before bulk translation.

Validation checkpoint: baseline 268 tests passed (one optional native skip);
25 new synthetic tests cover prefix routes, exact nested offsets, numbered
FNames, LO/HO flags, class/import/outer guards, exhaustive template truncation,
bounded recursion, malformed IDs/maps, duplicate/indexed fields, font-reference
patch/inverse and CLI guards. Modified 293 tests passed (one optional skip),
and all 293 passed with the explicitly selected native decoder. None execute
game code. Independent source rollback restores the prior 268-test behavior.
