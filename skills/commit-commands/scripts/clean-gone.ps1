[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "Fetching and pruning remote tracking branches..."
git fetch --prune

$lines = git branch -vv
$goneBranches = @()

foreach ($line in $lines) {
    if ($line -match '\[gone\]') {
        $cleaned = ($line -replace '^[*+\s]+', '').Trim()
        $branchName = ($cleaned -split '\s+')[0]
        if ($branchName) {
            $goneBranches += $branchName
        }
    }
}

if (-not $goneBranches -or $goneBranches.Count -eq 0) {
    Write-Host "No stale [gone] branches detected. Repository is clean!" -ForegroundColor Green
    return
}

Write-Host "Found $($goneBranches.Count) stale [gone] branch(es):" -ForegroundColor Yellow
$goneBranches | ForEach-Object { Write-Host " - $_" }

if ($DryRun) {
    Write-Host "`n[DryRun] No changes were made." -ForegroundColor Cyan
    return
}

$worktrees = git worktree list
$repoRoot = (git rev-parse --show-toplevel).Trim().Replace('/', '\')

foreach ($branch in $goneBranches) {
    Write-Host "`nProcessing branch: $branch"
    
    # Check for attached worktree
    $matchedWt = $null
    foreach ($wtLine in $worktrees) {
        if ($wtLine -match "\[$([regex]::Escape($branch))\]") {
            $wtPath = ($wtLine -split '\s+')[0]
            if ($wtPath -and ($wtPath.Replace('/', '\') -ne $repoRoot)) {
                $matchedWt = $wtPath
                break
            }
        }
    }

    if ($matchedWt) {
        Write-Host "  Removing associated worktree: $matchedWt" -ForegroundColor Yellow
        git worktree remove --force "$matchedWt"
    }

    Write-Host "  Deleting local branch: $branch" -ForegroundColor Yellow
    git branch -D "$branch"
}

Write-Host "`nCleanup complete!" -ForegroundColor Green
