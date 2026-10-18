# Hash-locked native image reconstruction — 2026-10-19

## Verified offline results

Both original XEX2 files reconstruct the **same20119552-byte native image**:

| Input | Original size | Original SHA-256 |
| --- | ---: | --- |
| Disc1 default.xex |19611648|`26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f`|
| Disc2 default.xex |19611648|`44976b6bf9f978312f14387ea4e60bbdfffd1a8aa72f31841f7a58ab2ebef586`|

The derived full-image SHA-256 is
`d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`.
Each disc was independently reconstructed with PyCryptodome3.23.0 and
cryptography46.0.3; all four outputs match byte for byte. An inverse extent walk
and re-encryption restored each original XEX byte for byte using its preserved
header, and the physical restored files were reopened/compared with the sources.

Disc2 was newly extracted with the existing read-only XDVDFS tool and matched
the previously independently inventoried file SHA. Its Media ID/disc number
remain4d4c6b53/2 versus Disc1's4c23be53/1; both Title IDs are4e4d0811.
**Common native-image bytes do not make the complete XEX files interchangeable.**
No source XEX, image, config, entry point, signature or installed game resource
was patched; no game/emulator, image or function was executed.

## Reproducible extraction

Core tools/default tests remain standard-library-only. Encrypted reconstruction
uses an explicitly selected optional backend:

```powershell
python -m pip install -r requirements-crypto.txt
python tools/extract_xex_image.py build/poc-game/disc1/default.xex --sha256 26146f0ceaeb1945bc8e0031d31bfd7fe929c85a6e9e0992aeaa823968c0750f --key retail --backend pycryptodome --output build/NEW-disc1-native.bin --report build/NEW-disc1-native.json --roundtrip-output build/NEW-disc1-restored.xex
```

Use a new output/report name with `--backend cryptography` and
`--image-sha256 d18d49fb2960426715ba17d61d069cce42b1eadac153af13c9395cd42b1773e9`
for the independent second backend. Disc2 uses its own source SHA above.
An optional original Disc2 extraction command is:

```powershell
python tools/disc_inventory.py "MagnaCarta II (Korea) (Disc 2).iso" --output build/NEW-disc2-selected.json --extract default.xex --extract-dir build/NEW-disc2-source
```

The XEX tool defaults to key selection none, not a guessed retail/devkit key.
Only encrypted inputs need a crypto dependency. Expected source hash and all
supported metadata/profile bounds are checked **before optional crypto import**.
Source/output/report/optional restored paths must be distinct and new; artifacts
are reopened and source snapshots checked before/after writing. Exit0 means
reconstruction, structural checks, inverse byte comparison and reopening passed;
exit2 means a failed guard. Reports retain executed=false.

## Supported storage/profile facts

This reader deliberately supports XEX2 title module flags1, reserved0,
encryption0/1 and compression none/basic0/1, not normal/LZX/delta/patch variants.
It validates optional-header uniqueness/bounds, required file-format metadata,
security/header overlap, execution ID bounds, image/load-base agreement,
page/type extents, block totals and encrypted alignment. Input/image bounds are
256MiB, optional headers4096, basic blocks65536 and pages4096. Unknown variants fail explicitly.

Actual file-format info at0x1f00 has size32, encryption1 and compression1.
The stored/zero basic extents are:

| Stored bytes | Following zero bytes |
| ---: | ---: |
|19038208|491520|
|32768|32768|
|524288|0|

Stored bytes total19595264, exactly the source payload after0x4000. Expanded
bytes total20119552, exactly the security image size0x1330000. The307 page
descriptors cover the same image. Adjacent type runs are read-only
[0,0x2d0000), code[0x2d0000,0xea0000), data[0xea0000,0x12b0000), then read-only
[0x12b0000,0x1330000), relative to base0x82000000.

The public platform key unwraps the16-byte session key using CBC with zero IV.
The concatenated stored payload is decrypted in one CBC stream; zero spans are
inserted **afterward**, not decrypted and not used to reset chaining. The inverse
walk verifies zero spans, removes them and re-encrypts the stored stream before
comparing the entire original container, including its preserved header.

