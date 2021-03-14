Add-Type -AssemblyName System.speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice("Microsoft Huihui Desktop");
$synth.Rate = 3
$synth.Volume = 100;  
$synth.SetOutputToWaveFile($args[0])
$synth.Speak($args[1])
