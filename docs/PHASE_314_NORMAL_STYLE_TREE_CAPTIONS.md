# Phase314: normal style-tree image captions

## Verified actual consumers and original coordinate defaults

Normal MC2UIScene_StyleTree scenes reference21used Style_Tree_Skill_Name_Jpn images through actual UIImage/UITexture ImageTexture fields or direct DamageUpgradeTex_Heal/Damage fields.96unique explicit sampled cells are bound to97UITexture references. Four bonus captions plus Holy Ripple/Aero Veil whole-image captions bring the batch to102owned glyph layers. The unused Ru_Skill_Sub1 image and3spare atlas cells remain original.

This is normal gameplay UI,not tutorial screenshots. All108tutorial illustrations remain original.

Coordinates are tagged FloatProperties inside the actual component's UIImageStyleOverride.TextureCoordinates,not guessed32pixel rows or texture-name conventions. Actual rows vary around31pixels;Juto uses two columns atU0/123. Native output glyph bounds are checked inside each actual sampled rectangle. Source block-aligned repair regions never overlap and clear only original glyph/shadow footprints,not a rectangle of background color.

Two single-caption components retain stale coordinates but no enabled override flag. Their complete original explicit archetype and flag-selected class-default chains were read. The actual Engine.UIRoot.UIImageStyleOverride serialized struct defaults explicitly store bOverrideCoordinates=False with a complete declaration chain and no missing slots. This is explicit original flag evidence,not an assumption that omitted values are zero. It establishes the original whole-image path for these single captions;no game execution is claimed.

## Language, namespace and inputs

The original96sampled skill names are bound to exact current adopted MC2Skill fields. OCR transcription errors were corrected by original native glyph review before selecting fields. Bonus captions use current terminology:伤害量,耐力消耗,使用KAN,恢复量. The21real encoded native images were visually reviewed. All84physical aliases retain canonical namespace GUID,whole-source/payload/native block/RGBA checks. Identical pixel data never merges namespaces.

Only one additional original resource path is required. Rebuild it from the user's verified original disc inventories with the generic source-subset tool:

```powershell
python -m tools.materialize_resource_sources --descriptor locales/zh-Hans/source-resources/normal-style-tree.json --inventory 1=build/disc1-hashed.json --inventory 2=build/disc2-hashed.json
```

At phase314 close the cumulative plan was783groups,1425layers,3774aliases,476source rows. The separately staged map work followed in phases315–316, not as tutorial work; the cumulative release and verification now live in `docs/PHASE_316_NORMAL_MAP_TERRAIN_CAPTIONS.md`.

## Release gates

## Independent lower-edge alpha audit

The final independent audit found 79 original nonzero-alpha pixels outside the
repair union in two used cells: Sere_Skill_Main00/cell067 had 67 pixels on
y=56..57 (maximum alpha 177); Sere_Skill_Sub/cell078 had 12 pixels on y=152
(maximum alpha 13). Rounded UV bounds and the initial block-aligned rectangles
had clipped these original glyph/shadow tails. The repair extends only the two
lower rectangle edges, retaining sparse original-alpha masks rather than filling
the background. The previous 762 images and the other 19 images in this batch remain protected. The corrected native replay and affected-package verification passed; the cumulative phase316 ledger records the test-copy refresh, isolated rollback and repository publication. No game/Xenia launch, ISO or full-game-copy build occurred.

## Final cumulative closeout (phase316)

The 21 style-tree groups/102 layers, 27 map-title groups/36 layers, and remaining map/room captions were built together. The final plan contains 832 image groups, 1560 layers, 3869 physical aliases and 518 source paths. Baseline 2124 tests and modified 2138 tests passed (one intentional skip each); dual-disc comparison packets and the existing phase313 test copy were hash-verified in phase316. See `docs/PHASE_316_NORMAL_MAP_TERRAIN_CAPTIONS.md` and its linked `VERIFICATION.txt`.