This inverse proves byte restoration, **not RSA authentication or the meaning of
stored page digests**. A direct SHA-1-of-plaintext-64KiB-page hypothesis matched
0/307 stored digest fields and is explicitly rejected as a verified algorithm.
Both rsa_signature_verified and stored_page_digests_verified remain false.
Original expected SHA-256 is the version/content anchor used by these tools.

## PE annotation and analysis boundaries

The reconstructed image has MZ/PE signatures, machine01f2(PowerPCBE), optional
magic010b(PE32), base0x82000000 and entry0x82868ec0. COFF/optional header fields
are little-endian; code/data words and inspected wide strings are big-endian.
PE32 does not imply x86 or prove CPU register-width semantics.

These are **XEX virtual-image bytes, not a normal PE raw-file layout**. The old
PE .text raw pointer0x2c8c00 differs from its RVA0x2d0000. PE declared image size
0x1540800 differs from the XEX security image size; .reloc is not fully present
in the reconstructed XEX image. The tool annotates these fields without mapping
bytes through raw pointers or allocating the stale PE declared size.

REA rejected the original XEX format and then the genuinely reconstructed PE's
architecture; neither attempt opened a native session. No rename, architecture
spoofing, provider reconfiguration or target execution was used. Bounded local
Capstone5.0.8 big-endian PPC inspection produced plausible entry/code prologues,
but it is not a whole-image decompilation or call/renderer acceptance result.

Four full NUL-terminated wide names are present:
intUUIComp_DrawStringexecSetFont at RVA0x16d2a0,
intUUIComp_DrawStringexecDisableCustomFont0x16d440,
intUUIComp_DrawStringexecGetAppliedStringStyle0x16d560 and
intUUIComp_DrawStringexecGetFinalStringStyle0x16d5c0. Each has one aligned
big-endian pointer occurrence in data. These are **bounded name/reference leads,
not verified native function entry points**. Interior/suffix searches do not
establish function references, and a UTF-16LE ASCII-pattern match shifted by one
byte is not evidence for little-endian wide strings. Native registration and
the font override/measurement implementations still need tracing.

## Validation, hygiene and provenance

Twenty-two new standard-library fixture tests cover unencrypted none/basic
images, actual synthetic PE/XEX CLI inputs, every4096-byte header-prefix
truncation, bounds/overlaps/profile/hash guards, page/block totals, cipher call
contracts across basic extents, inverse failure, PE metadata/entry/machine,
source mutation, artifact paths and native-image signature detection. The cipher
test double is explicitly non-cryptographic; CI does not claim AES validation
without the optional libraries. Real AES evidence is the dual-backend four-run
comparison above. Full source regression438 ->460 -> isolated rollback438;
native-decoder-enabled460. Local evidence is under build/xex-native-verification/.

Generated XEX/native images stay ignored, never in Git. Repository hygiene now
also recognizes ELF/PE signatures in tracked files regardless of suffix, so a
forced add under a data-like filename is caught; the existing path-only API
remains available. Signature detection is repository hygiene, not a license
classification or a general executable-format validator.

Format research and the public platform key constant come from Ben Vanik and
Xenia contributors, BSD-3-Clause, fixed commit
`95a5c3ee250f80c3b9d139658649d9ffb6db3eec`:
[xex2_info.h](https://github.com/xenia-project/xenia/blob/95a5c3ee250f80c3b9d139658649d9ffb6db3eec/src/xenia/kernel/util/xex2_info.h),
[xex_module.cc](https://github.com/xenia-project/xenia/blob/95a5c3ee250f80c3b9d139658649d9ffb6db3eec/src/xenia/cpu/xex_module.cc).
Exact URLs/hashes are locked in references/xex-image-research.lock.json;
license text is retained at licenses/Xenia-BSD-3-Clause.txt. The Python format
implementation is independent; no emulator, SDK or runtime was integrated.
