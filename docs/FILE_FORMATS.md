# File Formats

## Property container declaration tails (2026-10-19)

For the source-locked446/25 big-endian metadata profile, ArrayProperty adds one
int32 property-definition reference after the common declaration header;
MapProperty adds key/value int32 references. Font's map stores0/0 and remains
opaque. Nonnull types are exact local/owned Core property exports, not guessed
native element widths. These tails are declarations, not Array/Map value data.
See FONT_DECLARATIONS.md for scope, guards and complete Font source findings.

## Native metric glyph records versus stored Font records (2026-10-19)

The source-locked metric code computes a20-byte runtime record stride, reads
width/height-like words at+8/+C and a texture-index byte at+10. Existing Font
serialization still stores17 bytes per native glyph entry. The code's map-like
entry stride is8, next-link word+0/key-u16+4/value-u16+6. These observations do not
prove the serialized/native layout bridge or change the file writer. See
TEXT_MEASUREMENT_PATH.md for exact branches, hashes and limits.

## Initialized Font/Canvas native rows (2026-10-19)

For the hash-locked reconstructed PPC image, the Font/MultiFont/Canvas tables
store big-endian u32 name-address/code-address pairs (8 bytes), followed by an
8-byte zero sentinel. Their complete native scopes have2/1/10 rows. Function
native tokens live in the separate Engine declaration metadata, not an invented
third table word. This format is distinct from the earlier cold12-byte UI
descriptor profile. Coordinates are virtual-image addresses, not PE raw file
offsets; names/code words and .pdata-declared entries do not prove live dispatch.
See INITIALIZED_NATIVE_TABLES.md for source/plan/report hashes and reproduction.

## Cooked namespace metadata (2026-10-19)

For this profile, export flag bit0 (value1, EF_ForcedExport) identifies forced
exports. An outermost exported Package provides their uncooked namespace name
and GUID; standalone objects use the physical package's summary GUID and label.
Matching path/class/GUID is namespace-candidate evidence, not loaded-instance
precedence. Three General_15 representations have identical full normalized
glyph/remap/decoded-atlas data despite different table-local payload bytes.
See FONT_BINDING_AUDIT.md for hash-locked sources, complete-disc scope and limits.

## Verified 446/25 UI serialization (2026-10-18)

The component template header precedes NetIndex: class defaults use 4 bytes,
ordinary component instances 8, components under a class-default outer chain 16.
Flags are serialized LO u32 then HO u32; ClassDefaultObject is HO 0x200.
STYLE_ID is four tagged IntProperty A/B/C/D values. UIStyle's native tail holds
an int32 count followed by state/style-data int32-reference pairs. Full schema,
guards, offsets, fixed source references and coverage: UI_STYLE_GRAPH.md.

This document records reverse-engineered file formats used by the localization project.

Use this file for concrete binary or structured format documentation such as headers, offsets, field sizes, alignment, compression, checksums, string tables, pointer tables, and archive metadata.

High-level implementation notes belong in `TECHNICAL.md`.

---

# 1. Documentation Rules

For every documented format, include as much of the following as known:

- filename or extension
- purpose
- platform
- endianness
- magic
- version
- header size
- entry count
- offsets
- lengths
- alignment
- compression
- checksum behavior
- string encoding
- pointer tables
- filename tables
- secondary manifests
- unknown fields
- parser or builder implementation
- confidence level

Important claims should be classified as:

- Verified
- High-confidence deduction
- Unverified hypothesis

Do not assign meanings to unknown fields without evidence.

---

# 2. Format Entry Template

Use this template when documenting a new format.

```markdown
## FORMAT_NAME

**Purpose:**
Describe what the file stores.

**Platform:**
Describe where it is used.

**Status:**
Verified / High-confidence / Unverified

**Known files:**
- example.ext
- another.ext

**Endianness:**
Little-endian / Big-endian / Mixed / Unknown

**Encoding:**
ASCII / UTF-8 / UTF-16 / CP932 / CP936 / CP949 / Custom / Unknown

**Magic:**
`XX XX XX XX`

**Header size:**
`0x00`

**Alignment:**
4 bytes / 16 bytes / 0x800 bytes / Unknown

**Compression:**
None / algorithm / Unknown

**Structure:**

| Offset | Size | Type | Meaning | Status |
|---|---:|---|---|---|
| 0x00 | 4 | u32 | magic | Verified |
| 0x04 | 4 | u32 | entry count | Verified |

**Entry structure:**

| Offset | Size | Type | Meaning | Status |
|---|---:|---|---|---|
| 0x00 | 4 | u32 | data offset | Verified |
| 0x04 | 4 | u32 | data length | Verified |

**Notes:**
Additional behavior.

**Unknown fields:**
- offset 0x10
- offset 0x14

**Tools:**
- `tools/extract_format.py`
- `tools/build_format.py`
```

