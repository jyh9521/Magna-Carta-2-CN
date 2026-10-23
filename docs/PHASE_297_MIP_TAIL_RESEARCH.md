# UI_Battle_Master first-mip rejection resolved read-only

## Verified root cause

`build/phase-295-texture-layout/layout.py:39` rejects the complete serialized mip chain with `assert (mw,mh)==(max(1,w>>i),max(1,h>>i))`. All eight selected original exports serialize BC tail dimensions clamped at4 texels rather than1 texel: `(max(4,w>>i),max(4,h>>i))`. The first mip dimensions, flags, SourceArt pointer, physical payload pointers and export EOF are valid. The census therefore never reached its first-mip extraction, despite the first mip being independently decodable. This is not a missing natural-language font, unsupported pixel format or missing first-mip data.

- Exact original resource: `MC2Game/CookedXenon/UI_Battle_Master.xxx`.
- Original full SHA-256 `5c69d5105a7f392aec11a289847e5ffb002d2537d7bf21a4bea1af3825b5e3a2`; size`163840`. Both original ISO members were freshly read and rehashed; identity matches on disc1 and disc2.
- SourceArt header for every selected export: three zero uint32 fields followed by a pointer equal to export serial offset plus SourceArt header offset plus16. Actual values are recorded below and in JSON.
- All nonempty bulk records have flags`0x40` (LZX-compressed UE3 chunk). Every empty tail record has flags`0x21`, count0, size and pointer`0xFFFFFFFF`. Both formats are already supported decode formats:5=BC1/DXT1,7=BC3/DXT5.
- All serialized dimensions in all mip records exactly follow clamp4. This is an observed profile in these exact eight exports, not authorization to relax generic writers or infer arbitrary packages.

## Exact first failing assertions

| Export/object | Logical serial offset/size | Base dimensions/format | First offending mip | Header-relative offset | Stored dims / strict expected dims | Flags/count/size/pointer |
|---|---|---|---|---|---|---|
|27 `Tex.od_eff_aa01`|40615/5671|64×64 /7|5|5623 (absolute logical 46238)|4×4 /2×2|0x21/0/4294967295/4294967295|
|28 `Tex.od_eff_aa02`|46286/4279|64×64 /7|5|4231 (absolute logical 50517)|4×4 /2×2|0x21/0/4294967295/4294967295|
|29 `Tex.od_eff_aa03`|50565/6731|128×128 /5|6|6683 (absolute logical 57248)|4×4 /2×2|0x21/0/4294967295/4294967295|
|30 `Tex.od_eff_aa04`|57296/1493|16×128 /5|3|1373 (absolute logical 58669)|4×16 /2×16|0x21/0/4294967295/4294967295|
|31 `Tex.od_eff_aa05`|58789/9681|256×64 /5|5|9585 (absolute logical 68374)|8×4 /8×2|0x21/0/4294967295/4294967295|
|32 `Tex.od_eff_aa06`|68470/2551|128×32 /5|4|2455 (absolute logical 70925)|8×4 /8×2|0x21/0/4294967295/4294967295|
|39 `Tex.stagage_hline01`|84446/2581|32×128 /5|4|2485 (absolute logical 86931)|4×8 /2×8|0x21/0/4294967295/4294967295|
|40 `Tex.stagage_hline02`|87027/839|16×32 /5|3|767 (absolute logical 87794)|4×4 /2×4|0x21/0/4294967295/4294967295|

## Read-only first-mip decoding contract and limits

- The isolated helper reads exactly the original source selected member; it uses existing property parsing, UE3 LZX chunk decompression, frozen Xbox tiling/packed-origin mapping, endian conversion and BC decoder. It does not call a relaxed production `parse` or any write/repack function.
- The first-mip bulk dimensions equal SizeX/SizeY, flags equal0x40, source encoded SHA matches recorded bytes, pointer equals serial+payload offset, compressed output byte count equals expected count, every mapped block lies inside decompressed bytes, and identity scatter reproduces the full tiled first-mip buffer exactly (including padding). PNGs are reopened and RGBA hashes checked.
- Only independently stored first logical mips were decoded. Shared tails flagged0x21 were not decoded or assigned a physical owner. All-mip writer correctness, tail rendering and runtime behavior remain unverified. No production tooling checks changed.
- Visual inspection of all eight individual native PNGs shows vortex/glow/explosion/beam/lightning effect artwork, with no readable language captions in these first-mip pixels. This finding is based on actual decoded pixels, not object names. It does not assert the complete UI_Battle_Master package or other mips lack text.

