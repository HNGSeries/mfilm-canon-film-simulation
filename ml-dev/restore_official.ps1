# Put the official ML (backed up by install_fork.ps1) back on the card.
#   powershell -File restore_official.ps1 -Card G:
# Or the build that was on the card before the last install_fork.ps1:
#   powershell -File restore_official.ps1 -Card G: -Previous
param([Parameter(Mandatory = $true)][string]$Card, [switch]$Previous)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$card = $Card.TrimEnd('\') + '\'

if ($Previous) {
    $prev = Join-Path $here "card_backup\previous"
    if (-not (Test-Path (Join-Path $prev "autoexec.bin"))) { throw "No backup in $prev" }
    Copy-Item (Join-Path $prev "autoexec.bin") $card -Force
    foreach ($d in "MODULES", "DATA", "SAMPLES", "DARKROOM") {
        $p = Join-Path $prev "ML\$d"
        if (Test-Path $p) {
            New-Item -ItemType Directory -Force (Join-Path $card "ML\$d") | Out-Null
            Copy-Item (Join-Path $p "*") (Join-Path $card "ML\$d") -Force
        }
    }
    Write-Output "The previous build is back on $card"
    return
}

$backup = Join-Path $here "card_backup\official"
if (-not (Test-Path (Join-Path $backup "autoexec.bin"))) { throw "No backup in $backup" }

Copy-Item (Join-Path $backup "autoexec.bin") $card -Force
Copy-Item (Join-Path $backup "ML\MODULES\*") (Join-Path $card "ML\MODULES") -Force
Write-Output "Official ML restored on $card (the filmroll module from ml-dev\out can be copied back if wanted)"