---

# 3. Integer Types

Use consistent notation.

Recommended types:

```text
u8
s8
u16
s16
u32
s32
u64
s64
f32
f64
char[n]
bytes[n]
```

If a field uses fixed-point representation, document it explicitly.

Examples:

```text
u16 8.8 fixed-point
s32 16.16 fixed-point
```

---

# 4. Endianness

Always document endianness where binary integer fields are involved.

Possible values:

- little-endian
- big-endian
- mixed-endian
- platform-native
- unknown

Do not infer endianness solely from the platform if the format has not been verified.

---

# 5. Offsets

For every offset, specify what it is relative to.

Possible bases include:

- file start
- current structure start
- current entry start
- data section start
- archive start
- decompressed block start

Example:

```text
string_offset:
u32 little-endian
relative to the beginning of the string table
```

Do not write only "offset" when the base is ambiguous.

---

# 6. Length Fields

Document what each length represents.

Possible meanings:

- byte length
- character count
- code-unit count
- glyph count
- compressed size
- decompressed size
- aligned size
- size including terminator
- size excluding terminator

Example:

```text
text_length:
number of encoded bytes
does not include trailing 0x00
```

This distinction is especially important for multibyte localization.

---

# 7. Alignment

Document alignment rules precisely.

Examples:

```text
entries aligned to 4 bytes
payloads aligned to 0x10 bytes
files aligned to 0x800-byte sectors
```

Record whether padding bytes are:

- zero
- 0xFF
- preserved from original
- ignored
- unknown

Incorrect alignment may break loading even when offsets appear valid.

---

# 8. String Storage

Document how strings are represented.

Possible forms:

- null-terminated
- fixed-width field
- offset + length
- string-table index
- pointer
- inline script token
- compressed string block
- glyph index stream

Record:

- encoding
- terminator
- length semantics
- alignment
- duplicate-string behavior
- whether empty strings are allowed

---

# 9. String Tables

If the format uses a string table, document:

- table start
- entry count
- indexing method
- duplicate handling
- encoding
- alignment
- offset base
- whether strings are sorted

Example:

```text
entry.name_offset
→ relative to string_table_start
→ null-terminated CP932
```

---

# 10. Pointer Tables

If pointer-like values exist, determine whether they are:

- file offsets
- virtual addresses
- relative offsets
- indexes
- sector numbers
- runtime pointers

Do not assume an integer that increases monotonically is a file offset without verification.

---

# 11. Record Arrays

For fixed-size record arrays, document:

- record size
- record count
- padding
- field order
- unused slots

Example:

```text
record_size = 0x20
record_count = header.entry_count
```

If the final record differs from the others, note it explicitly.

---

# 12. Variable-Length Records

For variable-length records, document how boundaries are determined.

Possible methods:

- length prefix
- next offset
- terminator
- sentinel value
- block table
- parser state machine

If malformed input causes unsafe reads, document the failure behavior.

---

# 13. Archive Formats

For archives, document at minimum:

- file count
- TOC location
- filename table
- data offsets
- file lengths
- alignment
- compression
- ordering
- checksums
- secondary metadata

Also determine whether the game relies on:

- an external index
- a size manifest
- hash table
- path database
- fixed file ordering

Do not assume rebuilding the primary archive alone is sufficient.

---

# 14. Secondary Metadata

Some formats use metadata outside the main container.

Examples:

- size manifests
- lookup indexes
- filename hashes
- dependency tables
- scene indexes

Document these relationships explicitly.

Example:

```text
DATA.AFS
↔ DATA_INDEX.BIN
```

If both must be updated together, record the dependency in `TECHNICAL.md` as well.

