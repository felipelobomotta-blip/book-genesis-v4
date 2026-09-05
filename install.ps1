# Install the Book Genesis runtime from this checkout on Windows PowerShell.
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

if (-not $PSScriptRoot) {
    Write-Error "This script must be run from a saved file."
    exit 1
}

$RepoDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
Set-Location -LiteralPath $RepoDir

if (-not (Test-Path -LiteralPath (Join-Path $RepoDir "pyproject.toml") -PathType Leaf)) {
    Write-Error "pyproject.toml was not found beside this script."
    exit 1
}

$VersionCheck = 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
$VersionPrint = 'import sys; print(".".join(map(str, sys.version_info[:3])))'
$Candidates = @()

# An activated virtual environment is an explicit author choice. Resolve it directly
# before consulting PATH or the Windows Python launcher, which may select a global
# interpreter instead.
if ($env:VIRTUAL_ENV) {
    $ActivePython = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if (Test-Path -LiteralPath $ActivePython -PathType Leaf) {
        $Candidates += @{ Name = $ActivePython; Args = @(); Direct = $true }
    }
}

# `python` and `python3` may themselves resolve to the activated environment because
# activation prepends it to PATH. Keep `py -3` last as a global fallback.
$Candidates += @(
    @{ Name = "python"; Args = @(); Direct = $false },
    @{ Name = "python3"; Args = @(); Direct = $false },
    @{ Name = "py"; Args = @("-3"); Direct = $false }
)

$PythonCommand = $null
$PythonArgs = @()
foreach ($Candidate in $Candidates) {
    if ($Candidate.Direct) {
        $CommandPath = $Candidate.Name
    } else {
        $Command = Get-Command -Name $Candidate.Name -CommandType Application -ErrorAction SilentlyContinue
        if ($null -eq $Command) {
            continue
        }
        $CommandPath = $Command.Source
    }

    & $CommandPath @($Candidate.Args) -c $VersionCheck 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonCommand = $CommandPath
        $PythonArgs = @($Candidate.Args)
        break
    }
}

if ($null -eq $PythonCommand) {
    Write-Error "Book Genesis requires Python 3.10 or newer (tried an active virtual environment, python, python3, and py -3)."
    exit 1
}

$PythonVersion = & $PythonCommand @($PythonArgs) -c $VersionPrint
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Installing Book Genesis with $PythonCommand ($PythonVersion)..."
& $PythonCommand @($PythonArgs) -m pip install .
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Book Genesis is installed. Next:"
Write-Host "  book-genesis setup"
Write-Host '  book-genesis new --idea "Your idea" --language en --path books/my-book'
Write-Host ""
Write-Host "The installer did not connect a provider or run a model."
