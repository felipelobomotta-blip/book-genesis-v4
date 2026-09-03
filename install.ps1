# Book Genesis installer for Windows PowerShell.
# Installs full skill folders, including supporting references, to ~/.claude/.

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoDir) { $RepoDir = Get-Location }

$SkillsDir = Join-Path $RepoDir "skills"
$KnowledgeDir = Join-Path $RepoDir "knowledge"
$AgentsDir = Join-Path $RepoDir "agents"
$TargetSkills = Join-Path $env:USERPROFILE ".claude\skills"
$TargetKnowledge = Join-Path $env:USERPROFILE ".claude\knowledge"
$TargetAgents = Join-Path $env:USERPROFILE ".claude\agents"

Write-Host ""
Write-Host "Book Genesis" -ForegroundColor Blue
Write-Host "Copies the agent templates and knowledge base to ~/.claude (optional: the runner reads them from this clone)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Installing skills, supporting references, agents, and knowledge base" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $SkillsDir)) {
    Write-Host "Error: skills\ directory not found. Run this script from the repository root." -ForegroundColor Red
    exit 1
}

foreach ($dir in @($TargetSkills, $TargetKnowledge, $TargetAgents)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Skills live at skills\<name>\ AND in grouping folders like skills\optional\<name>\.
# Discover SKILL.md at any depth so nested groups are not silently skipped.
# skills\deprecated\ is intentionally excluded - those are superseded by agents\.
$count = 0
Get-ChildItem -Path $SkillsDir -Filter "SKILL.md" -File -Recurse | ForEach-Object {
    $skillDir = $_.Directory
    if ($skillDir.FullName -match '[\\/]deprecated[\\/]') { return }
    $skillName = $skillDir.Name
    $destDir = Join-Path $TargetSkills $skillName
    if (Test-Path $destDir) {
        Remove-Item -LiteralPath $destDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    Copy-Item -Path (Join-Path $skillDir.FullName "*") -Destination $destDir -Recurse -Force
    Write-Host "  + $skillName" -ForegroundColor Green
    $count++
}

$kbCount = 0
if (Test-Path $KnowledgeDir) {
    Get-ChildItem -Path $KnowledgeDir -Filter "*.md" | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $TargetKnowledge $_.Name) -Force
        Write-Host "  + knowledge/$($_.Name)" -ForegroundColor Green
        $kbCount++
    }
}

$agentCount = 0
if (Test-Path $AgentsDir) {
    Get-ChildItem -Path $AgentsDir -Filter "*.md" | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $TargetAgents $_.Name) -Force
        Write-Host "  + agent/$($_.Name)" -ForegroundColor Green
        $agentCount++
    }
}

# Verify every template the runner reads is present (runner/chapter.py, runner/phases.py).
# A missing one fails the runner closed, so fail loudly here instead.
$PipelineAgents = @(
    "book-researcher", "book-architect", "entity-tracker", "continuity-guardian",
    "book-writer", "book-disruptor", "book-judge",
    "book-evaluator", "book-editor", "book-packager"
)
$missing = $PipelineAgents | Where-Object { -not (Test-Path (Join-Path $TargetAgents "$_.md")) }

Write-Host ""
if ($missing) {
    Write-Host "Pipeline incomplete. Templates the runner needs are not installed:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "The runner fails closed when it reaches one of these."
    exit 1
}
Write-Host "Pipeline verified. All 10 runner templates resolve." -ForegroundColor Green

Write-Host ""
Write-Host "Done. $count skills + $agentCount agents + $kbCount knowledge files installed" -ForegroundColor Green
Write-Host ""
Write-Host "Skills:    $TargetSkills" -ForegroundColor Blue
Write-Host "Agents:    $TargetAgents" -ForegroundColor Blue
Write-Host "Knowledge: $TargetKnowledge" -ForegroundColor Blue
Write-Host ""
Write-Host "Start a book from this folder:  python runner\cli.py init my-book --idea ""..."" --language en"
Write-Host "Then:  run-phase (x3), book, approve, book.  Details: docs\runner.md"
Write-Host ""
