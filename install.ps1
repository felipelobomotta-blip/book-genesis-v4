[CmdletBinding()]
param(
    [ValidateSet("claude", "codex", "kimi", "shared")]
    [string]$Target = "claude",
    [string]$Destination = "",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$IncludeLegacy
)

$ErrorActionPreference = "Stop"
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cliPath = Join-Path $repoDir "runner\cli.py"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$launcherArgs = @()
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $launcherArgs = @("-3")
}
if (-not $pythonCommand) {
    throw "Python 3 was not found in PATH."
}

$cliArgs = @($cliPath, "install", $Target)
if ($Destination) {
    $cliArgs += @("--dest", $Destination)
}
if ($Force) {
    $cliArgs += "--force"
}
if ($DryRun) {
    $cliArgs += "--dry-run"
}
if ($IncludeLegacy) {
    $cliArgs += "--include-legacy"
}

& $pythonCommand.Source @launcherArgs @cliArgs
exit $LASTEXITCODE