---

# 15. Compression

Document compression behavior.

Include:

- algorithm
- header
- block size
- compression flags
- decompressed size
- recompression requirements
- tool compatibility

If decompression is understood but compression is not, state that clearly.

Do not describe a format as "supported" if only extraction works.

---

# 16. Checksums

Document checksums and hashes.

Possible algorithms include:

- CRC16
- CRC32
- Adler-32
- MD5
- SHA variants
- custom hash
- rolling checksum

Record:

- covered byte range
- stored location
- byte order
- initialization value
- final XOR
- whether padding is included

If the algorithm is unknown, preserve the field and mark it unknown.

---

# 17. Filename Hashes

If filenames are hashed, document:

- normalization
- case handling
- slash direction
- encoding
- hash algorithm
- collision behavior

Example:

```text
input:
lowercase ASCII path with backslashes

algorithm:
FNV-1a 32-bit
```

Do not infer a hash algorithm from a small number of examples.

---

# 18. Compression Flags

If entries use flags, document each verified bit separately.

Example:

| Bit | Meaning | Status |
|---:|---|---|
| 0 | compressed | Verified |
| 1 | encrypted | Unverified |
| 2 | streaming | High-confidence |

Do not assign meanings to unknown bits.

---

# 19. Script Formats

For script-like formats, document:

- opcode size
- argument encoding
- string references
- jump targets
- labels
- control flow
- embedded text
- variable references

Translation tools must distinguish text from executable script logic.

Do not rewrite script tokens as natural-language text.

---

# 20. Font Formats

For font resources, document:

- texture format
- atlas dimensions
- glyph order
- character map
- width table
- metrics
- baseline
- line height
- fallback glyph
- maximum glyph count

If the font system spans multiple files, document the relationship.

---

# 21. Texture Formats

If localization requires editing textures, document:

- dimensions
- pixel format
- palette
- swizzling
- alpha format
- mipmaps
- container header
- alignment

If standard formats are embedded inside custom containers, note both layers.

---

# 22. Subtitle Formats

For subtitle resources, document:

- timing units
- time base
- line structure
- text encoding
- speaker metadata
- style metadata
- line-count limits

If timing is frame-based, document frame rate assumptions.

---

# 23. Video Containers

If localization requires video processing, document:

- container type
- video codec
- audio codec
- subtitle handling
- multiplexing behavior
- alignment
- platform-specific constraints

Do not confuse container format with codec format.

---

# 24. Audio Formats

If text references audio assets, document relevant metadata such as:

- event ID
- filename mapping
- index tables
- sample rate
- codec
- channel count

Do not translate internal audio identifiers unless verified safe.

---

# 25. Save Formats

If localization touches save-related data, document:

- text fields
- identifiers
- checksums
- version fields
- string encoding

Visible names may also be logic identifiers.

Do not modify save structures without understanding compatibility impact.

---

# 26. Executable Data Tables

If strings or font tables are embedded in executables, document:

- file offset
- RVA
- virtual address
- section name
- record size
- relocation behavior

Clearly distinguish:

```text
file offset
RVA
runtime virtual address
```

Do not mix these concepts.

---

# 27. Sector-Based Formats

Console formats may use sector-relative addressing.

Document:

- sector size
- base sector
- offset calculation
- padding
- filesystem relationship

Examples:

```text
sector size = 0x800
byte_offset = sector_index * 0x800
```

Verify rather than assume.

---

# 28. Platform Notes

Record platform-specific format behavior.

Examples:

- PS2 DMA alignment
- little-endian MIPS data
- Xbox sector alignment
- PC filesystem paths
- console disc image constraints

Keep platform assumptions separate from format facts.

---

# 29. Unknown Fields

Unknown fields should remain visible in documentation.

Example:

| Offset | Size | Meaning |
|---|---:|---|
| 0x10 | 4 | unknown |

Do not delete unknown fields from diagrams just because the current tooling preserves them.

Preserving unknown bytes may be necessary for safe rebuilding.

---

# 30. Rebuild Strategy

For each format, state whether the project uses:

- in-place patching
- full rebuild
- append-and-repoint
- block replacement
- archive reconstruction
- runtime override

Document why the chosen strategy is safe.

