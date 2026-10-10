# FH6 Japanese Signs - patcher (enable / disable / status). Plain PowerShell, no executables.
#
# Forza Horizon 6 keeps its world textures inside large GeoChunk*.minizip archives and ignores loose
# override files, so the mod swaps the bytes of specific archive slots - carefully:
#   * each texture is found by NAME (ChunkContentsMiniZip*.txt), never by a fixed offset;
#   * a slot is only touched if its bytes match, exactly (SHA-256), the vanilla slot the mod was built
#     for. If a game update changed anything, nothing is patched;
#   * the replacement has exactly the original slot length (the game refuses anything else);
#   * original bytes go to backup\ first; every write is read back and checked; any failure rolls the
#     whole run back;
#   * disable puts the backed-up bytes back, only where the mod's bytes are still in place.
# Steam's "Verify integrity of game files" also restores vanilla at any time.
#
# Usage: Enable mod.bat / Disable mod.bat / Status.bat
#        powershell -ExecutionPolicy Bypass -File FH6JapaneseSigns.ps1 enable|disable|status [-Game <folder>]
param(
    [ValidateSet("enable", "disable", "status", "")][string]$Command = "",
    [string]$Game = "",
    [switch]$NoPause
)
$ErrorActionPreference = "Stop"
$App = "FH6 Japanese Signs"
$ModDir = $PSScriptRoot
$TrackRel = "media\Tracks\Brio"

function Pause-End { if (-not $NoPause) { [void](Read-Host "`nPress Enter to close") } }

function Find-Game {
    $cands = @()
    if ($Game) { $cands += $Game }
    $d = $ModDir
    for ($k = 0; $k -lt 4 -and $d; $k++) { $cands += $d; $d = Split-Path $d -Parent }
    $cands += (Get-Location).Path
    foreach ($c in $cands) {
        if ($c -and (Test-Path (Join-Path $c "$TrackRel\GeoChunk0.minizip"))) { return (Resolve-Path $c).Path }
    }
    return $null
}

function Get-Sha([byte[]]$b) {
    $h = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash($b)) -replace "-", "").ToLower() } finally { $h.Dispose() }
}

function Read-Bytes([string]$path, [long]$off, [int]$len) {
    $fs = [IO.File]::Open($path, "Open", "Read", "ReadWrite")
    try {
        $buf = New-Object byte[] $len
        [void]$fs.Seek($off, "Begin")
        $n = 0
        while ($n -lt $len) { $r = $fs.Read($buf, $n, $len - $n); if ($r -le 0) { throw "short read" }; $n += $r }
        return ,$buf
    } finally { $fs.Dispose() }
}

function Write-Bytes([string]$path, [long]$off, [byte[]]$data) {
    $fs = [IO.File]::Open($path, "Open", "ReadWrite", "Read")
    try { [void]$fs.Seek($off, "Begin"); $fs.Write($data, 0, $data.Length); $fs.Flush($true) } finally { $fs.Dispose() }
}

# Archive slot offset of entry $idx (PGZP v101 table: blocks of <block_size> 12-byte entries, each
# block starting with an 8-byte aligned u64 base).
function Get-EntryOffset([string]$archive, [int]$idx) {
    $fs = [IO.File]::Open($archive, "Open", "Read", "ReadWrite")
    try {
        $br = New-Object IO.BinaryReader($fs)
        $magic = [Text.Encoding]::ASCII.GetString($br.ReadBytes(4))
        $ver = $br.ReadUInt32(); [void]$br.ReadUInt32(); $count = $br.ReadUInt32()
        $indexCount = $br.ReadUInt32(); $blockSize = $br.ReadUInt32()
        if ($magic -ne "PGZP" -or $ver -ne 101) { throw "unsupported archive format in $archive" }
        if ($idx -ge $count) { throw "entry index out of range" }
        $p = 0x20 + 4 * [long]$indexCount + 4
        $p += (8 - ($p % 8)) % 8
        $blockBytes = 8 + 12 * [long]$blockSize          # multiple of 8, so every block stays aligned
        $b = [math]::Floor($idx / $blockSize); $k = $idx % $blockSize
        [void]$fs.Seek($p + $b * $blockBytes, "Begin"); $base = $br.ReadUInt64()
        [void]$fs.Seek($p + $b * $blockBytes + 8 + 12 * $k, "Begin"); $off = $br.ReadUInt32()
        return [long]$base + $off
    } finally { $fs.Dispose() }
}

