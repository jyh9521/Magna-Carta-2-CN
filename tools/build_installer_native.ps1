param(
    [Parameter(Mandatory)][string]$ZArchiveSource,
    [Parameter(Mandatory)][string]$ZstdSource,
    [string]$Output = 'build/installer-native'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$lock = Get-Content -LiteralPath "$root/references/installer-toolchain.lock.json" -Raw | ConvertFrom-Json
foreach ($item in @(@($ZArchiveSource, $lock.zarchive.commit), @($ZstdSource, $lock.zstd.commit))) {
    $actual = git -C $item[0] rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -ne $item[1]) { throw "Upstream revision mismatch: $($item[0])" }
    if (git -C $item[0] status --porcelain --untracked-files=no) { throw 'Upstream source has local edits' }
}
$finder = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vs = & $finder -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$cmake = "$vs/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$archivePath = (Resolve-Path -LiteralPath $ZArchiveSource).Path.Replace('\', '/')
$zstdPath = (Resolve-Path -LiteralPath $ZstdSource).Path.Replace('\', '/')
& $cmake -S "$root/src/installer/native" -B $Output -G 'Visual Studio 17 2022' -A x64 "-DZARCHIVE_SOURCE=$archivePath" "-DZSTD_SOURCE=$zstdPath"
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& $cmake --build $Output --config Release --parallel
exit $LASTEXITCODE
