# Phase 293 — Complete monster/name-source mapping, 199 + 117 = 316 rows

## Scope and observed result

This frozen research visually reviews **all199 originals** in UI_Monster_Name_Jpn and merges the117 Monster_Name originals from UI_Name_Jpn. These are316 source rows, not316 different pixel classes or316 already accepted game screens. Original hash-locked packages were read only; all316 selected exports were independently decoded, and their original payload and PNG hashes matched the existing source previews. The four sheet files retain the visual-review entry points; single native-size images were opened for ambiguous glyphs and ornamental title boundaries.

`mapping.json` contains per source row: package/resource/export/object/dimensions, original resource and payload hashes, preview path+SHA256, exact visible original string, normalized reading, selected Chinese translation, original style description and RGBA rendering suggestion, 4-aligned edit rectangle, font-size suggestion, protected wing rectangles, source/adopted evidence, classification and explicit old117 correspondence. `readings.json` records every199-string visual transcription. It does not use English object leaves as name evidence.

Observed summary:

{
  "total_source_rows": 316,
  "new_package_rows": 199,
  "old_package_monster_rows": 117,
  "unique_readings": 169,
  "exact_pixel_old_alias_new_rows": 125,
  "same_leaf_different_source_groups": 22,
  "translation_conflicts": {},
  "transcription_corrections": 2,
  "unclear_glyph_holds": 0
}

All199 images have legible source glyphs; no unresolved illegible-character hold remains. New opaque names are explicit consistent transliterations of readable primary pixels, not claims of official names. Ordinary body-part/monster/NPC/object descriptions are directly translated. Candidate font/style settings are implementation suggestions; encoded-preview tuning and game acceptance remain the main task's work.

## Two corrections to the earlier117 transcription

- UI_Name_Jpn export27 is **휴아렌의 팔**, not 휴아렌의 칼. Native-size image confirms 팔 (arm). New UI_Monster export39 shares the visible reading. Both select **修亚伦的手臂**.
- UI_Name_Jpn export67 is **겔피쉬**, not 젤피쉬. Both old67 and new105 select **格尔鱼**. Old66/new104 read 젤피쉬 and retain **水母**. A similar first syllable is not permission to merge the creatures.

The previous frozen research files remain unchanged. New rows carry explicit correction records, so future reconstruction can distinguish a corrected observation from an original-source mutation.

## Do not bind names by leaf or English variable

The audit finds22 reviewed same-leaf groups with different visible source readings. Examples:

- New export68 `Boss_Name_Big.Boss_Ch11_Melissa` visibly reads **푸 르 손**, selecting **普尔森**, not 梅莉莎. The English variable is misleading.
- New `Mname_51` reads **에브흐러스**, selecting **埃布赫鲁斯**; the old same leaf reads 콜러서스 and selects 巨像.
- Old/new `Mname_22` differ: 네코잭 versus 검은 네코네코. They select 猫杰克 versus 黑猫猫.
- Old/new `Mname_24` differ: 아오네코 versus 푸른 네코. Both select 青猫 semantically, but they are not asserted to be pixel aliases.
- New `Senti_208` reads 로얄가드, **皇家卫兵**. Old Senti_208 reads 가디언 알가트, **守护者阿尔加特**. No leaf-based overwrite is allowed.

125 new-package rows have an exact decoded RGBA match among the old117; other same-reading relationships are separately recorded. `same_leaf_different_sources` lists22 reviewed discrepancies after the independent erratum. Exact pixels establish aliases; same text alone does not prove equal resources, visual placement, object identity or runtime load routes.

## Translation consistency and primary adopted terms

169 normalized visible readings receive one Chinese output each; the repeated-reading conflict audit is empty. Exact matching ignores whitespace only, preserving all original spellings and raw source hashes. Existing adopted INT/JPN fields and final display overrides take priority over earlier provisional image candidates. Matching existing character names reuse their source IDs and adopted batch records. Existing phase291 applied-image terms are explicitly cited where available, rather than manufacturing missing INT entries.

Important consistent components:

- 높새바람섬 → 风息岛, with original MC2CharacterName village-role fields as primary adopted component evidence. New export10 **높새바람섬 간호사 → 风息岛护士**; the old UI_Name export10 has the same readable wording and may reuse this decision.
- 트레와 → 特雷瓦; 푸른 달 트레와 → 青月特雷瓦. Armor/dark/leader variants preserve that base.
- 벨포트 → 贝尔福特; 듀난 → 杜南, with adopted role/quest-field evidence.
- 주토 → 朱特; 휴아렌 → 修亚伦. Body parts and psychological states retain the same character name.
- 칸 → **KAN**, following exact adopted field `coalesced:d8ab492a1cd0d180dec3cef4c33b7c9ead279c9fd88ae111ec69aa9211c4fc11`; 칸 이터 → KAN吞噬者, not an invented new Chinese base-energy term.
- 북부군 연환술사 and elemental variants use 连环术师 consistently, not alternating 师/士.
- New readable proper names include 普尔森/普尔森·斯莱德, 斯特拉斯 and its left/right hands, 埃布赫鲁斯, 尤尼翁, 加里翁. These are newly reviewed image transliterations, not existing INT or official-name assertions.