| Export | First bulk header/payload offsets | Compressed size → tiled bytes | Storage dims / packed block origin / mapped max end | Original export payload SHA-256 | First-mip RGBA SHA-256 |
|---|---|---|---|---|---|
|27|311/327|3542→16384|[128, 128] /[0, 0] /14336|`cad9964a3e212bc9e6ebadf990002fb03e14ff46fe2ef55bd74b8df86f8135dc`|`49b99d2f442a322ca8e3931fe12b34942326f0a4eb8347b923eb40edf41b08c5`|
|28|311/327|2408→16384|[128, 128] /[0, 0] /14336|`83e949574911c1934284b1de495023dc279f3125d0e29f874394aacc6a4864a0`|`e5df7b4122e2f1c262808751ef65482271b178e60ee8d18227d64799f29a7941`|
|29|311/327|4042→8192|[128, 128] /[0, 0] /8192|`20816449e3eaba16755a74249bebf253dacab13945fccac7d9fa13772c2005e8`|`db70d1c7b0377f6b11222e7ae0d770c5424ec8455573c45ca0966333597b740c`|
|30|283/299|1018→8192|[128, 128] /[4, 0] /8128|`03df3f2224315d8ea2576a4554a60791b7c509e57ca01223ad3ac460800cff05`|`62dd1a04a613e8208c366807d8151bdb8a1f7fda3d9e2755cc8c5eb9334fbb93`|
|31|261/277|6590→16384|[256, 128] /[0, 0] /14336|`6926f5e12687b7bf3a269f3fa5fd421d0118f217acbe077dbdca879e3baa7189`|`6dd05c52d838f777d9b1e62cac35ad060a0752d6d88af882175a58f2915af756`|
|32|261/277|1410→8192|[128, 128] /[0, 0] /2048|`740f01d6427ce0f210df5e22fee763b5d5b66d5427af298570c9d620e18d96c4`|`08c7be28d1c92569190bee1b9974bae37f89157041ce2029370aa7dcfa349fea`|
|39|315/331|1380→8192|[128, 128] /[0, 0] /8128|`cda3dfbf15bf40df7fec1d4b90f5d1585d7aa36df1c25517c5fa35b782ede8e7`|`34387d2fa12179ab0e19373a175fa8164f8543406e335e5380d2187158f1b7b4`|
|40|287/303|408→8192|[128, 128] /[4, 0] /1856|`0ee9a9c3dc1a5d600755820be837485bf1089cbed4395b12ce2799ffeb65efb4`|`95abeea34b67e7bbc5efbbb353654e14d523e65bbdb21b1f067707a58c2e4f77`|

## Native first-mip pixels

### Export27 `Tex.od_eff_aa01`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-27-first-mip.png)

### Export28 `Tex.od_eff_aa02`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-28-first-mip.png)

### Export29 `Tex.od_eff_aa03`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-29-first-mip.png)

### Export30 `Tex.od_eff_aa04`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-30-first-mip.png)

### Export31 `Tex.od_eff_aa05`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-31-first-mip.png)

### Export32 `Tex.od_eff_aa06`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-32-first-mip.png)

### Export39 `Tex.stagage_hline01`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-39-first-mip.png)

### Export40 `Tex.stagage_hline02`
![Original decoded first mip](C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-readonly\export-40-first-mip.png)

## Reproduction and evidence identity

- Full source fields and every mip flags/count/size/pointer/dimensions/encoded SHA, plus tiled/linear/RGBA/PNG hashes: `C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\battle-master-profile-fields.json`, SHA-256`55e9a08c44ad48e2a52e1e80db811e0e259bc98514c87d8f1979d5e9145bf371`.
- Isolated helper: `C:\Users\noway\Downloads\Magna-Carta-2-CN\build\phase-297-ui-census\decode_battle_master_readonly.py`, SHA-256`28e1d31f7610be23e4c82ac86ef4e69eb293abff73223e33c0d42d3e581606b1`.
- Command: `python build/phase-297-ui-census/decode_battle_master_readonly.py`.
- Final literal output: `PASS8strictfirstmips;clamp4tailmetadata;freshdualdiscSHA;originalunchanged`; exit status0. An earlier helper run accidentally selected the first disc2 manifest member due to a shadowed generator variable; the assertion rejected it. The corrected helper selects matching resource path and freshly verifies both discs. No original or canonical output was written by either attempt.
- These evidence files and all eight PNGs were reopened. Canonical/tracked tools, title cohort, title aliases and original inputs remain unchanged.
