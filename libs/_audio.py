from _shutil import *
from _appmanager import *

get_executable("sox")


def create_noise_profile(in_file):
    os.makedirs("tmp", exist_ok=True)
    call2(["sox", in_file, "-n", "noiseprof", "tmp/noise.prof"])


def denoise(in_file, out_file=None):
    os.makedirs("tmp", exist_ok=True)
    if os.path.exists("tmp/noise.prof"):
        if out_file is None:
            tmp_file = in_file + ".denoise.wav"
        else:
            tmp_file = out_file

        print("De-noising %s..." % in_file)
        call2(["sox", in_file, tmp_file, "noisered", "tmp/noise.prof", "0.21"])

        if out_file is None:
            shutil.copyfile(tmp_file, in_file)
            os.remove(tmp_file)

    else:
        print("WARNING: Skip noise reduction, profile does not exist.")


def concat_audio(audio_files, silence_secs, out_file, channels=2):
    if silence_secs > 0:
        mkdir("tmp")
        call2(f"sox -n -r 44100 -c {channels} tmp/silence.wav trim 0.0 {silence_secs}")
        audio_files = " tmp/silence.wav ".join(audio_files)
    else:
        audio_files = " ".join(audio_files)

    print2("Output %s" % out_file)
    call2(f"sox {audio_files} {out_file}")
