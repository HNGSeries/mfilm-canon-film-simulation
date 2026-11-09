# Install the film-mode ML fork on the camera card.
#   powershell -File install_fork.ps1 -Card G:
# First run backs up the official ML (autoexec.bin + ML\MODULES) to
# ml-dev\card_backup\official\ so restore_official.ps1 can put it back.
# Every run also keeps the build it replaces in ml-dev\card_backup\previous\,
# unless the card already has this one (restore_official.ps1 -Previous puts
# that build back).
param([Parameter(Mandatory = $true)][string]$Card)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$fork = Join-Path $here "out\fork"
$backup = Join-Path $here "card_backup\official"
$prev = Join-Path $here "card_backup\previous"
$card = $Card.TrimEnd('\') + '\'

if (-not (Test-Path (Join-Path $card "autoexec.bin"))) { throw "No autoexec.bin on $card - is this the camera card?" }
if (-not (Test-Path (Join-Path $fork "autoexec.bin"))) { throw "Build the fork first (build_fork.sh)" }

# one-time backup of the official install
if (-not (Test-Path (Join-Path $backup "autoexec.bin"))) {
    New-Item -ItemType Directory -Force (Join-Path $backup "ML\MODULES") | Out-Null
    Copy-Item (Join-Path $card "autoexec.bin") $backup
    Copy-Item (Join-Path $card "ML\MODULES\*") (Join-Path $backup "ML\MODULES")
    Write-Output "Backed up official ML to $backup"
}

# what this install replaces, so the build on the card now can come back if
# the new one fails; not when the card already has this build (that would
# put the last good one out of reach)
$onCard = (Get-FileHash (Join-Path $card "autoexec.bin")).Hash
if ($onCard -ne (Get-FileHash (Join-Path $fork "autoexec.bin")).Hash) {
    $tmp = "$prev.new"
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Force (Join-Path $tmp "ML") | Out-Null
    Copy-Item (Join-Path $card "autoexec.bin") $tmp
    foreach ($d in "MODULES", "DATA", "SAMPLES") {
        $p = Join-Path $card "ML\$d"
        if (Test-Path $p) { Copy-Item $p (Join-Path $tmp "ML") -Recurse }
    }
    # only the colour tables: the prints in ML\DARKROOM stay on the card
    $looks = Join-Path $card "ML\DARKROOM\LOOK*.LUT"
    if (Test-Path $looks) {
        New-Item -ItemType Directory -Force (Join-Path $tmp "ML\DARKROOM") | Out-Null
        Copy-Item $looks (Join-Path $tmp "ML\DARKROOM")
    }
    # the copy is whole before the last one goes
    if (Test-Path $prev) { Remove-Item $prev -Recurse -Force }
    Rename-Item $tmp (Split-Path -Leaf $prev)
    Write-Output "Kept the build that was on the card in $prev"
}

# the fork's core and the modules/symbols built against it
Copy-Item (Join-Path $fork "autoexec.bin") $card -Force
Copy-Item (Join-Path $fork "ML\modules\*") (Join-Path $card "ML\MODULES") -Force
# the film OS is one of those modules (filmos.mo): its switch, so Magic Lantern loads it
$en = Join-Path $fork "ML\SETTINGS\filmos.en"
if (Test-Path $en) {
    New-Item -ItemType Directory -Force (Join-Path $card "ML\SETTINGS") | Out-Null
    Copy-Item $en (Join-Path $card "ML\SETTINGS") -Force
}
# the film OS fonts (not inside autoexec.bin, which has to stay small)
New-Item -ItemType Directory -Force (Join-Path $card "ML\DATA") | Out-Null
Copy-Item (Join-Path $fork "ML\data\FOSFONT.BIN") (Join-Path $card "ML\DATA") -Force
# the films beyond the built-in ones, and the donation codes if there are any
Copy-Item (Join-Path $fork "ML\data\FOSFILMS.BIN") (Join-Path $card "ML\DATA") -Force
$qr = Join-Path $fork "ML\data\FOSQR.BIN"
if (Test-Path $qr) { Copy-Item $qr (Join-Path $card "ML\DATA") -Force }
# the films' colour tables (the darkroom's prints stay as they are)
New-Item -ItemType Directory -Force (Join-Path $card "ML\DARKROOM") | Out-Null
Copy-Item (Join-Path $fork "ML\DARKROOM\LOOK*.LUT") (Join-Path $card "ML\DARKROOM") -Force
# the shelf's samples (EOS M builds only)
$samples = Join-Path $fork "ML\SAMPLES"
if (Test-Path $samples) {
    New-Item -ItemType Directory -Force (Join-Path $card "ML\SAMPLES") | Out-Null
    Copy-Item (Join-Path $samples "F*.BMP") (Join-Path $card "ML\SAMPLES") -Force
}

# filmroll is built in now; lua.mo was built for the official core
foreach ($m in "filmroll.mo", "lua.mo") {
    $p = Join-Path $card "ML\MODULES\$m"
    if (Test-Path $p) { Remove-Item $p; Write-Output "Removed ML\MODULES\$m" }
}

$a = (Get-FileHash (Join-Path $fork "autoexec.bin")).Hash
$b = (Get-FileHash (Join-Path $card "autoexec.bin")).Hash
Write-Output ("Installed fork autoexec.bin: " + $(if ($a -eq $b) { "verified" } else { "HASH MISMATCH" }))
