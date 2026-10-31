param(
  [Parameter(Mandatory = $true)][string]$TextFile,
  [Parameter(Mandatory = $true)][string]$OutputFile
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $pt = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
  if ($pt) {
    $synth.SelectVoice($pt.VoiceInfo.Name)
  } else {
    Write-Warning 'Não há voz pt-BR SAPI instalada. A voz padrão do Windows pode ter sotaque inadequado.'
  }
  $synth.Rate = 0
  $txt = [System.IO.File]::ReadAllText($TextFile, [System.Text.Encoding]::UTF8)
  $synth.SetOutputToWaveFile($OutputFile)
  $synth.Speak($txt)
  $synth.SetOutputToNull()
} finally {
  $synth.Dispose()
}
