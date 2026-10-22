# Phase 292 — Front menu, party names, guest and disc image labels

## Scope and primary evidence

This research resolves all **14 requested original images**, not only the easier twelve. It does not edit a locale plan or original package, launch a game, or claim runtime acceptance. Reproducible evidence is `build/phase-292-label-mapping/map.py`, `mapping.json`, `input-lock.json`, and `verification.log`. The script reopens each original package, decodes each selected export, and requires exact equality with its original PNG before recording hashes. All fourteen were viewed individually at native size; title and guest were also viewed on a 4× gray composite to expose alpha edges.

Primary sources are the user-supplied original `build/poc-game/disc1/MC2Game/CookedXenon/{UI_GameStart,UI_Battle_08_Jp,UI_Pillar_Title}.xxx`; original Coalesced INT/JPN and hashed per-disc manifests; adopted translation batches; final `locales/zh-Hans/display-fix.json`; and `README.md`. The mapping contains complete resource/payload/RGBA/PNG hashes and stable field IDs. Original assets and previews stay in ignored build output.

## Atlas rectangles — half-open [x,y,width,height], aligned to 4 pixels

These are **pixel/block replacement cells established from the decoded atlas**, not an assertion that every runtime DrawTile UV call has been recovered.

`UI_GameStart` export 14 (`Menu_tex`, 256×256):

| Original | Target | Normal | Hover |
|---|---|---|---|
| New Game | 新游戏 | [0,0,120,28] | [124,0,120,28] |
| Load Game | 读取游戏 | [0,28,120,32] | [124,28,120,32] |
| Option | 选项 | [0,112,120,32] | [124,112,120,32] |
| Extra | 附加内容 | [0,144,120,28] | [124,144,120,28] |
| Movie | 影片 | [0,172,120,32] | [124,172,120,32] |
| Live Drama | 语音剧 | [0,204,120,32] | [124,204,120,32] |

Normal text is white with black edge; hover text has red-orange glow. Both states must be replaced, using the same adopted phrase. New Game is a new-game action, so 新游戏 avoids losing the contrast with Load Game. Extra/Movie/Live Drama reuse the actual corresponding GameStart fields. **Final display overrides take precedence over the cumulative draft**: the latter still says 短剧 in places, whereas display-fix says 语音剧 and 附加内容. Each applicable evidence record includes both adopted draft and final override.

The Korean title reads **마그나카르타2**, not a character name or story-world title. Replace [0,60,124,32] with **真名法典2**, following repository branding in README and final GameStart display overrides. Do not regress to the older 玛格纳卡尔塔2 draft. Protect the entire aligned copyright row **[0,92,256,20]** exactly: visible © SOFTMAX CO., LTD. © 2009 NBGI. Never redraw, translate, or remove it. The y91 neighboring low-alpha filtering abuts the old title and copyright region; do not claim that a larger arbitrary margin is unmodified. All guaranteed copyright blocks start at y92; output inspection must confirm the complete readable copyright is preserved.

Export 15 (`Menu_tex_Back`, 256×32) has Back in normal/hover states. Render 返回 in [0,0,120,32] and [124,0,120,32]. Export 16 (`Press_Start_1`, 256×32) reads Press START Button. Render **按START键** in [0,0,256,32], retaining the controller's START identifier rather than translating that button to an ambiguous Chinese name.

## Eight party-name textures

`UI_Battle_08_Jp` has four normal/red pairs, each 128×32; replace the full [0,0,128,32] cell. Each Japanese reading was independently viewed, so the decision does not rely on its English object variable.

| Exports normal/red | Original | Target | Original INT key |
|---|---|---|---|
| 27 / 28 | アルゴ | 阿尔戈 | MC2CharacterName Default.Argo |
| 30 / 31 | セレスティン | 塞蕾丝汀 | MC2CharacterName Default.Celestin |
| 33 / 34 | ジュト | 朱特 | MC2CharacterName Default.Juto |
| 35 / 36 | ゼフィ | 洁菲 | MC2CharacterName Default.Zephi |

The map records exact stable IDs, source hashes, matching adopted batches and same-key Japanese primary fields. White and red output states must remain distinct; the red-state glyphs must not silently become white.

## Guest means a temporary party member

`UI_Pillar_Title` export 4 is GUEST (64×32), cyan/white. Use the short tag **临时** in [0,0,64,24], expanded meaning **临时同伴**, not 访客.

Verified primary semantic evidence includes MC2UI System_Log.JoinGuest/LeaveGuest; tutorial field `coalesced:1f8ccc923cfb01f332b7fd0059a11016afea0804f39d195106b587a68cd6f218` explicitly labels 临时同伴（GUEST）参战, and its paired explanation says temporary companions fight automatically and lack some normal party functions. Final display-fix preserves that meaning. The cooked package table also contains MC2UIDefinition.PartyCharacter.bGuest, Storage_CharInfo.bGuest, MC2Pawn.IsGuestPawn and MC2SaveData.PlayerPartyInfo.IsGuestPawn, recorded in the mapping. This is party terminology, not a platform login guest.

**High-confidence deduction:** this standalone GUEST badge uses the same party meaning. The exact texture-to-widget consumer was not recovered in this research. Do not relabel that missing binding as verified runtime behavior.

## Both disc badges are included

`UI_Pillar_Title` exports 2 and 3 are DISC 1 / DISC 2 (64×64). They combine a disc illustration with text, rather than being opaque textual identifiers that must stay English. Render **第1盘 / 第2盘** into **[0,36,64,28]**, suggested font size 16 with offset_y −3. Protect **[0,0,64,36]** exactly. The lower disc illustration overlaps the replacement region, so claim only exact upper-disc preservation, never that the entire original disc drawing survives. Inspect decoded candidate previews before adoption for fit, recognizable disc silhouette and unambiguous 1/2 distinction. The shared Chinese prefix/suffix does not remove or redraw a platform trademark.

## Reproduction and result

```powershell
$env:PYTHONIOENCODING='utf-8'
python build/phase-292-label-mapping/map.py
```

Observed exit 0: `{"images": 14, "menu_images": 3, "party_name_images": 8, "guest_images": 1, "disc_images": 2}`; `PASS 14 original exports decoded and PNG hashes matched; original/adopted source hash and batch matches verified; input hashes unchanged; no game launch`.

All four research artifacts were reopened after generation. Coordinates and semantic decisions are ready for the main implementation; no claim here replaces the candidate alias scan, encoding proof, actual protected-region hashes, dual-disc packet validation, isolated rollback, live incremental refresh, or eventual manual game testing.

## 实施后的坐标裁决

实际采用见[回填文档](PHASE_292_FRONT_PARTY_ADOPTION.md)：Guest全64×32、Disc默认居中无需offset_y、28高菜单16号字；其余证据与原保护区不变。
