$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$VideoRoot = Split-Path -Parent $PSScriptRoot
$VideoNarration = Get-Content -LiteralPath (Join-Path $VideoRoot 'narration.json') -Raw -Encoding utf8 | ConvertFrom-Json
$VoiceRoot = Join-Path $VideoRoot 'public/voice'
New-Item -ItemType Directory -Force -Path $VoiceRoot | Out-Null
$VideoTiming = @{ fps = 30; long = @(); short = @() }
foreach ($Cut in @('long','short')) {
    foreach ($Scene in $VideoNarration.$Cut) {
        $VoiceFile = Join-Path $VoiceRoot "$Cut-$($Scene.id).wav"
        $VoiceSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $VoiceSynth.SelectVoice('Microsoft Zira Desktop')
        $VoiceSynth.Rate = 0
        $VoiceSynth.SetOutputToWaveFile($VoiceFile)
        $VoiceSynth.Speak($Scene.text)
        $VoiceSynth.Dispose()
        $VoiceDuration = [double](& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $VoiceFile)
        $Padding = if ($Cut -eq 'long') { 0.5 } else { 0.24 }
        $Frames = [math]::Ceiling(($VoiceDuration + $Padding) * 30)
        $VideoTiming[$Cut] += @{ id = $Scene.id; frames = $Frames; voice = "voice/$Cut-$($Scene.id).wav"; caption = $Scene.caption; text = $Scene.text; speechSeconds = $VoiceDuration }
    }
}
$VideoTiming | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $VideoRoot 'src/timing.json') -Encoding utf8
foreach ($Cut in @('long','short')) {
    $Total = ($VideoTiming[$Cut] | ForEach-Object { $_.frames } | Measure-Object -Sum).Sum / 30
    Write-Output "$Cut duration: $Total seconds"
}
