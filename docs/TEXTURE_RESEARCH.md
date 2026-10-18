# Texture2D font atlas research — 2026-10-18

## Result and boundary

**Verified (static decoding):** all 35 Texture2D exports in the three original
font packages parse with complete export consumption. Each has one inline LZX
bulk mip, Format byte 7, and empty SourceArt. All 35 decompress successfully,
produce bounded Xbox360 untiled BC3 buffers, and generate local PNG previews.

Three previews were visually inspected: subtitle atlas 512×512 (coherent Latin
and Hangul glyphs); General_15 last atlas 512×64 (coherent Hangul rows); numerical
style atlas 256×64 (digits and punctuation). This verifies decoding for those
samples, not every glyph or runtime binding. No package/font/ISO was changed.

**High-confidence interpretation:** Format 7 is `PF_DXT5` / BC3; actual bulk size,
word-byte-swapped block decoding and readable output agree with UE3's format
ordering. **Unverified:** actual runtime sampler/layout behavior, remaining
preview images, lower packed mips, resource rebuilding and Chinese display.

## Source identity and reproducibility

Source bytes and hashes are unchanged from [FONT_RESEARCH.md](FONT_RESEARCH.md).

| Package | SHA-256 | Texture exports | Total decompressed tiled bytes |
|---|---|---:|---:|
| EngineFonts.xxx | `49e89e6c91ae4ead4297e10e44c3634e164a651f214c1a6eb3e161e3dd9ae5bc` | 5 | 753664 |
| font.xxx | `b9a476cc377fe54e04d574f66a2018f1a0b69138c9f25f696d46ef07b9b1a4e6` | 10 | 2424832 |
| font_ui.xxx | `5c0629a587b87fa54db57fdd3822fbab33315cc34e747545101505fb9dc1592f` | 20 | 720896 |

Ignored outputs:

- `build/texture-research/{EngineFonts,font,font_ui}.metadata.json`: framing only.
- `build/texture-research/{EngineFonts,font,font_ui}.decoded.json`: decoded hashes.
- `build/texture-research/{EngineFonts,font,font_ui}-previews/`: PNG assets, local only.

Example, using a **new** output path/directory:

```powershell
python tools/ue3_textures.py build/disc1-font-study/MC2Game/CookedXenon/font.xxx --output build/texture-research/font.decoded.json --lzx-library build/lzx/native-verified/ue3_lzx.dll --preview-dir build/texture-research/font-previews
python -m unittest discover -s tests -p test_ue3_textures.py -v
```

Metadata mode omits both `--lzx-library` and `--preview-dir`. Existing outputs
and preview directories are rejected. Python standard library suffices for
metadata, untile, BC3 and PNG logic. LZX uses the separately built optional
libmspack adapter, not a bundled proprietary codec.

The local adapter is libmspack commit
`55d501976171397ccd5d5a7a1ca7da065b1d9a06`, built by the table research task;
DLL SHA-256 `f16a0ef5dcac1f7ee8a9461f0cb02b7c0db06d48482d956a4317b9e285c0ffa1`.
Its source/build procedure and license remain separate from this MIT reader.
A new machine needs to reproduce that optional adapter before pixel decode;
this document does not imply the local DLL is distributed or sufficient build
infrastructure for releases.

## Verified byte layout: first subtitle texture

`font.xxx` export `EngineMedium_Subtitle.Texture2D_0`:
absolute serial offset **643869**, serial size **71942**.

| Relative offset | Field | Observed value |
|---:|---|---|
| 0 | net index i32 | 9 |
| 4–173 | tagged properties including terminal None | SizeX=512, SizeY=512, Format=7, MipTailBaseIdx=5 |
| 174 | SourceArt flags/count/disk size/data offset, four u32 | 0 / 0 / 0 / 644059 |
| 190 | mip count i32 | 1 |
| 194 | mip bulk flags/count/disk size/data offset | 0x40 / 262144 / 71724 / 644079 |
| 210 | compressed chunk header magic/blocksize/compressed total/uncompressed total | 0x9E2A83C1 / 131072 / 71692 / 262144 |
| 226 | first block compressed/uncompressed sizes | 33942 / 131072 |
| 234 | second block compressed/uncompressed sizes | 37750 / 131072 |
| 242 | first compressed block payload | 33942 bytes |
| 34184 | second compressed block payload | 37750 bytes |
| 71934 | native mip SizeX/SizeY | 512 / 512 |
| 71942 | export end | exact consumption |

The chunk compressed total excludes the chunk header and block-size table;
bulk disk size includes them. Each block contains Xbox LZX framing. The reader
validates magic, declared totals, exact block partition, decoder output length,
inline absolute pointers, dimensions and export termination. The supported
profile rejects external bulk references, nonempty SourceArt and unsupported
flags instead of guessing.

## Platform framing, pixels and original anomalies

Magna Carta's **bulk flag 0x40 denotes LZX through a game-specific remapping**.
Do not apply generic UE3 bulk flag interpretations blindly. This is explicitly
handled in UEViewer's MCARTA branch and corroborated by successful decoding.