---

# 31. Round-Trip Testing

Where possible, test:

```text
original file
→ extract
→ rebuild without modification
→ compare
```

Possible outcomes:

- byte-identical
- structurally equivalent
- functionally equivalent
- not yet reproducible

Document the expected level.

A non-byte-identical rebuild may still be valid if differences are understood.

---

# 32. Sample Data

Use minimal samples where legally and practically appropriate.

Prefer:

- synthetic examples
- short byte sequences
- structure diagrams
- tiny excerpts

Avoid embedding substantial copyrighted game content.

---

# 33. Parser Safety

Custom parsers should validate:

- file size
- header bounds
- entry count sanity
- offsets within file
- lengths within bounds
- integer overflow
- truncated data
- malformed records

Do not trust game files blindly.

---

# 34. Builder Safety

Custom builders should validate:

- encoded string lengths
- alignment
- offset range
- checksum generation
- required metadata
- entry count
- output size

Fail clearly rather than generating ambiguous broken files.

---

# 35. Version Differences

If format behavior differs between game versions or regions, document each variant separately.

Example:

```text
US version:
record size = 0x20

JP version:
record size = 0x24
```

Do not merge incompatible variants into one undocumented assumption.

---

# 36. Tool Mapping

For each documented format, list the tools that operate on it.

Example:

```text
Format:
SCRIPT.BIN

Extractor:
tools/extract_script.py

Builder:
tools/build_script.py

Validator:
tools/validate_script.py
```

This makes technical documentation directly actionable.

---

# 37. Open Questions

Keep unresolved format questions visible.

Example:

```text
- Unknown meaning of header field 0x18.
- Entry flag bit 2 may control streaming.
- Final 4 bytes may be a checksum.
```

Do not erase unanswered questions when the current implementation works.

---

# 38. Project-Specific Formats

Add actual game-specific format documentation below this line.

Remove unused template examples when adapting the file to a real project.

---

# 39. Final File Format Standard

A mature format document should allow another developer to understand:

- how the file is structured
- which fields are verified
- how text is stored
- how offsets and lengths work
- how alignment works
- which metadata must be updated
- how to extract and rebuild the file
- which parts remain unknown

The goal is to preserve enough knowledge that future localization work does not require repeating the same binary-format reverse engineering.


## 2026-10-18 当前实测索引

XDVDFS / XEX2：见 RESOURCE_SURVEY.md；Coalesced：见 COALESCED_SURVEY.md。二者为本轮真实字节验证，前文模板示例不是本作格式。

## Font / Texture / Stored LZX 新增实测

Font tagged/native双份指标和remap见FONT_RESEARCH.md；Texture2D的MCARTA LZX flag0x40与resident raw0变体、Xbox BC3布局见TEXTURE_RESEARCH.md及FONT_SUPPLEMENT.md；stored LZX帧及第三方decoder验证见LZX_STORED_RESEARCH.md。均为固定源字节/本地工具验证，不代替游戏显示证明。


## Source-hash edit manifest (tool schema1, not a game binary format)

Coalesced change plans retain the literal source mode and add explicit
source_mode=sha256-utf8 with entries id/source_sha256/translation. The source hash
covers exact extracted value UTF-8 bytes; whole input_sha256 locks the serialized
container independently. No normalization or implicit mode fallback is permitted.
See TEXT_FONT_COVERAGE.md for fields, example workflow and verification limits.


## Offline candidate assembly metadata (tool schema1)

Candidate plan references exact font/text plan bytes plus every expected Font,
text and TOC binary hash. Output manifest uses relative resource/report paths
for candidate, original-control and backup-restored copies. It is not an
installer format or a game archive. See LOCALE_CANDIDATE.md for the contract and
which original/raster/runtime properties are actually checked.


## 446/25 ScriptStruct/UProperty/UEnum metadata

Native serialized metadata layouts, explicit persistent defaults, inherited Guid
schemas and scoped property references are documented in STRUCT_DEFAULTS.md.
This profile retains zero editor header fields and no script bytes. BoolProperty
size0 stores its value in the tag header: logical bool-word and empty-payload
offsets differ by4. These are logical serialization offsets, not runtime member
or native bool-bit offsets. Unknown layouts fail instead of scanning for tags.


