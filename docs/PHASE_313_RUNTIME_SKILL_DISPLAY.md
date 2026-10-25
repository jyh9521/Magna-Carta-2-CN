# Phase313 - normal runtime skill display captions

## Verified source and semantic binding

The shipping `Data_Skill.xxx` contains620 `MC2SkillData` instances.117 instances declare a `SkillNameText` Strings reference and116 declare a `SkillNameDisplayTexture`;their108unique texture references include106 original `SkillName_Jpn` captions and2previously covered `UI_SkillName` images. The filename is not a language declaration:120of121original native sprites use Korean and1usesJapanese.

The106adopted image groups each pair the exact same object's display texture with its actual `SkillNameText` reference, exact current source field/hash and already adopted translation. No image-only guess is used.15unreferenced canonical sprites are retained unchanged. The unused old `UI_SkillName.Skill_Zephi_8` likewise remains original under the phase312 retention decision. Boss category wording stays English.

## Reproducible inputs

`locales/zh-Hans/candidate-decisions/runtime-skill-display-captions.json` records106consumer bindings,1143physical aliases and their original package/payload/tiled/native-pixel hashes. All canonical namespaces use the actual `SkillName_Jpn` package GUID; matching pixel data never merges namespaces.

The133additional original source rows are reproducibly materialized from user-supplied original disc inventories, not a private full game copy:

```powershell
python -m tools.materialize_resource_sources --descriptor locales/zh-Hans/source-resources/runtime-skill-display.json --inventory 1=build/disc1-hashed.json --inventory 2=build/disc2-hashed.json
```

The generic materializer verifies descriptor/inventory identity, original resource SHA256 and size, safe relative destinations, unique source selection, no disc substitution and no overwriting mismatched existing files. The descriptor contains133source rows corresponding to260physical disc resource instances. A second run verifies existing exact bytes without recopying them.

## Native image changes and exclusions

The native captions are transparent512x64 text-only sprites. Sparse old-glyph/shadow masks restore transparent RGBA and render the approved names; they do not place solid rectangles over artwork. All106actual writer outputs were visually reviewed. Alias locking covered302whole package instances and166distinct original package hashes, with1143exact namespace/native checks and no conflicts.

The cumulative plan becomes762image groups,1323rendering layers,3690physical aliases and475source rows. Its prior1217layers and prior656native outputs remain protected. All108tutorial embedded screenshots/illustrations remain original; none is reintroduced. Internal diagnostic text pictures retained by phase312 are unchanged.

## Validation and player boundary

Current root tests:2118. Full dual-disc bundle/composition/comparison/cold replay, actual native compatibility, isolated rollback, explicit enrollment plus hash-incremental refresh of the existing player copy, staged-source tests, commit identity and actual four CI logs are mandatory release gates. Their measured results live in the phase313 verification ledger; this design document is not a claim that a pending gate passed.

No Xenia/game execution, ISO build or full game-copy generation is part of this phase. Player in-game acceptance remains separate.