BC3 operates on 4×4 blocks of 16 bytes. Actual buffers match dimensions aligned
to **128×128 pixels**, then Xbox tiled block addressing. The reader untile pass
swaps each two-byte word before standard BC3 decoding. For example, General_15's
512×64 atlas has 65536 stored tiled bytes (512×128 alignment), not 32768.

The 30 original glyph bounds anomalies described in FONT_RESEARCH remain
unresolved: physical aligned storage can exceed tagged dimensions, but that
alone does not establish how the runtime samples those glyphs. No dimensions
were enlarged and no original records were trimmed to make validation pass.

`texture-000-mip-00.png` for font.xxx has SHA-256
`476007caf34a0b326c76f0b9929f01b6d1b2ad61eff70c0e9f76e01a747f0d9b`.
This is a generated local original-game atlas preview, not a redistributable
font asset or Chinese proof of concept.

## Upstream attribution

Primary implementation references are Konstantin Nosov's
[UEViewer](https://github.com/gildor2/UEViewer), pinned commit
`a0bfb468d42be831b126632fd8a0ae6b3614f981`:

- [UnCoreSerialize.cpp](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnCoreSerialize.cpp): MCARTA flag remap and bulk framing.
- [UnTexture3.cpp](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealMaterial/UnTexture3.cpp): empty SourceArt followed by mip bulk and dimensions.
- [UnMaterial3.h](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealMaterial/UnMaterial3.h): original UE3 pixel format ordering.
- [UnTexture.cpp](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealMaterial/UnTexture.cpp): Xbox block address formula, format alignment and word byte swap. The address formula is ported with MIT notice retained inside `tools/ue3_textures.py`.
- [MIT license](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/LICENSE.txt), Copyright 2022 Konstantin Nosov.

Local upstream reference files are under `build/texture-research/upstream/`;
original research does not claim authorship of this platform layout.

## Validation and next gate

29 synthetic tests pass: framing/block totals and decoder-length rejection,
every-prefix truncation, source pointer/dimensions/termination guards, 128×128
block-address bijection, byte swapping, opaque/special-alpha BC3 cases and PNG
CRC/scanline checks. Supplement tests cover all 256 alpha values, exact inverse block scatter, untouched-buffer/block invariants and bounds rejection. All real sources still hash to their original identities.

Before a Chinese runtime PoC, identify **resident startup copies** and all
references: Startup_int includes Font.General_15 and Font.EngineMedium_Subtitle
copies, not merely standalone font.xxx. Patching only an unrelated standalone
package is not evidence of renderer binding. Texture support here is read-only;
a guarded package/TOC/font writer and original/modified/rollback runtime
acceptance remain separate gates.

## Minimal supplement placement: static geometry only

Parent requested a two-character supplement feasibility check. All 2608
General_15 glyph metrics were inspected; TextureIndex5 contains 42 records
(indices 2566–2607). Existing rectangles end at x=503, y=47 (exclusive maximum).
Two candidate **24×24** rectangles at **(420,24)** and **(448,24)** lie within
512×64 and overlap neither any existing glyph rectangle nor any 4×4 BC3 block
occupied by an existing glyph. They have block-aligned origins and dimensions;
this is stronger than choosing visually transparent pixels.

Reproduction evidence is
`build/texture-research/general-last-atlas-placement.json`, bound to the original
font.xxx SHA-256 and generated directly from the guarded parser. No glyph was
added. Atlas enlargement is unnecessary for this two-glyph geometry proposal.

The inverse texture operation is straightforward for these blocks: encode
linear little-endian BC3, swap each word, then scatter each block to
`xbox_tiled_block_offset(x_block,y_block,aligned_width/4)*16` in an original
**copy** of the decompressed tiled buffer. Touching only the selected blocks
preserves all existing glyph blocks and padding. White font raster coverage
can use constant white BC3 color and quantized alpha endpoints (255,0); quality
and baseline need actual visual acceptance. The module provides the in-memory encoder/scatter primitives below, but does
not alter font metrics, write packages, rewrite LZX or claim runtime glyph rendering.


### In-memory supplement APIs

- `encode_white_bc3_block(alpha16)` returns one 16-byte linear BC3 block.
- `scatter_linear_dxt5_cell(tiled,width,height,x,y,cell_width,cell_height,linear)`
  returns a new tiled buffer; only specified 4×4 blocks change.
- `supplement_white_dxt5_cell(tiled,width,height,x,y,cell_width,cell_height,alpha)`
  accepts row-major coverage bytes, encodes white RGB and scatters into a copy.

Both alpha endpoints 0/255 are exact; intermediate coverage error is at most
18/255. Cell origins and dimensions must be block-aligned and wholly inside
tagged dimensions. All other blocks, aligned padding and the input buffer are
preserved exactly. No package or disk file is modified by these primitives.

`parse_texture_payload` returns `(report, decoded_rgba_mips)`. In `report`,
`source_art` and each mip's `bulk` include export-relative `header_offset`,
`payload_offset`, `size_on_disk_field_offset` (+8), `data_offset_field_offset`
(+12); `data_offset` is package-absolute. Each mip has export-relative
`dimensions_offset`. Inner compressed chunk block offsets are chunk-relative.
A separate relayout writer must update these pointers/sizes if bytes move;
blind replacement of compressed payload length is not supported here.
