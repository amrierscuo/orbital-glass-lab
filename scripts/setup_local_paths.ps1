param(
    [string]$ProjectRoot = 'D:\UnrealProjects\OrbitalGlassLab',
    [string]$DdcRoot = 'D:\UnrealCache\DDC',
    [string]$ZenRoot = 'D:\UnrealCache\Zen',
    [string]$AssetRoot = 'D:\UnrealAssets\OrbitalGlassLab',
    [string]$RenderRoot = 'D:\UnrealRenders\OrbitalGlassLab',
    [string]$VaultRoot = 'D:\EpicVaultCache'
)

$ErrorActionPreference = 'Stop'

$paths = @(
    $ProjectRoot,
    $DdcRoot,
    $ZenRoot,
    $AssetRoot,
    (Join-Path $AssetRoot '_Manifests'),
    (Join-Path $AssetRoot '_Licenses'),
    (Join-Path $AssetRoot 'FabDownloads'),
    (Join-Path $AssetRoot 'HDRI'),
    (Join-Path $AssetRoot 'NASA'),
    (Join-Path $AssetRoot 'SourceTextures'),
    (Join-Path $AssetRoot 'TestProjects'),
    $RenderRoot,
    (Join-Path $RenderRoot 'Previews'),
    (Join-Path $RenderRoot 'Frames'),
    (Join-Path $RenderRoot 'Final'),
    (Join-Path $RenderRoot 'Encoded'),
    (Join-Path $RenderRoot 'Captures'),
    $VaultRoot
)

foreach ($path in $paths) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}

$labRoot = Split-Path -Parent $PSScriptRoot
Copy-Item -LiteralPath (Join-Path $labRoot 'assets\asset_manifest.json') -Destination (Join-Path $AssetRoot '_Manifests\asset_manifest.json') -Force
Copy-Item -LiteralPath (Join-Path $labRoot 'docs\ASSET_MATRIX.md') -Destination (Join-Path $AssetRoot '_Manifests\ASSET_MATRIX.md') -Force
Copy-Item -LiteralPath (Join-Path $labRoot 'docs\INSTALL_CHECKLIST.md') -Destination (Join-Path $AssetRoot '_Manifests\INSTALL_CHECKLIST.md') -Force
Copy-Item -LiteralPath (Join-Path $labRoot 'docs\NVIDIA_SETUP.md') -Destination (Join-Path $AssetRoot '_Manifests\NVIDIA_SETUP.md') -Force
Copy-Item -LiteralPath (Join-Path $labRoot 'config\OrbitalGlassLab.vsconfig') -Destination (Join-Path $AssetRoot '_Manifests\OrbitalGlassLab.vsconfig') -Force
Copy-Item -LiteralPath (Join-Path $labRoot 'assets\NASA_CREDITS.txt') -Destination (Join-Path $AssetRoot 'NASA\CREDITS.txt') -Force

$projectFile = Join-Path $ProjectRoot 'OrbitalGlassLab.uproject'
$pluginsConfigured = $false
if (Test-Path -LiteralPath $projectFile) {
    $projectJson = Get-Content -Raw -LiteralPath $projectFile | ConvertFrom-Json
    if ($null -eq $projectJson.Plugins) {
        $projectJson | Add-Member -MemberType NoteProperty -Name Plugins -Value @()
    }

    $requiredPlugins = @(
        'PythonScriptPlugin',
        'EditorScriptingUtilities',
        'MovieRenderPipeline',
        'Water',
        'DaySequence',
        'CelestialVault',
        'SunPosition',
        'EnhancedInput',
        'ModelingToolsEditorMode',
        'GameplayStateTree'
    )

    foreach ($pluginName in $requiredPlugins) {
        $entry = $projectJson.Plugins | Where-Object { $_.Name -eq $pluginName } | Select-Object -First 1
        if ($null -eq $entry) {
            $projectJson.Plugins += [pscustomobject]@{
                Name = $pluginName
                Enabled = $true
            }
        }
        else {
            $entry.Enabled = $true
        }
    }

    $projectText = $projectJson | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($projectFile, $projectText, [System.Text.UTF8Encoding]::new($false))
    $pluginsConfigured = $true
}

[Environment]::SetEnvironmentVariable('UE-LocalDataCachePath', $DdcRoot, 'User')
[Environment]::SetEnvironmentVariable('UE-ZenDataPath', $ZenRoot, 'User')

[pscustomobject]@{
    ProjectRoot = $ProjectRoot
    DdcRoot = $DdcRoot
    ZenRoot = $ZenRoot
    AssetRoot = $AssetRoot
    RenderRoot = $RenderRoot
    VaultRoot = $VaultRoot
    PluginsConfigured = $pluginsConfigured
    Note = 'Riavviare Epic Games Launcher e Unreal Editor dopo questa configurazione.'
} | Format-List