`새도우` is recorded exactly as printed and interpreted as the shadow loan-name 暗影. The report does not silently respell the original to a more conventional Korean spelling. Creature names with semantically opaque phonemes remain transliterated instead of inventing species lore.

## Twelve large Boss title images — retain wings

All12 are512×64 with different wing positions; one universal central crop would damage at least some decorations. Alpha-column runs were inspected and native images opened. Exact authorized rectangles:

- 66 레카스 → 雷卡斯: [180, 0, 152, 64]; protected [[0, 0, 180, 64], [332, 0, 180, 64]]
- 67 조 파 → 乔帕: [200, 0, 116, 64]; protected [[0, 0, 200, 64], [316, 0, 196, 64]]
- 68 푸 르 손 → 普尔森: [176, 0, 160, 64]; protected [[0, 0, 176, 64], [336, 0, 176, 64]]
- 69 알 렉 스 → 亚历克斯: [176, 0, 160, 64]; protected [[0, 0, 176, 64], [336, 0, 176, 64]]
- 70 라 우 드 → 劳德: [176, 0, 160, 64]; protected [[0, 0, 176, 64], [336, 0, 176, 64]]
- 71 아스모데우스 → 阿斯莫德乌斯: [140, 0, 232, 64]; protected [[0, 0, 140, 64], [372, 0, 140, 64]]
- 72 폭주 주토 → 暴走朱特: [168, 0, 176, 64]; protected [[0, 0, 168, 64], [344, 0, 168, 64]]
- 73 벨 제 붑 → 别西卜: [176, 0, 160, 64]; protected [[0, 0, 176, 64], [336, 0, 176, 64]]
- 74 자이언트 모스 → 巨蛾: [132, 0, 248, 64]; protected [[0, 0, 132, 64], [380, 0, 132, 64]]
- 75 인페르노 → 因费尔诺: [164, 0, 184, 64]; protected [[0, 0, 164, 64], [348, 0, 164, 64]]
- 76 매드 골렘 → 狂暴魔像: [164, 0, 192, 64]; protected [[0, 0, 164, 64], [356, 0, 156, 64]]
- 77 스웜프 일 → 沼泽鳗: [164, 0, 192, 64]; protected [[0, 0, 164, 64], [356, 0, 156, 64]]

Each rectangle is4-pixel aligned, ends in clear gaps before the ornamental wing, and has exact left/right protected rectangles. The main implementation must independently validate protected block/pixel hashes after BC3 encoding, rather than accepting a visual impression. All other image cells are128×32 and allow a full4-aligned cell replacement. NPC labels preserve green-white coloring; ordinary enemy labels preserve pale red/white text with red/dark edge; large titles remain white with a dark edge. Final font sizing is deliberately left to actual encoded previews.

## Reproduction and freeze

```powershell
$env:PYTHONIOENCODING='utf-8'
python build/phase-293-monster-mapping/map.py
```

Observed exit0: `PASS316 original source rows decoded; 199 new originals individually visually reviewed; PNG and payload hashes matched; source-name Chinese conflicts0; all inputs rehashed unchanged; no source write/game launch`.

All JSON/script/log/research files were reopened after generation and all input-lock hashes were rechecked. Writes occur only in ignored build/phase-293-monster-mapping. No tracked file, locale plan, source tool, original asset or runtime was changed; no commit or game launch occurred. The complete316-row decision table is frozen for actual adoption by the main task. These source candidates do not replace dual-disc alias completeness, encoding proofs, packet verification, isolated rollback, existing-test-copy incremental refresh, or manual game testing.

Implementation and independent glyph errata: see PHASE_293_MONSTER_PARTY_ADOPTION.md and the committed candidate-decisions data. Earlier frozen readouts are historical evidence, not a reason to retain corrected errors.

## Independent implementation review errata

UI_Name132 is 로얄가드 → 皇家卫兵, identical RGBA to new140/206. UI_Name120 reads 데스발리스타 → 死亡弩炮, identical RGBA to new192. The frozen working report originally had two conflicting RGBA classes; committed adoption applies both independent errata, and the conflict count is zero. This brings four source-glyph corrections in total including the prior27/67 corrections. The historical23 same-leaf discrepancy claim includes a mistaken Senti208 split; current reviewed discrepancy count is22. No complete original file was changed.
