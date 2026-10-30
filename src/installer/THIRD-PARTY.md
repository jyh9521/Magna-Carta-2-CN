# Installer components

The toolchain revisions and supplied LOGO SHA256 are pinned in toolchain.lock.json.
The release contains deltas, not complete game executables, archives or DLC.
The supplied branding artwork remains separate from the project's MIT code license.

| Component | Author / source | Terms |
|---|---|---|
| Flutter / Dart | Google and contributors, https://github.com/flutter/flutter | BSD; engine dependency notices included |
| Material Icons | Google | Apache 2.0, included |
| Python | Python Software Foundation | PSF and bundled licenses, included |
| PyInstaller bootloader | PyInstaller contributors | GPL with bootloader exception, included |
| ZArchive 0.1.3 | Exzap, https://github.com/Exzap/ZArchive | MIT-0; SHA256 public domain |
| Zstandard 1.5.7 | Meta Platforms and contributors, https://github.com/facebook/zstd | BSD option, included |
| libmspack | Stuart Caie and contributors, https://github.com/kyz/libmspack | LGPL 2.1; corresponding complete source ZIP included |
| MSVC CRT | Microsoft Corporation | Visual Studio redistributable code; app-local DLLs |

MSVC distribution / maintenance:
https://learn.microsoft.com/en-us/cpp/windows/choosing-a-deployment-method?view=msvc-170
https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution
The app-local CRT is not installed globally; keep it updated when rebuilding releases.

## Replace or rebuild the LGPL decoder

The decoder is dynamically loaded, not statically linked into the installer.
Extract libmspack-source.zip into a new `libmspack-source` directory beside this file.
In an x64 Native Tools Command Prompt, compile the included bridge with:

```bat
cl /nologo /LD /O2 /Ilibmspack-source\libmspack\mspack lzx_bridge.c libmspack-source\libmspack\mspack\lzxd.c /link /OUT:ue3_lzx.dll
```

You may modify this library and debug modifications. The release integrity checks
are not a license restriction: for a modified build, replace patch/tools/ue3_lzx.dll,
update its SHA256 in patch/manifest.json, calculate the new manifest SHA256, and
run `python -m tools.package_installer` from the project source with that explicit
new `--manifest-sha256`. The generated backend embeds your new digest. The complete
installer source and packaging procedure are at:
https://github.com/jyh9521/Magna-Carta-2-CN (docs/INSTALLER.md).
Do not label your modified binary as the original published hash.

Project font, translation and upstream notices are retained alongside this file.
No game, emulator, original DLC, retail signature or third-party SDK is bundled.
