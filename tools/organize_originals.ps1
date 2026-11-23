$ErrorActionPreference = 'Stop'
$workspacePath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspacePrefix = $workspacePath.TrimEnd('\') + '\'
$mapping = Get-Content -LiteralPath (Join-Path $workspacePath '.review\move-map.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$sourceFolders = @()
foreach ($entry in $mapping) {
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $workspacePath $entry.source))
    $targetPath = [System.IO.Path]::GetFullPath((Join-Path $workspacePath $entry.target))
    if (-not $sourcePath.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase) -or -not $targetPath.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside workspace.' }
    $sourceFolders += Split-Path -Parent $sourcePath
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        if ((Test-Path -LiteralPath $targetPath) -and ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash -eq $entry.sha256)) { continue }
        throw "Missing source: $sourcePath"
    }
    if (Test-Path -LiteralPath $targetPath) { throw "Target already exists: $targetPath" }
    if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Source changed: $sourcePath" }
    $targetFolder = Split-Path -Parent $targetPath
    [System.IO.Directory]::CreateDirectory($targetFolder) | Out-Null
    Move-Item -LiteralPath $sourcePath -Destination $targetPath
    if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Verification failed: $targetPath" }
}
foreach ($sourceFolder in ($sourceFolders | Select-Object -Unique)) {
    if (-not $sourceFolder.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid directory.' }
    if ((Test-Path -LiteralPath $sourceFolder) -and @(Get-ChildItem -LiteralPath $sourceFolder -Force).Count -eq 0) { Remove-Item -LiteralPath $sourceFolder -Force }
}
Copy-Item -LiteralPath (Join-Path $workspacePath '.review\move-map.json') -Destination (Join-Path $workspacePath 'assets\source-map.json')
foreach ($fileName in @('design.css','effects.js','logo.svg','preview-desktop.png','preview-mobile.png')) {
    $oldPath = Join-Path $workspacePath $fileName
    $backupPath = Join-Path $workspacePath ('.review\original-' + $fileName)
    if ((Test-Path -LiteralPath $oldPath) -and -not (Test-Path -LiteralPath $backupPath)) { Move-Item -LiteralPath $oldPath -Destination $backupPath }
}
Write-Output "Organized and hash-verified $($mapping.Count) original media files."