function Get-Lookup($track, $entries) {
    $want = @{}
    foreach ($e in $entries) { $want[$e.name] = $true }
    $found = @{}
    $chunks = @($entries | ForEach-Object { $_.chunk } | Sort-Object -Unique) + (0..63)
    foreach ($c in ($chunks | Select-Object -Unique)) {
        if ($found.Count -eq $want.Count) { break }
        $txt = Join-Path $track "ChunkContentsMiniZip$c.txt"
        if (-not (Test-Path $txt)) { continue }
        $i = 0
        foreach ($line in [IO.File]::ReadLines($txt)) {
            $line = $line.Trim()
            if (-not $line -or -not $line.Contains("|")) { continue }
            $name = $line.Substring(0, $line.LastIndexOf("|"))
            $name = $name.Substring([math]::Max($name.LastIndexOf("\"), $name.LastIndexOf("/")) + 1)
            if ($want.ContainsKey($name) -and -not $found.ContainsKey($name)) { $found[$name] = @($c, $i) }
            $i++
        }
    }
    return $found
}

function Survey($track, $manifest) {
    $lk = Get-Lookup $track $manifest.entries
    $out = @{}
    $n = 0
    foreach ($e in $manifest.entries) {
        $n++
        Write-Progress -Activity $App -Status "Checking textures" -PercentComplete (100 * $n / $manifest.entries.Count)
        if (-not $lk.ContainsKey($e.name)) { $out[$e.name] = @{ state = "missing" }; continue }
        $c, $i = $lk[$e.name]
        $archive = Join-Path $track "GeoChunk$c.minizip"
        $off = Get-EntryOffset $archive $i
        $raw = Read-Bytes $archive $off $e.slot_length
        $h = Get-Sha $raw
        $st = if ($h -eq $e.vanilla_slot_sha256) { "vanilla" } elseif ($h -eq $e.mod_slot_sha256) { "modded" } else { "changed" }
        $out[$e.name] = @{ state = $st; archive = $archive; offset = $off; raw = $raw }
    }
    Write-Progress -Activity $App -Completed
    return $out
}

function Count-States($sv) {
    $c = @{ vanilla = 0; modded = 0; changed = 0; missing = 0 }
    foreach ($v in $sv.Values) { $c[$v.state]++ }
    return $c
}

function Do-Enable($track, $manifest) {
    $sv = Survey $track $manifest
    $c = Count-States $sv
    Write-Host ("  vanilla {0}, already modded {1}, changed by a game update {2}, not found {3}" -f $c.vanilla, $c.modded, $c.changed, $c.missing)
    if ($c.changed -or $c.missing) {
        Write-Host "`n  The game files don't match the version this mod was built for (a game update changed"
        Write-Host "  some textures). Nothing was patched. Please check for an updated version of the mod."
        if ($manifest.game_version) { Write-Host "  (This version of the mod was built for game version $($manifest.game_version).)" }
        return $false
    }
    $bdir = Join-Path $ModDir "backup"
    New-Item -ItemType Directory -Force $bdir | Out-Null
    $done = New-Object System.Collections.ArrayList
    $todo = @($manifest.entries | Where-Object { $sv[$_.name].state -eq "vanilla" })
    try {
        $n = 0
        foreach ($e in $todo) {
            $n++
            Write-Progress -Activity $App -Status "Patching" -PercentComplete (100 * $n / [math]::Max(1, $todo.Count))
            $s = $sv[$e.name]
            $bpath = Join-Path $bdir ($e.name + ".bin")
            if (-not (Test-Path $bpath)) { [IO.File]::WriteAllBytes($bpath, $s.raw) }
            $new = [IO.File]::ReadAllBytes((Join-Path $ModDir "mod\files\$($e.file)"))
            if ($new.Length -ne $e.slot_length -or (Get-Sha $new) -ne $e.mod_slot_sha256) { throw "mod file damaged: $($e.file) (re-download the mod)" }
            Write-Bytes $s.archive $s.offset $new
            if ((Get-Sha (Read-Bytes $s.archive $s.offset $e.slot_length)) -ne $e.mod_slot_sha256) { throw "verification failed for $($e.name)" }
            [void]$done.Add($e)
        }
        Write-Progress -Activity $App -Completed
    } catch {
        Write-Host "`n  ERROR: $($_.Exception.Message)`n  Rolling back this run..."
        for ($k = $done.Count - 1; $k -ge 0; $k--) {
            $e = $done[$k]; $s = $sv[$e.name]
            Write-Bytes $s.archive $s.offset $s.raw
        }
        Write-Host "  Rolled back - the game files are unchanged."
        return $false
    }
    Write-Host "  Enabled: $($done.Count) textures patched."
    return $true
}

function Do-Disable($track, $manifest) {
    $sv = Survey $track $manifest
    $restored = 0; $nobackup = 0
    foreach ($e in $manifest.entries) {
        $s = $sv[$e.name]
        if ($s.state -ne "modded") { continue }
        $bpath = Join-Path $ModDir "backup\$($e.name).bin"
        if (-not (Test-Path $bpath)) { $nobackup++; continue }
        $orig = [IO.File]::ReadAllBytes($bpath)
        if ((Get-Sha $orig) -ne $e.vanilla_slot_sha256) { $nobackup++; continue }
        Write-Bytes $s.archive $s.offset $orig
        if ((Get-Sha (Read-Bytes $s.archive $s.offset $e.slot_length)) -ne $e.vanilla_slot_sha256) { throw "restore verification failed for $($e.name)" }
        $restored++
    }
    Write-Host "  Disabled: $restored textures restored to vanilla."
    if ($nobackup) { Write-Host "  $nobackup modded textures have no valid backup here - use Steam's 'Verify integrity of game files'." }
    return ($nobackup -eq 0)
}

function Do-Status($track, $manifest) {
    $sv = Survey $track $manifest
    $c = Count-States $sv
    $total = $manifest.entries.Count
    $state = if ($c.modded -eq $total) { "ENABLED" } elseif ($c.vanilla -eq $total) { "DISABLED (vanilla)" } `
             elseif ($c.changed -or $c.missing) { "GAME UPDATED - mod needs an update" } else { "PARTIAL" }
    Write-Host "  $App $($manifest.version): $state"
    Write-Host ("  vanilla {0}, modded {1}, changed {2}, missing {3}" -f $c.vanilla, $c.modded, $c.changed, $c.missing)
}

# ------------------------------------------------------------------ main
Write-Host "$App`n$('-' * $App.Length)"
$ok = $false
try {
    $g = Find-Game
    if (-not $g) {
        Write-Host "Could not find Forza Horizon 6. Put this folder inside the game folder (next to"
        Write-Host "forzahorizon6.exe) or run with -Game `"<game folder>`"."
    } elseif ($Command -ne "status" -and (Get-Process -Name "forzahorizon6" -ErrorAction SilentlyContinue)) {
        Write-Host "Please close Forza Horizon 6 first."
    } else {
        Write-Host "Game: $g"
        $track = Join-Path $g $TrackRel
        $manifest = Get-Content -Raw -Encoding UTF8 (Join-Path $ModDir "mod\manifest.json") | ConvertFrom-Json
        if (-not $Command) {
            Do-Status $track $manifest
            $ch = Read-Host "`n  [1] Enable mod   [2] Disable mod (vanilla)   [3] Exit`n  Choice"
            $Command = @{ "1" = "enable"; "2" = "disable" }[$ch.Trim()]
        }
        $t = Get-Date
        switch ($Command) {
            "enable" { $ok = Do-Enable $track $manifest }
            "disable" { $ok = Do-Disable $track $manifest }
            "status" { Do-Status $track $manifest; $ok = $true }
        }
        if ($Command -in @("enable", "disable")) { Write-Host ("  ({0:N0}s)" -f ((Get-Date) - $t).TotalSeconds) }
    }
} catch {
    Write-Host "`n  ERROR: $($_.Exception.Message)"
}
Pause-End
if ($ok) { exit 0 } else { exit 1 }
