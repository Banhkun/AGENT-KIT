<#
.SYNOPSIS
    Syncs AGENT-KIT customizations to Global (~/.gemini/config) and Workspace (.agents) roots.

.DESCRIPTION
    AGENT-KIT provides a unified single source of truth for both:
    1. Global configurations: Rules, safety gate scripts, and hooks for ~/.gemini/config
    2. Workspace configurations: Skills and workflow rules for <workspace>/.agents

.PARAMETER Scope
    Target scope to sync: 'All' (default), 'Global', or 'Workspace'.

.PARAMETER WorkspaceRoot
    Path to the workspace root directory containing .agents. Defaults to 'C:\Users\Xabin\apps'.

.PARAMETER Mode
    'Copy' (default) copies files cleanly. 'Junction' creates directory junctions for live editing.

.EXAMPLE
    .\sync.ps1
    .\sync.ps1 -Scope Global
    .\sync.ps1 -Scope Workspace -WorkspaceRoot "C:\Users\Xabin\apps"
#>

[CmdletBinding()]
param (
    [ValidateSet('All', 'Global', 'Workspace')]
    [string]$Scope = 'All',

    [string]$WorkspaceRoot = "C:\Users\Xabin\apps",

    [ValidateSet('Copy', 'Junction')]
    [string]$Mode = 'Copy'
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Target directories
$GlobalRoot = Join-Path $env:USERPROFILE ".gemini\config"
$WorkspaceAgents = Join-Path $WorkspaceRoot ".agents"

function Sync-Directory($source, $destination) {
    if (-not (Test-Path $source)) {
        Write-Warning "Source directory not found: $source"
        return
    }

    if ($Mode -eq 'Junction') {
        if (Test-Path $destination) {
            $item = Get-Item $destination
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                Write-Host "  [Junction exists] $destination -> $($item.Target)"
                return
            }
            Remove-Item -Path $destination -Recurse -Force
        }
        New-Item -ItemType Junction -Path $destination -Target $source | Out-Null
        Write-Host "  [Linked Junction] $destination -> $source"
    } else {
        if (-not (Test-Path $destination)) {
            New-Item -ItemType Directory -Path $destination -Force | Out-Null
        }
        Copy-Item -Path "$source\*" -Destination $destination -Recurse -Force
        Write-Host "  [Copied] $source -> $destination"
    }
}

Write-Host "=== AGENT-KIT Customization Sync ===" -ForegroundColor Cyan
Write-Host "Source: $ScriptDir"
Write-Host "Scope:  $Scope | Mode: $Mode`n"

# 1. Sync Global Scope (~/.gemini/config)
if ($Scope -in @('All', 'Global')) {
    Write-Host "[1/2] Syncing Global Customizations -> $GlobalRoot" -ForegroundColor Yellow

    # Rules
    $srcGlobalRules = Join-Path $ScriptDir "global\rules"
    $dstGlobalRules = Join-Path $GlobalRoot "rules"
    Sync-Directory $srcGlobalRules $dstGlobalRules

    # Scripts
    $srcGlobalScripts = Join-Path $ScriptDir "global\scripts"
    $dstGlobalScripts = Join-Path $GlobalRoot "scripts"
    Sync-Directory $srcGlobalScripts $dstGlobalScripts

    # Hooks
    $srcHooks = Join-Path $ScriptDir "global\hooks.json"
    if (Test-Path $srcHooks) {
        Copy-Item -Path $srcHooks -Destination (Join-Path $GlobalRoot "hooks.json") -Force
        Write-Host "  [Copied] hooks.json -> $GlobalRoot\hooks.json"
    }

    Write-Host "  Global sync complete.`n" -ForegroundColor Green
}

# 2. Sync Workspace Scope (.agents)
if ($Scope -in @('All', 'Workspace')) {
    Write-Host "[2/2] Syncing Workspace Customizations -> $WorkspaceAgents" -ForegroundColor Yellow

    # Workspace Rules
    $srcRules = Join-Path $ScriptDir "rules"
    $dstRules = Join-Path $WorkspaceAgents "rules"
    Sync-Directory $srcRules $dstRules

    # Workspace Skills
    $srcSkills = Join-Path $ScriptDir "skills"
    $dstSkills = Join-Path $WorkspaceAgents "skills"
    Sync-Directory $srcSkills $dstSkills

    Write-Host "  Workspace sync complete.`n" -ForegroundColor Green
}

Write-Host "Sync successful!" -ForegroundColor Cyan
