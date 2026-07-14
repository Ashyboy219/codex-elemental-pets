$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$PetsDirectory = Join-Path $CodexHome "pets"

foreach ($Pet in @("frostbyte", "bolt")) {
    $Source = Join-Path $Root "pets/$Pet"
    $Destination = Join-Path $PetsDirectory $Pet
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Copy-Item (Join-Path $Source "pet.json") $Destination -Force
    Copy-Item (Join-Path $Source "spritesheet.webp") $Destination -Force
    Write-Host "Installed $Pet -> $Destination"
}

Write-Host "Open Codex Settings > Pets and choose Refresh, then select your pet."