## 446/25 native Function declarations and parameter stubs

See FUNCTION_METADATA.md for retained Line/TextPos/FriendlyName fields, native token/flags and exact `(NativeParm + i32 reference)* Nothing EndOfScript` stub recognition. This is a bounded native-only subset, not general bytecode or executable decompilation. UIComp_DrawString has18 recognized methods and5 explicit non-native unparsed records; unknown tokens are rejected. Shared declaration-chain validation retains all parameter/return types and checks owned reference order.


## Opt-in 446/25 scripted UI wrapper subset

SCRIPTED_UI_LAYOUT.md records the bounded grammar and exact5-body/736-byte/242-token result. StructMember retains property/struct references and copy/modification bytes; inherited owner ancestry is checked. Static arrays retain enum/type identity, not runtime index proof. Default/Skip spans and forward statement targets are checked; Context raw skip5 is preserved without VM-meaning inference. Core.Object numeric operator declarations are scoped/unique, not executable registrations. This is not a general VM or bytecode dialect claim.


## XEX2 none/basic offline image profile

NATIVE_IMAGE.md records the hash-locked dual-disc originals, exact basic stored/zero extents and common virtual-image identity. XEX/security fields are big-endian, reconstructed PE metadata little-endian and native code/data words big-endian. CBC spans the concatenated stored data; zero extents are inserted afterward. PE raw pointers/declared image size are annotations, not remapping instructions. Stored page extents are checked; RSA/page-digest authentication remains unverified.


## Hash-locked PPC native row12 cold-initializer profile

NATIVE_BINDINGS.md records18 rows (name pointer +8-byte descriptor), zero sentinel, typed Engine metadata identity, bounded constant/symbolic-stack def-use recovery and exact lookup structure. Descriptor code words and zero adjustment words are recovered without modifying image bytes. Native object-relative0xd8/0xe4 word operations and packed mask0x20000000 are distinct from serialized tagged properties; semantic field labels are high-confidence deductions, not complete struct/runtime layout proof.

## CE/PPC exception-directory and guarded style profile

NATIVE_STYLE_SELECTION.md records the PE little-endian directory3/virtual .pdata
contract and big-endian8-byte CE records. Packed prologue8/function-length22
fields count four-byte words; two raw flags are retained without unwind claims.
All44484 records are checked, not silently skipped by flag. Exact declared ends
and absent leaf entries remain distinct from next-start guesses and runtime code
coverage. The opt-in style profile verifies four code windows and the font
bit/nonzero-pointer guards before the unique output+0x20 store.

## Native class-name/table opt-in profile

NATIVE_CLASS_TABLES.md records full UTF-16BE U-prefixed names with the verified
name+2 call operand, bounded16-word registration/21-word leaf templates and
81-word .rdata table windows. Shared callback/table aliases preserve separate
class names. Slot128 points to a checked61-word getter; slot124's result selects
entry+E8 vs the pointer loaded at entry+28 plus174. These are static operands,
not serialized offsets or active runtime field values. Table window size and
leaf BLR boundaries do not imply full table/function extent.

## Object-initialization static contract

OBJECT_INITIALIZATION.md records metadata size+50/callback+11C word transfers,
checked save/base/constructor helpers, the metadata table's slot120 size getter,
selected wrapper/allocator sites, and the40-word zero-fill template. Its integer
geometry uses prefix/16-byte blocks/4-byte words/tail partitions, not memory or
CPU execution. Wrapper/allocation whole-function hashes and declared extents
are distinct from their partially checked instruction windows; later call
effects and callback-entry/render values remain unverified.

## Source-hash prefix Coalesced edits (schema1)

Explicit source_mode=sha256-utf8-prefix uses id/source_sha256,
source_prefix_codepoints/replacement/preserve_utf16_units and optional exact
selector(embedded_path/section/key/occurrence). The source hash covers the whole
unmodified UTF-8 value; replacement operates at Unicode codepoint boundaries,
with a separately typed UTF-16-unit length guard. Protected-token splits and
content/order changes fail. Resolved output retains the exact suffix; reports
record selector/unit counts/suffix hash, not original text. Literal/full-value
hash modes are unchanged for valid inputs. See LOGIN_PROBE.md.
