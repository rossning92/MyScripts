Add-Type -AssemblyName System.speech
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speech.SelectVoice("Microsoft Huihui Desktop");
$speech.Rate = 3
$speech.SetOutputToWaveFile($args[0])
$speech.Speak($args[1])
