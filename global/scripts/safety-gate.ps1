[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Read from pipeline $input first, fallback to Console.In
$rawInput = ($input | Out-String)
if ([string]::IsNullOrWhiteSpace($rawInput)) {
    $rawInput = [Console]::In.ReadToEnd()
}

# Default decision: allow
$response = @{
    decision = "allow"
    reason   = "Command passed safety gate check."
}

if (-not [string]::IsNullOrWhiteSpace($rawInput)) {
    try {
        $data = $rawInput | ConvertFrom-Json
        $cmd = ""
        if ($data.toolCall -and $data.toolCall.args -and $data.toolCall.args.CommandLine) {
            $cmd = $data.toolCall.args.CommandLine
        }

        if ($cmd) {
            # 1. Hard Block (Deny): High-risk system, disk, or credential destruction
            $hardBlockPatterns = @(
                '(?i)\bformat\b\s+[a-zA-Z]:',
                '(?i)\bdiskpart\b',
                '(?i)\bbcdedit\b',
                '(?i)\breg\s+delete\b',
                '(?i)\bvssadmin\b',
                '(?i)rmdir\s+.*\/s.*[a-zA-Z]:\\',
                '(?i)del\s+.*\/[fs].*[a-zA-Z]:\\',
                '(?i)rm\s+-(r|rf|fr)\s+([\/~]|[a-zA-Z]:\\)',
                '(?i)Remove-Item\s+.*-Recurse.*(\$env:USERPROFILE|\$HOME|[a-zA-Z]:\\)',
                '(?i)(\.ssh[\\\/]|\.aws[\\\/]|Windows[\\\/]System32)'
            )

            foreach ($pattern in $hardBlockPatterns) {
                if ($cmd -match $pattern) {
                    $response = @{
                        decision = "deny"
                        reason   = "Safety Gate: Command blocked by safety policy (potential destructive system, disk, or credential modification)."
                    }
                    Write-Output ($response | ConvertTo-Json -Compress)
                    exit 0
                }
            }

            # 2. Gate (Force Ask): High-impact git actions requiring explicit user confirmation
            $forceAskPatterns = @(
                '(?i)git\s+push\s+.*(--force\b|-f\b)',
                '(?i)git\s+reset\s+--hard\b',
                '(?i)git\s+clean\s+-[a-zA-Z]*f\b',
                '(?i)git\s+branch\s+-[dD]\b'
            )

            foreach ($pattern in $forceAskPatterns) {
                if ($cmd -match $pattern) {
                    $response = @{
                        decision = "force_ask"
                        reason   = "Safety Gate: Command requires explicit confirmation (force-push, hard reset, or mass untracked file deletion)."
                    }
                    Write-Output ($response | ConvertTo-Json -Compress)
                    exit 0
                }
            }
        }
    } catch {
        # Fall back to allow on unexpected JSON format
        $response = @{
            decision = "allow"
            reason   = "Default allow on payload parsing fallback: $($_.Exception.Message)"
        }
    }
}

Write-Output ($response | ConvertTo-Json -Compress)
